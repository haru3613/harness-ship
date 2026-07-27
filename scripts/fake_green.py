#!/usr/bin/env python3
"""Recompute the anti-fake-green verdict from the recorded assertion audit.

Stage 4 of `testing-workflow` used to read:

    > 50% static assertions -> reject.
    > 30% weak assertions -> reject.

Those percentages were computed by an LLM, about output an LLM produced, with
no tool, no defined denominator, and no record of the count. The verdict could
not be reproduced or challenged — a vibe threshold wearing a metric's clothes.

Classifying an assertion still needs judgement, and this script does not
attempt it. What it does is force the judgement to be *written down per
assertion, with a location and a reason*, and then do the arithmetic itself.
The auditor argues about rows; the threshold is no longer a matter of opinion.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

CLASSIFICATIONS = ("static", "weak", "ok")
STATIC_LIMIT = 0.50
WEAK_LIMIT = 0.30

HEADING = re.compile(r"(?mi)^#+\s*Assertion audit\b[^\n]*$")
ROW = re.compile(r"(?m)^\|(?P<cells>.+)\|\s*$")
DENOMINATOR = re.compile(r"(?mi)^\s*[-*]\s*Denominator:\s*(?P<count>\d+)\b")


class AuditError(ValueError):
    """The ledger does not record an auditable assertion classification."""


def parse_rows(section: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for match in ROW.finditer(section):
        cells = [cell.strip().strip("`") for cell in match.group("cells").split("|")]
        if len(cells) < 3:
            continue
        location, classification, reason = cells[0], cells[1].lower(), cells[2]
        if classification not in CLASSIFICATIONS:
            continue  # header, separator, or a table that is not the audit
        if not location:
            raise AuditError("an audit row has no assertion location")
        if classification in ("static", "weak") and not reason:
            raise AuditError(f"{location} is classified {classification} with no reason")
        rows.append({"location": location, "classification": classification, "reason": reason})
    return rows


def check(ledger_text: str) -> Dict[str, object]:
    if not HEADING.search(ledger_text):
        raise AuditError("ledger records no `Assertion audit` section")
    declared = DENOMINATOR.search(ledger_text)
    if not declared:
        raise AuditError("assertion audit declares no denominator")
    denominator = int(declared.group("count"))

    rows = parse_rows(ledger_text)
    if not rows:
        raise AuditError("assertion audit enumerates no assertions")
    if len(rows) != denominator:
        raise AuditError(
            f"assertion audit enumerates {len(rows)} assertions but declares {denominator}"
        )
    if denominator == 0:
        raise AuditError("assertion audit denominator is zero")

    counts = {name: sum(1 for row in rows if row["classification"] == name) for name in CLASSIFICATIONS}
    static_ratio = counts["static"] / denominator
    weak_ratio = counts["weak"] / denominator

    problems: List[str] = []
    if static_ratio > STATIC_LIMIT:
        problems.append(
            f"{counts['static']}/{denominator} static assertions "
            f"({static_ratio:.0%}) exceeds {STATIC_LIMIT:.0%}"
        )
    if weak_ratio > WEAK_LIMIT:
        problems.append(
            f"{counts['weak']}/{denominator} weak assertions "
            f"({weak_ratio:.0%}) exceeds {WEAK_LIMIT:.0%}"
        )

    verdict = {
        "denominator": denominator,
        "counts": counts,
        "static_ratio": round(static_ratio, 4),
        "weak_ratio": round(weak_ratio, 4),
        "rejected": sorted(
            row["location"] for row in rows if row["classification"] in ("static", "weak")
        ),
    }
    if problems:
        return {**verdict, "status": "fail", "problems": problems}
    return {**verdict, "status": "pass"}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--ledger", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        result = check(args.ledger.read_text(encoding="utf-8"))
    except (AuditError, OSError, UnicodeError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
