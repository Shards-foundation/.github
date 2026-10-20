#!/usr/bin/env python3
"""Policy checks for this repo's workflows and templates.

Third-party actions must be pinned to a full commit SHA with a version comment.
Reusable workflows in this org repo may be called at @main. pull_request_target
and continue-on-error are rejected.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ORG_REPO = "Shards-foundation/.github"
SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION_COMMENT = re.compile(r"\bv\d+(?:\.\d+)*\b")
USES_RE = re.compile(
    r"^\s*(?:-\s*)?uses:\s*(['\"]?)([^'\"#\s]+)\1(?:\s+#\s*(.+))?\s*$"
)
WORKFLOW_GLOBS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "workflow-templates/*.yml",
    "workflow-templates/*.yaml",
)


def fail(path: Path, line: int, message: str, errors: list[str]) -> None:
    errors.append(f"{path}:{line}: {message}")


def check_uses(path: Path, line_no: int, value: str, comment: str | None, errors: list[str]) -> None:
    if value.startswith("./"):
        if not value.startswith("./.github/workflows/") and not value.startswith("./.github/actions/"):
            fail(path, line_no, f"local action must live under .github/: {value}", errors)
        return

    if value.startswith("docker://"):
        if "@sha256:" not in value or not re.search(r"@sha256:[0-9a-f]{64}$", value):
            fail(path, line_no, f"docker action must be pinned by sha256 digest: {value}", errors)
        return

    match = re.fullmatch(r"(?P<repo>[^/]+/[^/@]+)(?P<sub>/[^@]+)?@(?P<ref>.+)", value)
    if not match:
        fail(path, line_no, f"unpinned or unparseable action: {value}", errors)
        return

    repo = match.group("repo")
    ref = match.group("ref")
    if repo == ORG_REPO:
        if ref in {"main", "master"} or SHA.fullmatch(ref):
            return
        fail(
            path,
            line_no,
            f"org reusable workflow must use @main or a full SHA, got @{ref}",
            errors,
        )
        return

    if not SHA.fullmatch(ref):
        fail(path, line_no, f"third-party action must be pinned to a 40-character SHA: {value}", errors)
        return
    if comment is None or VERSION_COMMENT.search(comment) is None:
        fail(
            path,
            line_no,
            f"pinned action is missing a version comment such as '# v1.2.3': {value}",
            errors,
        )


def check_file(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "pull_request_target" in stripped:
            fail(path, line_no, "pull_request_target is not allowed", errors)
        if re.search(r"continue-on-error:\s*true\b", stripped):
            fail(path, line_no, "continue-on-error: true is not allowed", errors)
        uses = USES_RE.match(line)
        if uses:
            check_uses(path, line_no, uses.group(2), uses.group(3), errors)

    if not re.search(r"(?m)^[ \t]*permissions:\s*$", text):
        fail(path, 1, "workflow is missing a permissions block", errors)
    if "concurrency:" not in text or "cancel-in-progress:" not in text:
        fail(path, 1, "workflow is missing concurrency with cancel-in-progress", errors)

    runs_on = len(re.findall(r"(?m)^\s*runs-on:\s*", text))
    timeouts = len(re.findall(r"(?m)^\s*timeout-minutes:\s*", text))
    if runs_on and timeouts < runs_on:
        fail(
            path,
            1,
            f"every runs-on job needs timeout-minutes ({timeouts} timeouts for {runs_on} jobs)",
            errors,
        )


def workflow_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in WORKFLOW_GLOBS:
        found.extend(root.glob(pattern))
    return sorted(found)


def scan(root: Path) -> list[str]:
    errors: list[str] = []
    files = workflow_files(root)
    if not files:
        errors.append(f"{root}: no workflow files found")
        return errors
    for path in files:
        check_file(path, errors)
    return errors


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        good = workflows / "good.yml"
        good.write_text(
            """name: Good
on:
  workflow_call:
permissions:
  contents: read
concurrency:
  group: good
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: ./.github/workflows/other.yml
      - uses: Shards-foundation/.github/.github/workflows/python-ci.yml@main
""",
            encoding="utf-8",
        )
        bad = workflows / "bad.yml"
        bad.write_text(
            """name: Bad
on:
  pull_request_target:
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        continue-on-error: true
""",
            encoding="utf-8",
        )
        errors = scan(root)
        joined = "\n".join(errors)
        expected = [
            "pull_request_target",
            "continue-on-error",
            "40-character SHA",
            "timeout-minutes",
            "permissions",
            "concurrency",
        ]
        missing = [item for item in expected if item not in joined]
        if missing:
            print("self-test did not report:", ", ".join(missing), file=sys.stderr)
            print(joined, file=sys.stderr)
            return 1
        if any(str(good) in error for error in errors):
            print("self-test flagged the valid fixture:", file=sys.stderr)
            print(joined, file=sys.stderr)
            return 1
    print("workflow policy self-test passed")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    errors = scan(REPO_ROOT)
    if errors:
        print("workflow policy check failed:", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"workflow policy check passed ({len(workflow_files(REPO_ROOT))} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
