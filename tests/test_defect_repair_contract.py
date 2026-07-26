from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(path: str) -> str:
    return " ".join(read(path).lower().split())


class DefectRepairContractTests(unittest.TestCase):
    """HS-QA-BUG/acceptance-v1: SC-004/005 trace to AC-5/6/7."""

    def test_diagnose_only_emits_a_safe_append_only_receipt(self) -> None:
        diagnose = normalized("skills/diagnose/SKILL.md")
        receipt = normalized("skills/diagnose/diagnosis-receipt-template.md")

        for marker in (
            "diagnosis receipt",
            "diagnosed",
            "inconclusive",
            "reproduction-blocked",
            "unsafe",
            "destructive",
            "production-only",
            "intermittent",
            "do not force",
            "append",
            "same stable bug-id",
        ):
            self.assertIn(marker, diagnose + receipt)
        for forbidden in ("## phase 3", "fix at the root"):
            self.assertNotIn(forbidden, diagnose)
        self.assertIn("does not edit product code", diagnose)
        self.assertIn("does not edit product code, create a replacement defect", diagnose)
        self.assertIn("or mark the bug case `verified`", diagnose)

    def test_product_defect_flow_has_four_ordered_receipts(self) -> None:
        workflow = normalized("skills/bug-workflow/SKILL.md")

        markers = (
            "diagnosis receipt",
            "implement defect receipt",
            "new deployment receipt",
            "qa verification attempt",
        )
        positions = [workflow.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("same stable bug-id", workflow)
        self.assertIn("append-only", workflow)
        self.assertIn("do not overwrite", workflow)

    def test_implement_accepts_a_versioned_defect_packet_under_rd_ownership(self) -> None:
        implement = normalized("skills/implement/SKILL.md")
        packet = normalized("skills/implement/defect-repair-receipt-template.md")

        for marker in (
            "versioned defect packet",
            "hs-defect-packet/v1",
            "stable bug-id",
            "product-defect",
            "diagnosis receipt",
            "original failed-artifact evidence",
            "repair attempt",
            "implement defect receipt",
            "rd unit",
            "rd api-contract",
            "tdd",
            "review",
            "new deployment receipt",
        ):
            self.assertIn(marker, implement + packet)
        for owner in (
            "worktrees",
            "prs",
            "ci",
            "deployment",
            "recovery",
            "tracker",
        ):
            self.assertIn(owner, implement)
        self.assertRegex(implement, r"rd.{0,120}root-cause repair")
        self.assertIn("must not set `verified`", implement)

    def test_fixed_artifact_handoff_is_exact_and_traceable(self) -> None:
        handoff = normalized("skills/testing-workflow/qa-handoff-template.md")
        repair_receipt = normalized(
            "skills/implement/defect-repair-receipt-template.md"
        )

        for marker in (
            "stable bug-id",
            "fix attempt",
            "original failed artifact",
            "exact new full source sha",
            "exact new deployed artifact/environment revision",
            "new deployment receipt",
            "affected sc-ids",
            "rd verification summary",
            "diagnosis receipt",
            "implement defect receipt",
        ):
            self.assertIn(marker, handoff)
        for marker in (
            "every receipt must name the same stable bug-id",
            "diagnosis receipt retains its own diagnosis-attempt",
            "stable bug-id / repair attempt",
        ):
            self.assertIn(marker, handoff + repair_receipt)

    def test_qa_retest_scope_and_attempt_history_stay_qa_owned(self) -> None:
        workflow = normalized("skills/testing-workflow/SKILL.md")
        ledger = normalized("skills/testing-workflow/execution-ledger-template.md")

        for marker in (
            "original observation",
            "affected sc-id journey",
            "proportionate neighbouring regression",
            "fixed artifact",
            "qa verification attempt",
            "fix attempt",
            "retest attempt",
            "append-only",
            "original failed-artifact evidence",
            "never overwrite",
            "normalized scenario classification",
            "does not assign the final bug case disposition",
        ):
            self.assertIn(marker, workflow + ledger)
        self.assertIn("qa execution only", workflow)
        self.assertIn("does not execute unit or api-contract tests", workflow)

    def test_only_qa_can_close_or_reopen_fixed_artifact_verification(self) -> None:
        workflow = normalized("skills/testing-workflow/SKILL.md")
        implement = normalized("skills/implement/SKILL.md")

        self.assertRegex(workflow, r"only qa.{0,80}`verified`")
        self.assertRegex(workflow, r"repeated failure.{0,80}`reopened`")
        self.assertRegex(
            workflow,
            r"(missing|mismatched).{0,120}deployment.{0,120}`blocked`",
        )
        for marker in (
            "stage 2",
            "stage 3",
            "qa ownership preflight",
            "ordered first-match normalization",
            "stage 4",
            "retry-green remains `flaky`",
            "every required scenario classification is `pass`",
        ):
            self.assertIn(marker, workflow)
        self.assertIn("resumable", workflow)
        self.assertIn("explicit human decision", workflow)
        self.assertIn("linked follow-up", workflow)
        self.assertNotIn("set `verified`", implement.replace("must not set `verified`", ""))

    def test_acceptance_report_compares_original_and_fixed_artifacts(self) -> None:
        report = normalized("skills/testing-workflow/acceptance-report-template.md")

        for marker in (
            "stable bug-id",
            "original failure",
            "original failed artifact",
            "fixed-artifact retest",
            "same bug-id",
            "contract trace",
            "qa verification attempt",
            "human caveat decision",
            "same bug-id",
            "other blocking acceptance failures return to `dev-workflow`",
        ):
            self.assertIn(marker, report)

    def test_completed_release_inventory_version_and_install_paths_are_consistent(self) -> None:
        readme = read("README.md")
        self.assertIn("plus nine self-contained blocks", readme)
        self.assertIn("codex plugin add harness-ship@harness-ship", readme)
        self.assertIn("codex plugin marketplace upgrade harness-ship", readme)
        self.assertIn("claude plugin install harness-ship@harness-ship", readme)
        self.assertIn("claude plugin update harness-ship@harness-ship", readme)

        versions = {
            json.loads(read(path))["version"]
            for path in (
                ".claude-plugin/plugin.json",
                ".codex-plugin/plugin.json",
            )
        }
        self.assertEqual(len(versions), 1)
        version = versions.pop()
        self.assertGreaterEqual(
            tuple(int(part) for part in version.split(".")),
            (0, 6, 1),
        )

        marketplace = json.loads(read(".claude-plugin/marketplace.json"))
        self.assertIn(
            "nine self-contained blocks",
            marketplace["plugins"][0]["description"].lower(),
        )
        ci = read(".github/workflows/ci.yml")
        self.assertIn("github.event.pull_request.base.sha", ci)
        self.assertIn("github.event.pull_request.head.sha", ci)
        self.assertIn(
            'scripts/validate_plugin_lifecycle.sh "$BASE_SHA" "$CURRENT_SHA"',
            ci,
        )
        lifecycle = normalized("scripts/validate_plugin_lifecycle.sh")
        for marker in (
            "fresh-install receipt",
            "upgrade receipt",
            "diagnosis-receipt-template.md",
            "defect-repair-receipt-template.md",
            "no skills discovered after install",
        ):
            self.assertIn(marker, lifecycle)

        for path in (
            "skills/bug-workflow/SKILL.md",
            "skills/diagnose/SKILL.md",
            "skills/implement/SKILL.md",
            "skills/testing-workflow/SKILL.md",
        ):
            text = normalized(path)
            for peer in ("bug-workflow", "diagnose", "implement", "testing-workflow"):
                if peer not in path:
                    self.assertIn(peer, text)


if __name__ == "__main__":
    unittest.main()
