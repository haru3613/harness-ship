"""Behavioural tests for the anti-fake-green recomputation."""

from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "fake_green.py"

spec = importlib.util.spec_from_file_location("fake_green", HELPER)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

HEADER = "| Assertion | Classification | Reason |\n|---|---|---|\n"


def ledger(rows: list, denominator: int = None) -> str:
    if denominator is None:
        denominator = len(rows)
    body = "".join(
        f"| `{location}` | {classification} | {reason} |\n"
        for location, classification, reason in rows
    )
    return (
        "# Execution ledger\n\n"
        "### Assertion audit — QA-RUN-7 / SC-002\n"
        f"- Denominator: {denominator} assertions in the QA checks executed for this scenario\n\n"
        f"{HEADER}{body}\n"
    )


def rows(ok: int = 0, static: int = 0, weak: int = 0) -> list:
    return (
        [(f"tests/e2e/a.spec.ts:{i}", "ok", "") for i in range(ok)]
        + [(f"tests/e2e/b.spec.ts:{i}", "static", "asserts only status 200") for i in range(static)]
        + [(f"tests/e2e/c.spec.ts:{i}", "weak", "recomputes expected with the same helper") for i in range(weak)]
    )


class ThresholdTests(unittest.TestCase):
    def test_mostly_real_assertions_pass(self) -> None:
        result = audit.check(ledger(rows(ok=8, static=1, weak=1)))

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["counts"], {"ok": 8, "static": 1, "weak": 1})

    def test_static_majority_is_rejected(self) -> None:
        result = audit.check(ledger(rows(ok=4, static=6)))

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["static_ratio"], 0.6)
        self.assertTrue(any("static" in p for p in result["problems"]))

    def test_static_exactly_at_the_limit_passes(self) -> None:
        """The rule is `> 50%`, not `>= 50%`."""
        self.assertEqual(audit.check(ledger(rows(ok=5, static=5)))["status"], "pass")

    def test_weak_exactly_at_the_limit_passes(self) -> None:
        """The rule is `> 30%`, not `>= 30%`."""
        self.assertEqual(audit.check(ledger(rows(ok=7, weak=3)))["status"], "pass")

    def test_weak_over_thirty_percent_is_rejected(self) -> None:
        result = audit.check(ledger(rows(ok=6, weak=4)))

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("weak" in p for p in result["problems"]))

    def test_both_thresholds_breached_are_both_reported(self) -> None:
        result = audit.check(ledger(rows(ok=1, static=6, weak=4)))

        self.assertEqual(len(result["problems"]), 2)

    def test_rejected_assertions_are_named(self) -> None:
        result = audit.check(ledger(rows(ok=4, static=6)))

        self.assertEqual(len(result["rejected"]), 6)
        self.assertTrue(all("b.spec.ts" in location for location in result["rejected"]))


class AuditabilityTests(unittest.TestCase):
    """The point of the ticket: a verdict nobody can recompute is not a verdict."""

    def test_missing_audit_section_is_rejected(self) -> None:
        with self.assertRaises(audit.AuditError) as caught:
            audit.check("# Execution ledger\n\nAll green, looked fine.\n")

        self.assertIn("no `Assertion audit` section", str(caught.exception))

    def test_missing_denominator_is_rejected(self) -> None:
        text = ledger(rows(ok=3)).replace(
            "- Denominator: 3 assertions in the QA checks executed for this scenario\n", ""
        )

        with self.assertRaises(audit.AuditError) as caught:
            audit.check(text)

        self.assertIn("no denominator", str(caught.exception))

    def test_enumeration_that_disagrees_with_the_denominator_is_rejected(self) -> None:
        with self.assertRaises(audit.AuditError) as caught:
            audit.check(ledger(rows(ok=3), denominator=20))

        self.assertIn("enumerates 3 assertions but declares 20", str(caught.exception))

    def test_empty_enumeration_is_rejected(self) -> None:
        with self.assertRaises(audit.AuditError):
            audit.check(ledger([], denominator=0))

    def test_static_row_without_a_reason_is_rejected(self) -> None:
        text = ledger([("tests/e2e/a.spec.ts:9", "static", "")])

        with self.assertRaises(audit.AuditError) as caught:
            audit.check(text)

        self.assertIn("with no reason", str(caught.exception))

    def test_ok_row_needs_no_reason(self) -> None:
        self.assertEqual(audit.check(ledger([("t.spec.ts:1", "ok", "")]))["status"], "pass")

    def test_unrelated_ledger_tables_are_ignored(self) -> None:
        text = ledger(rows(ok=2)).replace(
            "# Execution ledger\n",
            "# Execution ledger\n\n| Attempt | SC-ID | Result |\n|---|---|---|\n| 1 | SC-002 | PASS |\n",
        )

        self.assertEqual(audit.check(text)["counts"], {"ok": 2, "static": 0, "weak": 0})


class CliTests(unittest.TestCase):
    def run_cli(self, text: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.md"
            path.write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(HELPER), "check", "--ledger", str(path)],
                capture_output=True,
                text=True,
            )

    def test_exit_zero_on_a_healthy_suite(self) -> None:
        self.assertEqual(self.run_cli(ledger(rows(ok=9, static=1))).returncode, 0)

    def test_exit_two_on_a_fake_green_suite(self) -> None:
        result = self.run_cli(ledger(rows(ok=2, static=8)))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "fail")

    def test_exit_two_when_the_audit_is_absent(self) -> None:
        self.assertEqual(self.run_cli("# Execution ledger\n\nlooked fine\n").returncode, 2)


if __name__ == "__main__":
    unittest.main()
