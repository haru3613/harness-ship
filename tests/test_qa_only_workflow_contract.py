from pathlib import Path
import re
from typing import Optional
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def section(text: str, start: str, end: Optional[str] = None) -> str:
    value = text.split(start, maxsplit=1)[1]
    if end is not None:
        value = value.split(end, maxsplit=1)[0]
    return " ".join(value.lower().split())


class QAOnlyWorkflowContractTests(unittest.TestCase):
    """HS-QA-BUG/acceptance-v1: SC-002 traces to AC-2, AC-3, and AC-7."""

    def test_qa_starts_only_from_a_complete_valid_handoff(self) -> None:
        workflow = read("skills/testing-workflow/SKILL.md")
        stage2 = section(
            workflow,
            "## Stage 2 — Route approved scenarios by ownership",
            "## Stage 3",
        )

        for marker in (
            "qa-handoff-template.md",
            "full 40-character source sha",
            "deployed artifact/environment revision",
            "artifact-provenance source",
            "fixtures/accounts",
            "known risks",
            "rd coverage summary",
            "qa evidence location",
            "writable",
            "not ready",
            "do not start stage 3",
        ):
            self.assertIn(marker, stage2)
        self.assertRegex(stage2, r"missing.{0,80}(placeholder|mismatched)")

    def test_rd_coverage_is_informational_and_qa_never_executes_rd_tests(self) -> None:
        workflow = read("skills/testing-workflow/SKILL.md")
        stage2 = section(
            workflow,
            "## Stage 2 — Route approved scenarios by ownership",
            "## Stage 3",
        )

        for marker in (
            "informational only",
            "avoid duplicate testing",
            "does not audit the tdd cycle",
            "does not execute unit or api-contract tests",
        ):
            self.assertIn(marker, stage2)
        self.assertNotIn("test the contract against the api schema", stage2)

    def test_qa_execution_scope_is_limited_to_approved_qa_layers(self) -> None:
        workflow = read("skills/testing-workflow/SKILL.md")
        self.assertIn("## Stage 3 — Execute QA scope", workflow)
        stage3 = section(
            workflow,
            "## Stage 3",
            "## Stage 4",
        )

        for marker in (
            "integration",
            "e2e",
            "user journeys",
            "risk-selected",
            "manual",
            "exploratory",
            "non-functional",
            "qa execution only",
        ):
            self.assertIn(marker, stage3)
        self.assertIn("configured qa commands", stage3)
        self.assertNotRegex(stage3, r"\b(run|execute)\b.{0,50}\b(unit|api-contract)\b")

    def test_rd_workflows_never_consume_qa_commands_before_handoff(self) -> None:
        tdd = " ".join(read("skills/tdd/SKILL.md").lower().split())
        implement_raw = read("skills/implement/SKILL.md")
        implement = " ".join(implement_raw.lower().split())

        for workflow in (tdd, implement):
            self.assertIn("rd unit", workflow)
            self.assertIn("rd api-contract", workflow)
            self.assertRegex(
                workflow,
                r"(do not|never).{0,100}(run|execute|consume).{0,100}qa.{0,60}command",
            )
        self.assertNotIn("repository's test commands", tdd)
        self.assertNotIn("full configured suite", implement)

        for path in (
            "skills/dev-workflow/SKILL.md",
            "skills/implement/SKILL.md",
            "skills/tdd/SKILL.md",
            "skills/testing-workflow/SKILL.md",
        ):
            entrypoint = " ".join(read(path).lower().split())
            self.assertIn("config version 1", entrypoint)
            self.assertIn("legacy or unversioned", entrypoint)
            self.assertIn("run `setup`", entrypoint)
            self.assertIn("do not reinterpret", entrypoint)
            self.assertIn("generic test command", entrypoint)

        dispatch = section(
            implement_raw,
            "## Dispatch contract",
            "## Phase 0",
        )
        self.assertIn("every pre-handoff child", dispatch)
        self.assertRegex(
            dispatch,
            r"(do not|must not|never).{0,120}(run|invoke|consume).{0,100}qa.{0,80}(command|job)",
        )

        phase0 = section(
            implement_raw,
            "## Phase 0 — Resolve the work and pin the fixed point",
            "## Durable checkpoint protocol",
        )
        self.assertIn("rd unit", phase0)
        self.assertIn("rd api-contract", phase0)
        self.assertRegex(
            phase0,
            r"(do not|never).{0,100}(run|execute|consume).{0,100}qa.{0,60}command",
        )
        self.assertNotIn("each approved seam", phase0)

        phase3 = section(implement_raw, "## Phase 3", "## Phase 4")
        self.assertIn("rd-owned independent verification", phase3)
        self.assertRegex(
            phase3,
            r"(do not|must not|never).{0,120}(run|invoke|consume).{0,100}qa.{0,80}(command|job)",
        )
        phase3_review = phase3.split("run `review`", maxsplit=1)[1]
        self.assertIn("rd-owned pre-handoff review", phase3_review)
        self.assertRegex(
            phase3_review,
            r"(do not|must not|never).{0,120}(run|invoke|consume).{0,100}qa.{0,80}(command|job)",
        )

        phase4 = section(implement_raw, "## Phase 4")
        self.assertIn("rd-owned ci", phase4)
        self.assertIn("ownership violation", phase4)
        self.assertRegex(
            phase4,
            r"(do not|must not|never).{0,120}(run|trigger|consume).{0,100}qa.{0,80}(command|job)",
        )
        self.assertIn("non-qa branch-required checks", phase4)
        self.assertIn("security, license, provenance, or policy", phase4)
        preflight = phase4.index("ci ownership preflight")
        self.assertLess(preflight, phase4.index("push the feature branch"))
        self.assertLess(preflight, phase4.index("open/update one pr"))
        self.assertIn("workflow triggers", phase4)
        self.assertIn("stop before the mutation", phase4)
        for trigger in (
            "initial push",
            "retry push",
            "pr open/update",
            "merge/integration push",
            "deployment",
            "workflow dispatch",
            "job rerun",
            "infrastructure retry",
        ):
            self.assertIn(trigger, phase4)
        self.assertIn("unclassified test job", phase4)
        self.assertIn("re-read the current config v1", phase4)
        self.assertIn("current remote workflow and job wiring", phase4)
        remote_loop = phase4.split("remote feedback loop", maxsplit=1)[1].split(
            "5. proceed", maxsplit=1
        )[0]
        merge_path = phase4.split("6. rerun", maxsplit=1)[1].split(
            "7. run", maxsplit=1
        )[0]
        deployment_path = phase4.split("8. obtain", maxsplit=1)[1].split(
            "9. update", maxsplit=1
        )[0]
        self.assertLess(
            remote_loop.index("rerun the ci ownership preflight"),
            remote_loop.index("push a new head"),
        )
        self.assertLess(
            remote_loop.rindex("rerun the ci ownership preflight"),
            remote_loop.index("retry unrelated"),
        )
        self.assertLess(
            merge_path.index("the ci ownership preflight"),
            merge_path.index("merge only"),
        )
        self.assertIn("rerun the ci ownership preflight", deployment_path)
        rebase_review = phase4.split("rebase or conflict resolution", maxsplit=1)[1].split(
            "2. before any push", maxsplit=1
        )[0]
        remote_review = phase4.split("remote feedback loop", maxsplit=1)[1].split(
            "5. proceed", maxsplit=1
        )[0]
        for review_path in (rebase_review, remote_review):
            self.assertIn("rd-only pre-handoff review boundary", review_path)
            self.assertRegex(
                review_path,
                r"(do not|must not|never).{0,120}(run|invoke|consume).{0,100}qa.{0,80}(command|job)",
            )

    def test_reusable_qa_handoff_template_has_required_fields(self) -> None:
        template = " ".join(
            read("skills/testing-workflow/qa-handoff-template.md").lower().split()
        )

        for marker in (
            "handoff status",
            "acceptance contract revision",
            "sc-id → ac-id",
            "full 40-character source sha",
            "deployed artifact/environment revision",
            "artifact-provenance source",
            "artifact provenance receipt",
            "fixtures/accounts",
            "known risks",
            "rd coverage summary",
            "informational only",
            "not covered by rd",
        ):
            self.assertIn(marker, template)
        self.assertIn("ready | not ready", template)

    def test_execution_ledger_is_per_scenario_exact_artifact_and_append_only(self) -> None:
        raw_ledger = read("skills/testing-workflow/execution-ledger-template.md")
        ledger = " ".join(raw_ledger.lower().split())

        for marker in (
            "qa-run-id",
            "attempt",
            "sc-id",
            "ac-id",
            "full source sha",
            "exact artifact/environment revision",
            "artifact-provenance source",
            "method/command or manual steps",
            "result",
            "evidence",
            "started at",
            "completed at",
            "previous attempt",
            "append-only",
            "resume",
            "raw attempt outcome",
            "scenario classification",
            "not run",
        ):
            self.assertIn(marker, ledger)
        self.assertIn("never overwrite", ledger)
        self.assertIn("first matching rule wins", ledger)
        for sequence in (
            "`fail → pass` → `flaky`",
            "`pass → fail` → `flaky`",
            "`fail → pass → blocked` → `blocked`",
            "`fail → pass → not run` → `not tested`",
        ):
            self.assertIn(sequence, ledger)
        attempt_header = next(
            line.lower() for line in raw_ledger.splitlines() if line.startswith("| Attempt |")
        )
        for field in (
            "sc-id",
            "ac-id",
            "full source sha",
            "exact artifact/environment revision",
            "artifact-provenance source",
            "method/command or manual steps",
            "raw attempt outcome",
            "scenario classification",
            "evidence",
        ):
            self.assertIn(field, attempt_header)

    def test_retry_green_is_flaky_and_p0_cannot_be_quarantined_to_pass(self) -> None:
        workflow_raw = read("skills/testing-workflow/SKILL.md")
        workflow = " ".join(workflow_raw.lower().split())
        stage3 = section(workflow_raw, "## Stage 3", "## Stage 4")

        for marker in (
            "retry-green",
            "flaky",
            "attempt history",
            "p0",
            "cannot be quarantined",
            "must not count as pass",
            "not ready",
        ):
            self.assertIn(marker, workflow)
        self.assertRegex(workflow, r"retry-green.{0,100}flaky")
        self.assertIn("raw attempt outcome", stage3)
        self.assertIn("scenario classification", stage3)
        self.assertIn("not run", stage3)
        self.assertIn("ordered first-match precedence", stage3)
        self.assertRegex(
            stage3,
            r"fail.{0,160}pass.{0,160}flaky",
        )
        self.assertIn("every valid handoff's qa candidate artifact", stage3)
        self.assertIn("pr smoke gate", stage3)
        self.assertIn("rd-owned", stage3)
        self.assertNotRegex(stage3, r"p0.{0,50}every pr")
        self.assertIn("every classification except pass", stage3)
        self.assertRegex(stage3, r"p0.{0,160}every classification except pass.{0,120}not ready")
        self.assertIn("qa evidence location", stage3)
        self.assertIn("still writable", stage3)

    def test_anti_fake_green_rejection_is_appended_to_the_ledger(self) -> None:
        workflow = read("skills/testing-workflow/SKILL.md")
        stage4 = section(workflow, "## Stage 4", "## Stage 5")

        for marker in (
            "append",
            "blocked",
            "every affected scenario",
            "preserve",
            "not ready",
            "repaired",
            "new attempt",
        ):
            self.assertIn(marker, stage4)

    def test_acceptance_report_keeps_plain_verdict_and_ledger_evidence(self) -> None:
        report = read("skills/testing-workflow/acceptance-report-template.md")
        normalized = " ".join(report.lower().split())

        for marker in (
            "ready to accept",
            "accept with caveats",
            "not ready",
            "not tested",
            "scenario",
            "spec criterion",
            "exact artifact/environment revision",
            "method/command or manual steps",
            "result",
            "flaky",
            "evidence",
            "ledger attempt",
            "caveat",
        ):
            self.assertIn(marker, normalized)
        report_rows = [line for line in report.splitlines() if line.startswith("| ")]
        result_cells = [row.split("|")[9].strip() for row in report_rows[1:]]
        for result in result_cells:
            self.assertRegex(result, r"^(✅ PASS|⚠️ FLAKY|❌ (FAIL|BLOCKED|NOT TESTED))$")
        self.assertNotIn("CAVEAT", result_cells)
        self.assertNotIn("⚠️ Accept with caveats", report)
        self.assertNotIn("(⚠️)", report)
        self.assertRegex(report, r"\*\*Execution ledger:\*\* \[[^\]]+\]\([^)]+\)")
        for row in report_rows[1:]:
            self.assertRegex(row, r"\|\s*\[run/attempts?\]\([^)]+\)\s*\|")

    def test_setup_config_is_versioned_and_separates_rd_from_qa(self) -> None:
        setup = read("skills/setup/SKILL.md")
        config = section(setup, "<config-template>", "</config-template>")

        for field in (
            "config version:",
            "rd unit command:",
            "rd api-contract command:",
            "qa integration command:",
            "qa p0 command:",
            "qa full-suite command:",
            "qa environment:",
            "artifact-provenance source:",
            "qa evidence location:",
            "deployment / test environment:",
            "legacy test-command migration note:",
        ):
            self.assertIn(field, config)
        self.assertRegex(config, r"config version:\*\* `1`")
        self.assertIn(
            "must agree with the qa environment and artifact-provenance source",
            config,
        )

    def test_readme_explains_config_v1_and_qa_ownership(self) -> None:
        readme = " ".join(read("README.md").lower().split())

        for marker in (
            "config v1 migration",
            "re-run",
            "rd unit/api-contract",
            "qa integration/p0/full-suite",
            "artifact provenance",
            "evidence location",
        ):
            self.assertIn(marker, readme)

    def test_legacy_config_migration_is_idempotent_and_fail_closed(self) -> None:
        setup = read("skills/setup/SKILL.md")
        migration = section(
            setup,
            "## Legacy configuration migration",
            "## Idempotent",
        )

        for marker in (
            "legacy v0",
            "exactly one `## harness-ship` block",
            "preserve",
            "not-configured",
            "manual: <steps",
            "never infer pass",
            "legacy test-command migration note",
            "second run",
            "byte-for-byte unchanged",
        ):
            self.assertIn(marker, migration)
        self.assertIn("count", migration)
        self.assertRegex(
            migration,
            r"more than one.{0,120}(stop|do not write|do not mutate)",
        )
        self.assertIn("require explicit reconciliation", migration)
        for marker in (
            "no existing block",
            "explicit `0`",
            "exactly `1`",
            "unsupported version",
            "zero mutation",
        ):
            self.assertIn(marker, migration)

    def test_dev_handoff_uses_template_and_keeps_rd_summary_informational(self) -> None:
        dev = read("skills/dev-workflow/SKILL.md")
        stage6 = section(dev, "## Stage 6 — Hand to QA")

        for marker in (
            "qa-handoff-template.md",
            "full 40-character source sha",
            "artifact-provenance source",
            "rd coverage summary",
            "informational",
            "qa does not audit",
        ):
            self.assertIn(marker, stage6)
        match = re.search(r"\[QA handoff template\]\(([^)]+)\)", dev)
        self.assertIsNotNone(match)
        referenced = (ROOT / "skills/dev-workflow" / match.group(1)).resolve()
        self.assertTrue(referenced.is_file())
        self.assertIn(ROOT.resolve(), referenced.parents)


if __name__ == "__main__":
    unittest.main()
