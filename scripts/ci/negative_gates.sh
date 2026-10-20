#!/usr/bin/env bash
# Proves the coverage gate and gitleaks fail closed. These cases are not separate
# workflow jobs, because a job that is expected to fail would stay red on the PR.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

workflow="${root}/.github/workflows/gitleaks.yml"
for sha in \
  551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb \
  e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080
do
  if ! grep -q "$sha" "$workflow"; then
    echo "::error::gitleaks checksum ${sha} is missing from the reusable workflow"
    exit 1
  fi
  if ! grep -q "$sha" "$0"; then
    echo "::error::gitleaks checksum ${sha} is missing from negative_gates.sh"
    exit 1
  fi
done

if ! grep -q 'cov-fail-under' "${root}/.github/workflows/python-ci.yml"; then
  echo "::error::Python CI does not pass --cov-fail-under"
  exit 1
fi

install_gitleaks() {
  local version="8.30.1"
  local asset sha
  case "$(uname -m)" in
    x86_64)
      asset="gitleaks_${version}_linux_x64.tar.gz"
      sha="551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"
      ;;
    aarch64)
      asset="gitleaks_${version}_linux_arm64.tar.gz"
      sha="e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080"
      ;;
    *)
      echo "::error::Unsupported architecture $(uname -m)"
      exit 1
      ;;
  esac
  local workdir
  workdir="$(mktemp -d)"
  curl -fsSL --retry 3 --retry-delay 2 \
    "https://github.com/gitleaks/gitleaks/releases/download/v${version}/${asset}" \
    -o "${workdir}/gitleaks.tar.gz"
  echo "${sha}  ${workdir}/gitleaks.tar.gz" | sha256sum -c -
  tar -xzf "${workdir}/gitleaks.tar.gz" -C "$workdir" gitleaks
  install -m 0755 "${workdir}/gitleaks" "${1}/gitleaks"
  rm -rf "$workdir"
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "${tmp}/bin"
install_gitleaks "${tmp}/bin"

# A Slack-shaped token is assembled at runtime so the fixture is not stored in git.
# The AWS documentation key is allowlisted by gitleaks and does not prove the gate.
prefix="$(printf '%s%s' 'xox' 'b')"
body="$(printf '%s-%s-%s' '123456789012' '123456789012' 'abcdefghijklmnopqrstuvwx')"
fixture_key="${prefix}-${body}"

leaky="${tmp}/leaky"
mkdir -p "$leaky"
git -C "$leaky" init -q
git -C "$leaky" config user.email "ci-fixture@example.com"
git -C "$leaky" config user.name "CI Fixture"
printf 'slack_token=%s\n' "$fixture_key" > "${leaky}/credentials.txt"
git -C "$leaky" add credentials.txt
git -C "$leaky" commit -q -m "add fixture credential"
set +e
leak_log="${tmp}/gitleaks-leak.txt"
"${tmp}/bin/gitleaks" detect --source "$leaky" --redact --no-banner --exit-code 1 >"$leak_log" 2>&1
leak_code=$?
set -e
if [ "$leak_code" -eq 0 ]; then
  echo "::error::gitleaks did not fail on a fixture credential"
  exit 1
fi
if grep -q "$fixture_key" "$leak_log"; then
  echo "::error::gitleaks output was not redacted"
  exit 1
fi
echo "gitleaks fail-closed check passed (exit ${leak_code}, secret redacted)"

clean="${tmp}/clean"
mkdir -p "$clean"
git -C "$clean" init -q
git -C "$clean" config user.email "ci-fixture@example.com"
git -C "$clean" config user.name "CI Fixture"
printf 'print("hello")\n' > "${clean}/app.py"
git -C "$clean" add app.py
git -C "$clean" commit -q -m "add app"
"${tmp}/bin/gitleaks" detect --source "$clean" --redact --no-banner --exit-code 1
echo "gitleaks clean-repo check passed"

py="${tmp}/py"
python3 -m pip install --disable-pip-version-check --target "$py" \
  "${root}/fixtures/python-app[dev]" \
  "${root}/fixtures/python-low-cov[dev]"
export PYTHONPATH="${py}${PYTHONPATH:+:$PYTHONPATH}"

(
  cd "${root}/fixtures/python-app"
  python3 -m ruff check .
  python3 -m mypy
  python3 -m pytest --cov=sample_widget --cov-fail-under=80 --cov-report=term-missing
)

set +e
(
  cd "${root}/fixtures/python-low-cov"
  python3 -m pytest --cov=sample_lowcov --cov-fail-under=100 --cov-report=term-missing
)
low_code=$?
set -e
if [ "$low_code" -eq 0 ]; then
  echo "::error::coverage threshold did not fail a partially covered package"
  exit 1
fi
echo "coverage fail-under check passed (exit ${low_code})"

(
  cd "${root}/fixtures/python-low-cov"
  python3 -m ruff check .
  python3 -m mypy
  python3 -m pytest
)

lint_copy="${tmp}/lint-src"
mkdir -p "${lint_copy}/src" "${lint_copy}/scripts"
printf 'export const value = 1;\ndebugger;\n' > "${lint_copy}/src/bad.ts"
cp "${root}/fixtures/node-npm/scripts/lint.mjs" "${lint_copy}/scripts/lint.mjs"
set +e
(cd "$lint_copy" && node scripts/lint.mjs >"${tmp}/lint.txt" 2>&1)
lint_code=$?
set -e
if [ "$lint_code" -eq 0 ]; then
  echo "::error::node lint fixture did not reject a debugger statement"
  exit 1
fi
echo "node lint fail-closed check passed (exit ${lint_code})"

echo "negative gates passed"
