#!/usr/bin/env python3
"""Reject protected Harness Ship contract drift under an unchanged version.

This repository-owned check prevents accidental drift. It is not a tamper-proof
authorization boundary; branch protection and human review still own merge policy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import List, Tuple


MANIFESTS = (
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
)
PROTECTED_PATHS = (
    ".github/workflows/ci.yml",
    "agents/harness-ship-independent-verifier.md",
    "scripts/check_release_contract.py",
    "scripts/role_binding_contract.py",
    "scripts/validate_plugin_lifecycle.sh",
    "skills/implement/SKILL.md",
    "skills/setup/SKILL.md",
)


class ReleaseContractError(ValueError):
    """A release-sensitive diff has invalid or stale version metadata."""


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ReleaseContractError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def resolve_commit(repo: Path, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()


def manifest_version(repo: Path, ref: str, path: str) -> Tuple[int, int, int]:
    try:
        payload = json.loads(git(repo, "show", f"{ref}:{path}"))
        raw = payload["version"]
        parts = tuple(int(part) for part in raw.split("."))
    except (json.JSONDecodeError, KeyError, AttributeError, ValueError) as error:
        raise ReleaseContractError(
            f"{ref}:{path} must contain a three-part numeric version"
        ) from error
    if len(parts) != 3 or any(part < 0 for part in parts):
        raise ReleaseContractError(
            f"{ref}:{path} must contain a three-part numeric version"
        )
    return parts


def display(version: Tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def synchronized_version(repo: Path, ref: str) -> Tuple[int, int, int]:
    versions = {manifest_version(repo, ref, path) for path in MANIFESTS}
    if len(versions) != 1:
        raise ReleaseContractError(
            f"{ref} has unsynchronized Codex and Claude plugin versions"
        )
    return versions.pop()


def changed_protected_paths(repo: Path, base: str, current: str) -> List[str]:
    output = git(
        repo,
        "diff",
        "--name-only",
        base,
        current,
        "--",
        *PROTECTED_PATHS,
    )
    return [line for line in output.splitlines() if line]


def check(repo: Path, base_ref: str, current_ref: str) -> str:
    base = resolve_commit(repo, base_ref)
    current = resolve_commit(repo, current_ref)
    base_version = synchronized_version(repo, base)
    current_version = synchronized_version(repo, current)
    if current_version < base_version:
        raise ReleaseContractError(
            f"version regressed: {display(base_version)} -> {display(current_version)}"
        )

    changed = changed_protected_paths(repo, base, current)
    if changed and current_version <= base_version:
        rendered = ", ".join(changed)
        raise ReleaseContractError(
            "protected contract changed without version increase "
            f"({display(base_version)} -> {display(current_version)}): {rendered}. "
            "Bump both plugin manifest versions."
        )
    if changed:
        return (
            "release contract pass: "
            f"{display(base_version)} -> {display(current_version)}; "
            f"protected paths changed: {', '.join(changed)}"
        )
    return (
        "release contract pass: "
        f"{display(base_version)} -> {display(current_version)}; "
        "no protected contract drift"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("base_ref")
    parser.add_argument("current_ref")
    args = parser.parse_args()
    try:
        print(check(args.repo.resolve(), args.base_ref, args.current_ref))
        return 0
    except (OSError, ReleaseContractError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
