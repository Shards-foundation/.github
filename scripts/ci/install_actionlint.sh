#!/usr/bin/env bash
# Install a pinned actionlint binary and put it on PATH for later steps.
set -euo pipefail

version="1.7.12"
case "$(uname -m)" in
  x86_64)
    asset="actionlint_${version}_linux_amd64.tar.gz"
    sha="8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"
    ;;
  aarch64)
    asset="actionlint_${version}_linux_arm64.tar.gz"
    sha="325e971b6ba9bfa504672e29be93c24981eeb1c07576d730e9f7c8805afff0c6"
    ;;
  *)
    echo "::error::Unsupported architecture $(uname -m)"
    exit 1
    ;;
esac

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
url="https://github.com/rhysd/actionlint/releases/download/v${version}/${asset}"
curl -fsSL --retry 3 --retry-delay 2 "$url" -o "${workdir}/actionlint.tar.gz"
echo "${sha}  ${workdir}/actionlint.tar.gz" | sha256sum -c -
tar -xzf "${workdir}/actionlint.tar.gz" -C "$workdir" actionlint
install_dir="${HOME}/.local/bin"
mkdir -p "$install_dir"
install -m 0755 "${workdir}/actionlint" "${install_dir}/actionlint"
if [ -n "${GITHUB_PATH:-}" ]; then
  echo "$install_dir" >> "$GITHUB_PATH"
fi
export PATH="${install_dir}:${PATH}"
actionlint -version
