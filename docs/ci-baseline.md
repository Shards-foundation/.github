# CI and security baseline

This repository is the Shards-foundation org `.github` repository. Reusable workflows live in `.github/workflows/` here. A workflow in another repository calls them as:

`Shards-foundation/.github/.github/workflows/<file>.yml@main`

`@main` is deliberate. Third-party actions inside the reusable workflows are pinned to a full commit SHA with a version comment, so Dependabot can bump the SHA and the comment together. Callers stay on `@main` and pick up those bumps after this repository's default branch moves. That only stays safe if the default branch of **this** repository is protected. The owner turns that protection on by hand. This change does not modify org or repository settings.

Every check in these workflows is a real gate. A failing test, linter, type check, build, secret scan, or vulnerable dependency fails the job. The workflows do not set `continue-on-error`, do not append `|| true` to a test command, and do not use `pull_request_target`.

## Hardening on every workflow

- `permissions` is set to the smallest set that job needs. Callers must grant at least that set on the calling job, because a called workflow cannot raise the caller's token.
- Third-party `uses:` values are 40-character SHAs. The comment on the same line is the release tag, for example `# v7.0.1`.
- `concurrency` cancels superseded runs, except Release Please, which does not cancel an in-progress release.
- Every job that runs on a runner has `timeout-minutes`. A caller job that only `uses` a reusable workflow cannot set `timeout-minutes` (GitHub rejects that key). The limit lives in the reusable workflow.
- Tokens are passed as secrets or as `github.token`. Scripts do not print them. gitleaks is invoked with `--redact`.
- Runners are `ubuntu-24.04`.
- User-supplied shell snippets (`install-command`, `lint-command`, and the other command inputs) are passed through environment variables and executed with `bash -euo pipefail`. They are not interpolated into the workflow script.

`scripts/ci/check_workflows.py` fails the self-test if a workflow or template breaks these rules.

## Workflows

| Workflow | What it does | Stable check name |
| --- | --- | --- |
| `python-ci.yml` | Install, lint, type-check when configured, pytest on a version matrix | `Python CI` |
| `node-ci.yml` | pnpm or npm install, then lint, type-check, build, and test | `Node CI` |
| `gitleaks.yml` | Scan full git history for secrets | `Gitleaks` |
| `dependency-review.yml` | Fail a pull request that adds a known-vulnerable dependency | `Dependency review` |
| `codeql.yml` | CodeQL for detected or requested languages | `CodeQL` |
| `scorecard.yml` | OpenSSF Scorecard SARIF report | `OpenSSF Scorecard` |
| `release-please.yml` | Release pull requests and changelogs, only when a repo calls it | `Release Please` |

Matrix workflows add a final job with that stable name. Require **that** name in a ruleset, not `python (3.12)` or `javascript-typescript`. Those legs change when the matrix changes. GitHub shows reusable jobs as `<caller job name> / <called job name>`. The templates set both to the same words, so the check to require is `Python CI / Python CI` (and the same shape for the others). Copy the name from the first green run if the UI differs.

### Python CI

Runs on each version in `python-versions`.

1. Install. A custom `install-command` replaces detection. Otherwise the workflow installs an editable project from `pyproject.toml` (the `dev` extra when `[project.optional-dependencies]` defines `dev`), then `requirements.txt` if that file is also present. `setup.py` and `requirements-dev.txt` are supported. A Poetry-only project fails with an error telling you to set `install-command`.
2. Lint. A custom `lint-command` replaces detection. Otherwise Ruff runs when `ruff.toml`, `.ruff.toml`, or `[tool.ruff` is present, and Flake8 runs when its config is present. If neither is configured, the step records a notice and does not pretend a linter ran.
3. Type check. A custom `typecheck-command` replaces detection. Otherwise mypy runs when `mypy.ini`, `.mypy.ini`, `[tool.mypy`, or `[mypy]` is present. With no config, the step records a notice.
4. Test. The default is pytest. `require-tests` defaults to `false`: pytest exit code 5 (nothing collected) is a notice, not a failure. Any other non-zero exit fails the job. Set `require-tests: true` when an empty suite should fail.
5. `extra-checks` runs on **every** matrix leg after tests, with `bash -euo pipefail`. Use it for smoke scripts and package builds. An empty value skips the step.

`python-versions` is a string that contains a JSON array, because a reusable-workflow input cannot be a real array. At most eight versions. Each entry must look like `3.12`, `3.11.9`, `3.x`, or `pypy3.10`.

`coverage-threshold` is a number from 0 to 100. **The default is 0, which turns the gate off** and does not collect coverage. Any value above 0 installs `pytest-cov` when needed and passes `--cov-fail-under`. That fails the job when total coverage is under the threshold. It does not lower the bar to make a red suite green.

Coverage is collected when the threshold is above 0 or when `coverage-packages` is set. Reports are written in the working directory as `coverage.xml` and `coverage.json`. `coverage-packages` is a comma-separated list of import names (`kernels,implementations` becomes `--cov=kernels --cov=implementations`). With a threshold and no packages, the workflow passes `--cov=.`. `coverage-branch: true` adds `--cov-branch`. `pytest-args` is appended to the default pytest command and is ignored when `test-command` replaces pytest. A custom `test-command` is responsible for its own coverage flags.

### Node.js / TypeScript CI

`node-versions` is a JSON array string such as `["20","22"]`. Versions may be `20`, `20.18.1`, or `lts/jod`. At most eight.

`package-manager` is `auto` (default), `npm`, or `pnpm`. `auto` reads `packageManager`, then `pnpm-lock.yaml`, then `package-lock.json`. `yarn.lock` fails the job instead of being forced through npm. When pnpm is selected, `pnpm-version` overrides the version; otherwise the `packageManager` field is used, or `10.4.1` if the field is missing.

Install uses `pnpm install --frozen-lockfile` or `npm ci` when the matching lockfile exists. A missing lockfile still installs, and the log says the install is not reproducible. A lockfile that does not match the manifest fails the job.

Then, in order:

- **Lint** runs `lint-command`, or the `lint` script. If neither exists, it records a notice.
- **Type check** runs `typecheck-command`, or the `typecheck` / `type-check` script, or `tsc --noEmit` when `tsconfig.json` exists and `typescript` is a dependency. The binary is the project's (`pnpm exec` or `npx --no-install`), not a freshly downloaded compiler.
- **Build** runs `build-command` or the `build` script. A missing script is a notice.
- **Test** runs `test-command` or the `test` script. The npm placeholder `"Error: no test specified"` counts as no tests. `require-tests` defaults to `false`. A script that exists and fails always fails the job.
- **extra-checks** behaves as in Python CI.

### Gitleaks

Checks out the full history and runs gitleaks `8.30.1`. The tarball checksum is pinned in the workflow for `linux_x64` and `linux_arm64`. `--redact` is on, so a finding's secret is not printed. Exit code 1 fails the job. A repository `.gitleaks.toml` is picked up by gitleaks itself. Use that only for false positives. Do not allowlist a real credential.

`config-path` points at a different config file when the default is wrong.

### Dependency review

On `pull_request`, `actions/dependency-review-action` compares the dependency graph of the base and head. A new dependency with a known vulnerability at low severity or above fails the job. `fail-on-scopes` is `runtime`, `development`, and `unknown`, so a vulnerable dev dependency fails too. `warn-only` is not set. The summary is not posted as a pull-request comment, so the job only needs `contents: read`.

Outside a pull request the review job is skipped. The stable check still succeeds and records a notice, which is what makes the check usable as a required check on a branch that also receives pushes. The gate itself runs on pull requests.

`fail-on-severity` may be `low`, `moderate`, `high`, or `critical`. Leave it empty to keep the action default (`low`).

The action needs the dependency graph. Enabling that is an owner setting, described below.

### CodeQL

`languages` is a JSON array of CodeQL language ids (`python`, `javascript-typescript`, `java-kotlin`, `go`, `ruby`, `csharp`, `c-cpp`, `actions`, and the other ids CodeQL accepts). An empty string auto-detects committed Python and JavaScript/TypeScript files only. Pass `languages` for anything else. No detected language records a notice and the stable check succeeds.

Interpreted languages use `build-mode: none`. Other languages use `autobuild`. `queries` is omitted unless you set it, so the default query suite is not replaced by an empty list. `security-extended` is an example value.

The SARIF file is parsed in the job. Any result fails the build, whether or not GitHub code scanning is enabled. When code scanning is enabled, the action uploads the SARIF. When it is not, the job records a notice, still fails on findings, and uploads the SARIF as a workflow artifact. The database is not uploaded.

This is an advanced CodeQL setup. Do not also turn on the repository's default CodeQL setup.

### OpenSSF Scorecard

The Scorecard action writes `results.sarif`. A missing or empty file fails the job. The file is always kept as an artifact and is uploaded to code scanning when that feature is enabled.

A low score does **not** fail CI. Branch protection, token permissions, and several other Scorecard checks only become green after the owner changes org settings. Failing the workflow until those exist would deadlock a required check. The score is still produced on every run. `publish_results` is true only for a push or schedule on the default branch of a public repository, which is what the Scorecard API accepts.

Private repositories often need a PAT because the default token cannot read what Scorecard asks for. Pass it as a secret, not an input:

```yaml
jobs:
  scorecard:
    name: OpenSSF Scorecard
    permissions:
      actions: read
      contents: read
      id-token: write
      security-events: write
    uses: Shards-foundation/.github/.github/workflows/scorecard.yml@main
    secrets:
      repo-token: ${{ secrets.SCORECARD_TOKEN }}
```

Do not echo that token. This repository does not contain one.

The pinned Scorecard action runs the upstream image `ghcr.io/ossf/scorecard-action:v2.5.0`. The `uses:` line is a commit SHA. The image tag is what that pinned action declares. We do not retag or rebuild it.

### Release Please

`release-please.yml` has **no** `push` or `pull_request` trigger. Nothing in a repository releases until that repository adds a caller. The template `workflow-templates/release-please.yml` is that opt-in. It runs on pushes to `main` or `master` and opens a release pull request plus changelog for conventional commits.

`release-type` defaults to `simple`. Use `python` or `node` when that matches the repo. For a manifest, set `release-type` to an empty string and set `config-file` (and `manifest-file` if it is not `.release-please-manifest.json`).

`dry-run: true` sets `skip-github-release`, `skip-github-pull-request`, and `skip-labeling`. The self-test uses that so the action runs here without opening a release pull request. Callers that want releases leave `dry-run` at its default, `false`.

The job's token is the workflow `GITHUB_TOKEN` (`contents: write`, `pull-requests: write`, `issues: write`). Pull requests and tags created by that token do not start other workflows. If the release pull request must run CI, the owner has to add a separate token. This baseline does not create or store that token.

`cancel-in-progress` is false for a real release and true for a dry run.

## Adopt a workflow

1. In the repository, open **Actions → New workflow**. Templates from this repo appear after this change is on the default branch. Or copy a file from `workflow-templates/` into that repo's `.github/workflows/`.
2. Change the inputs. The snippets below are the ones that keep the current gates for four existing repos.
3. Let the new check go green on a pull request. Then delete the old workflow in that repo so two different gates are not required for the same job. Do not delete a check this baseline does not replace (markdown lint, docs, publish).
4. Ask the org owner to require the new check name in a ruleset. Do not mark a red run green to get there.

Caller workflows in other repositories are not created by this pull request.

### kernels

Current CI is Python 3.9–3.12, Ruff with `E`/`F` except `E501`, pytest coverage of `kernels` and `implementations` at 66% with branch coverage, plus the governance script, smoke script, and package build. The broader Ruff config in that repo is not the CI gate today, so pass `lint-command` or the default Ruff invocation will enforce rules the repo does not enforce yet. Codecov upload is not part of this workflow: the old job allowed it to fail, and this baseline will not.

```yaml
name: Python CI

on:
  push:
    branches: [main, master]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: python-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  python-ci:
    name: Python CI
    permissions:
      contents: read
    uses: Shards-foundation/.github/.github/workflows/python-ci.yml@main
    with:
      python-versions: '["3.9","3.10","3.11","3.12"]'
      coverage-threshold: 66
      coverage-packages: kernels,implementations
      coverage-branch: true
      lint-command: ruff check . --select E,F --ignore E501
      extra-checks: |
        python scripts/ci/check_governance_coverage.py coverage.json
        ./scripts/smoke.sh
        python -m pip install build
        python -m build
```

3.9 is end of life. The default matrix for a new repo is 3.11, 3.12, and 3.13. Keep 3.9 only while kernels still claims it.

### super-intelligence-agent

Current CI is Python 3.11, Flake8's syntax/undefined-name selector, and pytest. The old test step used `pytest || echo "Tests failed"`, which hid failures. This workflow does not. If pytest fails, the check stays red until the tests pass. There is no mypy config required by the old workflow; mypy still runs here if a mypy config is committed.

```yaml
name: Python CI

on:
  push:
    branches: [main, master]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: python-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  python-ci:
    name: Python CI
    permissions:
      contents: read
    uses: Shards-foundation/.github/.github/workflows/python-ci.yml@main
    with:
      python-versions: '["3.11"]'
      coverage-threshold: 0
      install-command: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then python -m pip install -r requirements.txt; fi
        if [ -f pyproject.toml ]; then python -m pip install .; fi
        python -m pip install pytest flake8
      lint-command: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### swarm-agent

Current CI installs with npm on Node 20, then tries a type check and a build and ignores their failures. The package manager field is pnpm `10.4.1`, and `package.json` defines `check` (`tsc --noEmit`), `build`, and `test` (`vitest run`). `auto` follows pnpm. Type check finds `tsconfig.json` and the `typescript` dependency and runs `tsc --noEmit`. Build and test scripts run, and a failure fails the job. That is stricter than the old `|| echo` steps. There is no `lint` script, so lint is skipped until you add one or set `lint-command`. Pass `node-versions: '["20"]'` to keep the current runtime. Add `"22"` when you want the second LTS.

```yaml
name: Node CI

on:
  push:
    branches: [main, master]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: node-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  node-ci:
    name: Node CI
    permissions:
      contents: read
    uses: Shards-foundation/.github/.github/workflows/node-ci.yml@main
    with:
      node-versions: '["20"]'
      package-manager: auto
```

To call the existing `check` script instead of the detected `tsc --noEmit`, set `typecheck-command: pnpm run check`.

### revenue-engine

Python CI today installs `api/requirements.txt`, runs a Flake8 syntax selector, and runs pytest. A second Flake8 invocation uses `--exit-zero`, so it is not a gate and it is not copied. The markdown lint workflow is separate and stays in that repo. `3.x` is not a matrix entry; pass explicit versions. `3.12` is the single current interpreter. Widen the JSON array when you want more.

```yaml
name: Python CI

on:
  push:
    branches: [main, master]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: python-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  python-ci:
    name: Python CI
    permissions:
      contents: read
    uses: Shards-foundation/.github/.github/workflows/python-ci.yml@main
    with:
      python-versions: '["3.12"]'
      coverage-threshold: 0
      install-command: |
        python -m pip install --upgrade pip
        python -m pip install -r api/requirements.txt
        python -m pip install pytest pyyaml flake8
      lint-command: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## Workflow templates

`workflow-templates/*.yml` each has a matching `.properties.json`. GitHub lists them on the **Actions** tab of repositories in this org once they are on the default branch of this repo.

| Template | Adds |
| --- | --- |
| `python-ci.yml` | Python caller, threshold off, versions 3.11–3.13 |
| `node-ci.yml` | Node caller, versions 20 and 22, package manager `auto` |
| `gitleaks.yml` | Secret scan on push, pull request, and Monday |
| `dependency-review.yml` | Dependency review on pull requests |
| `codeql.yml` | CodeQL on push, pull request, and Monday |
| `scorecard.yml` | Scorecard on push, pull request, and Monday |
| `security-baseline.yml` | The four security callers in one file |
| `release-please.yml` | Opt-in release-please. Do not add it unless the repo should release |

Use `security-baseline.yml` **or** the four individual security templates, not both.

## Dependabot

`docs/templates/dependabot.yml` is the config to copy to a repo's `.github/dependabot.yml`. It schedules **weekly** updates for `github-actions`, `npm` (also used for pnpm lockfiles), and `pip`. Delete ecosystems that repo does not have, and change `directory` when the manifest is not at `/` (revenue-engine's Python requirements live under `/api`).

Minor and patch updates are one group per ecosystem (`patterns: ["*"]`, `update-types: [minor, patch]`). Major updates are **not** in that group, so each major version opens its own pull request. `open-pull-requests-limit` is 5.

This repository's own `.github/dependabot.yml` is the same policy for the ecosystems that exist here: `github-actions` at `/`, and `npm` for the two Node fixtures. It does not list `pip` because these fixtures are installed from `pyproject.toml` optional dependencies, which this config does not try to update.

Dependabot security updates are a separate switch in the org settings. They are not folded into the minor/patch group. That is what you want for a security fix: its own pull request.

SHA-pinned actions are updated when the comment contains the version tag. Keep the `# vX.Y.Z` comment on the `uses:` line.

## Settings the owner turns on by hand

This pull request does not call the settings API and does not change branch protection, secret scanning, Dependabot, or Actions policy. The workflows still run without these. A few results stay local until the feature exists, and the docs say which.

1. **Rulesets or branch protection** on every default branch you care about, and on `Shards-foundation/.github` first, because other repos track `@main`.
   - Require a pull request before merging.
   - Require the status checks the repo actually adopted (`Python CI / Python CI`, `Node CI / Node CI`, `Gitleaks / Gitleaks`, `Dependency review / Dependency review`, `CodeQL / CodeQL`, `OpenSSF Scorecard / OpenSSF Scorecard`). Use the name from the first run.
   - Block force pushes. Prefer no bypass, including for administrators, on this `.github` repo.
2. **Secret scanning and push protection.** Org settings → Code security. Enable secret scanning for public repositories, then enable push protection. Private repositories need GitHub Code Security (or Advanced Security) licensed and enabled. The gitleaks workflow does not replace that; it runs even when the product switch is off.
3. **Dependency graph, Dependabot alerts, and Dependabot security updates.** Enable them for the org's repositories. Copy `docs/templates/dependabot.yml` into each repo and trim it. Dependency review fails until the dependency graph can build a snapshot for the pull request.
4. **Actions permissions.**
   - Allow actions and reusable workflows from `Shards-foundation` and from GitHub, and allow third-party actions only when they are pinned to a full commit SHA. Turn on the org policy that requires SHA pinning if it is available in the settings UI.
   - Default `GITHUB_TOKEN` permission: read repository contents. These workflows raise that per job when they must.
   - Keep the rule that workflows from outside collaborators need approval. Do not switch callers to `pull_request_target` to skip it.
   - For Release Please, allow Actions to open pull requests if the org currently blocks that. A token created by `GITHUB_TOKEN` will not trigger the CI workflows on the release PR. Add a separate token only if you need those workflows, and store it as an org or repo secret yourself.
5. **Code scanning.** Enable it for repositories that should show CodeQL and Scorecard in the Security tab. Disable the **default** CodeQL setup on any repo that uses `codeql.yml`, or the two setups will fight. Until code scanning is enabled, both workflows still analyze and still fail when CodeQL reports a result; they do not upload into the Security tab.
6. **Private Scorecard.** If a private repo's Scorecard job cannot read the repo with `GITHUB_TOKEN`, create a read-only PAT and pass it as `secrets.repo-token`. Do not commit it.

## What this baseline will not do

- It will not mark a failing test, lint, type check, or build as success.
- It will not use `pull_request_target`.
- It will not publish a package, deploy Pages, or run Kernel's old `safety check || true` vulnerability scan. Publishing stays a repo-specific workflow with `id-token: write` and an environment.
- It will not fail a repository for a low Scorecard score.
- It will not open releases unless that repository adds the Release Please caller.
- It will not edit other repositories or org settings.

## Self-test

`.github/workflows/self-test.yml` runs on this repository:

- `scripts/ci/check_workflows.py` on every workflow and template, plus a fixture that must be rejected.
- `actionlint` 1.7.12 (checksum-pinned) and the runner's shellcheck.
- `scripts/ci/negative_gates.sh`, which must see gitleaks fail on a credential generated at runtime (and must not print it), must see `--cov-fail-under=100` fail on `fixtures/python-low-cov`, and must see the Node lint script reject a `debugger` statement.
- Python CI against `fixtures/python-app` on 3.12 and 3.13 with `coverage-threshold: 80`.
- Python CI against `fixtures/python-low-cov` on 3.12 with `coverage-threshold: 0`, so a partial suite stays green only because the gate is off.
- Node CI against `fixtures/node-npm` on Node 20 and 22, and against `fixtures/node-pnpm` on Node 22.
- Gitleaks, dependency review, CodeQL (auto-detected Python and JavaScript/TypeScript), and Scorecard on this repository.
- Release Please with `dry-run: true`.

The fixtures are not products. They exist so this pull request's own checks exercise the workflows.
