from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class BugWorkflowContractTests(unittest.TestCase):
    """HS-QA-BUG/acceptance-v1: SC-003 traces to AC-4 and AC-5."""

    def test_skill_and_portable_template_are_discoverable(self) -> None:
        skill = read("skills/bug-workflow/SKILL.md")
        template = read("skills/bug-workflow/bug-case-template.md")

        self.assertRegex(skill, r"(?m)^name:\s+bug-workflow$")
        self.assertIn("# bug-workflow", skill)
        self.assertIn("bug-case-template.md", skill)
        self.assertIn("| `bug-workflow` |", read("README.md"))
        self.assertIn("BUG-ID", template)

        for path in (
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
        ):
            payload = json.loads(read(path))
            keywords = (
                payload["plugins"][0]["keywords"]
                if path.endswith("marketplace.json")
                else payload["keywords"]
            )
            self.assertIn("bug-workflow", keywords)

    def test_one_stable_bug_id_and_append_only_history(self) -> None:
        text = " ".join(
            (
                read("skills/bug-workflow/SKILL.md")
                + read("skills/bug-workflow/bug-case-template.md")
            )
            .lower()
            .split()
        )

        for marker in (
            "stable bug-id",
            "assign once",
            "append-only",
            "never replace",
            "handoff",
            "retest",
        ):
            self.assertIn(marker, text)

    def test_phase_classification_and_disposition_are_separate(self) -> None:
        template = read("skills/bug-workflow/bug-case-template.md")
        headers = [
            line.lower() for line in template.splitlines() if line.startswith("- **")
        ]

        self.assertTrue(any("phase:" in line for line in headers))
        self.assertTrue(any("classification:" in line for line in headers))
        self.assertTrue(any("disposition:" in line for line in headers))

    def test_six_classifications_have_distinct_routes(self) -> None:
        skill = read("skills/bug-workflow/SKILL.md").lower()
        routes = {
            "product-defect": ("rd diagnosis", "`diagnose`"),
            "test-defect": ("qa maintenance",),
            "environment-defect": ("configured environment owner",),
            "spec-ambiguity": ("`acceptance-design`", "new contract revision"),
            "duplicate": ("canonical bug-id",),
            "known-limitation": ("scope", "user impact", "human disposition"),
        }

        for classification, markers in routes.items():
            self.assertIn(classification, skill)
            route = skill.split(f"- `{classification}`", maxsplit=1)[1].split(
                "\n-", maxsplit=1
            )[0]
            route = " ".join(route.split())
            for marker in markers:
                self.assertIn(marker, route)

        self.assertEqual(skill.count("→ rd diagnosis"), 1)

    def test_qa_diagnosis_requires_a_classified_bug_and_stops_before_repair(self) -> None:
        diagnose = " ".join(read("skills/diagnose/SKILL.md").lower().split())

        for marker in (
            "stable bug-id",
            "classification is `product-defect`",
            "otherwise run `bug-workflow` and stop",
            "diagnosis-only",
            "then stop without changing product code",
            "downstream repair workflow explicitly authorizes",
        ):
            self.assertIn(marker, diagnose)

    def test_bug_case_preserves_traceability_provenance_and_observation(self) -> None:
        template = " ".join(
            read("skills/bug-workflow/bug-case-template.md").lower().split()
        )

        for marker in (
            "acceptance contract revision",
            "sc-id",
            "ac-id",
            "originating ticket",
            "full source sha",
            "exact tested artifact/environment revision",
            "expected",
            "actual",
            "reproducibility",
            "evidence",
        ):
            self.assertIn(marker, template)

    def test_blocked_and_needs_evidence_are_resumable_not_closure(self) -> None:
        skill = " ".join(read("skills/bug-workflow/SKILL.md").lower().split())

        for state in ("blocked", "needs-evidence"):
            self.assertIn(state, skill)
        self.assertRegex(skill, r"(blocked|needs-evidence).{0,160}resum")
        self.assertRegex(skill, r"(blocked|needs-evidence).{0,200}(not|never).{0,40}clos")

    def test_tracker_unavailable_emits_portable_case_without_fake_publication(self) -> None:
        skill = " ".join(read("skills/bug-workflow/SKILL.md").lower().split())

        for marker in (
            "tracker adapter",
            "unavailable",
            "portable bug case",
            "publication did not occur",
            "do not invent",
        ):
            self.assertIn(marker, skill)

    def test_testing_workflow_routes_non_pass_to_bug_case_first(self) -> None:
        workflow = read("skills/testing-workflow/SKILL.md")
        stage6 = " ".join(workflow.split("## Stage 6 — Bug loopback", maxsplit=1)[1].lower().split())

        self.assertIn("`bug-workflow`", stage6)
        self.assertIn("bug-id", stage6)
        self.assertIn("non-pass", stage6)
        self.assertRegex(stage6, r"product-defect.{0,120}`diagnose`")
        self.assertNotRegex(stage6, r"(any|every) (confirmed )?failure.{0,80}`diagnose`")


if __name__ == "__main__":
    unittest.main()
