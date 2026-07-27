#!/usr/bin/env python3
"""Verify that a TDD receipt's RED actually happened.

The old receipt asked for `RED: <command> — failed because <reason>`. Nothing
bound that line to an execution: no output, no exit code, no commit. And one
executor owns both RED and GREEN, so the only agent that could misreport was
also the sole holder of the evidence, reporting in prose to a root that could
not check it. An executor that wrote the implementation first and composed the
receipt afterwards produced artifacts identical to one that did the work.

This makes the claim falsifiable with two git commands. The RED commit must
contain the failing test and no implementation; the GREEN commit must contain
the implementation. Root runs `check` and reads the exit code.

What this does not prove: that the test failed for the *right* reason. That
judgement stays in `tdd`'s invalid-RED rules — a syntax error is still a bad
RED, and no amount of git plumbing detects it. This closes the cheap lie, not
the expensive one.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Language-agnostic: a path is a test if any component or the filename says so.
TEST_PATH = re.compile(
    r"(^|/)(tests?|spec|specs|__tests__)(/|$)|(^|/)(test_[^/]+|[^/]+_test\.[^/.]+|[^/]+\.(test|spec)\.[^/.]+)$"
)
SHA_LINE = re.compile(r"(?mi)^\s*[-*]\s*(?P<label>RED|GREEN) commit:\s*`?(?P<sha>[0-9a-f]{7,40})`?\s*$")
FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)


class ReceiptError(ValueError):
    """The receipt does not evidence a real RED."""


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ReceiptError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def is_ancestor(repo: Path, earlier: str, later: str) -> bool:
    """`merge-base --is-ancestor` reports by exit code, so it cannot use git()."""
    return subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", earlier, later],
        capture_output=True,
    ).returncode == 0


def is_test_path(path: str) -> bool:
    return bool(TEST_PATH.search(path))


def changed_paths(repo: Path, sha: str) -> List[str]:
    # --root so an initial commit still reports its files.
    return [p for p in git(repo, "show", "--name-only", "--format=", "--root", sha).splitlines() if p]


def parse_receipt(text: str) -> Dict[str, str]:
    commits = {m.group("label").upper(): m.group("sha") for m in SHA_LINE.finditer(text)}
    for label in ("RED", "GREEN"):
        if label not in commits:
            raise ReceiptError(f"receipt cites no {label} commit")
    fences = [block.strip() for block in FENCE.findall(text) if block.strip()]
    if not fences:
        raise ReceiptError("receipt quotes no failing output; paste the first 20 lines verbatim")
    return {**commits, "output": fences[0]}


def check(receipt_text: str, repo: Path) -> Dict[str, object]:
    receipt = parse_receipt(receipt_text)
    red = git(repo, "rev-parse", "--verify", f"{receipt['RED']}^{{commit}}")
    green = git(repo, "rev-parse", "--verify", f"{receipt['GREEN']}^{{commit}}")

    problems: List[str] = []
    if red == green:
        problems.append("RED and GREEN are the same commit")
    elif not is_ancestor(repo, red, green):
        problems.append(f"RED commit {red[:12]} does not precede GREEN {green[:12]}")

    red_paths = changed_paths(repo, red)
    implementation_in_red = sorted(p for p in red_paths if not is_test_path(p))
    if not any(is_test_path(p) for p in red_paths):
        problems.append(f"RED commit {red[:12]} adds no test file")
    if implementation_in_red:
        problems.append(
            f"RED commit {red[:12]} already contains implementation: {', '.join(implementation_in_red)}"
        )

    green_paths = changed_paths(repo, green)
    if not any(not is_test_path(p) for p in green_paths):
        problems.append(f"GREEN commit {green[:12]} changes no implementation file")

    verdict = {
        "red": red,
        "green": green,
        "red_paths": red_paths,
        "green_paths": green_paths,
        "output_lines": len(receipt["output"].splitlines()),
    }
    if problems:
        return {**verdict, "status": "fail", "problems": problems}
    return {**verdict, "status": "pass"}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--receipt", required=True, type=Path)
    check_parser.add_argument("--repo", default=Path("."), type=Path)
    args = parser.parse_args(argv)

    try:
        result = check(args.receipt.read_text(encoding="utf-8"), args.repo)
    except (ReceiptError, OSError, UnicodeError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
