#!/usr/bin/env python3
"""Attended, fail-closed Harness Ship GitHub release publication.

All version, channel, exact-main, tag-state, and plugin lifecycle checks finish
before a missing tag is created. Existing matching tags/releases are resumed
idempotently. Tags are never moved, deleted, or rolled back.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


class PublicationError(RuntimeError):
    pass


def run(
    command: list[str], *, cwd: Path, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        raise PublicationError(
            result.stderr.strip() or result.stdout.strip() or "command failed"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--main-ref", default="refs/remotes/origin/main")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--channel", default="stable")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()

    try:
        preflight = [
            "python3",
            str(repo / "scripts" / "check_release_contract.py"),
            "post-merge",
            "--repo",
            str(repo),
            "--candidate",
            args.candidate,
            "--main-ref",
            args.main_ref,
            "--tag",
            args.tag,
            "--channel",
            args.channel,
            "--dry-run",
        ]
        contract = run(preflight, cwd=repo).stdout.strip()
        parent = run(
            ["git", "rev-parse", f"{args.candidate}^"], cwd=repo
        ).stdout.strip()
        lifecycle = run(
            [
                "bash",
                str(repo / "scripts" / "validate_plugin_lifecycle.sh"),
                parent,
                args.candidate,
            ],
            cwd=repo,
        ).stdout.strip()
        if args.dry_run:
            print(contract)
            print(lifecycle)
            print("publication dry-run: zero mutation")
            return 0

        release = run(
            [
                "gh",
                "release",
                "view",
                args.tag,
                "--json",
                "tagName,url",
            ],
            cwd=repo,
            check=False,
        )
        if release.returncode not in (0, 1):
            raise PublicationError(
                release.stderr.strip() or "could not inspect GitHub release state"
            )
        tag_target = run(
            ["git", "rev-parse", "--verify", f"refs/tags/{args.tag}^{{}}"],
            cwd=repo,
            check=False,
        ).stdout.strip()
        if release.returncode == 0:
            if tag_target != args.candidate:
                raise PublicationError(
                    "existing release is not backed by the matching candidate tag"
                )
            print(contract)
            print(f"publication receipt: existing matching release {release.stdout.strip()}")
            return 0

        if not tag_target:
            run(
                [
                    "git",
                    "tag",
                    "-a",
                    args.tag,
                    args.candidate,
                    "-m",
                    f"Harness Ship {args.tag}",
                ],
                cwd=repo,
            )
            run(
                ["git", "push", "origin", f"refs/tags/{args.tag}"],
                cwd=repo,
            )
        run(
            [
                "gh",
                "release",
                "create",
                args.tag,
                "--verify-tag",
                "--title",
                f"Harness Ship {args.tag}",
                "--generate-notes",
            ],
            cwd=repo,
        )
        print(contract)
        print(
            f"publication receipt: channel={args.channel} tag={args.tag} "
            f"sha={args.candidate}"
        )
        return 0
    except (OSError, PublicationError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
