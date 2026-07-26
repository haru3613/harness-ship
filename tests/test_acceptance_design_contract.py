from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class AcceptanceDesignContractTests(unittest.TestCase):
    """HS-QA-BUG/acceptance-v1: SC-001 traces to AC-1 and AC-7."""

    def test_acceptance_design_is_a_discoverable_skill(self) -> None:
        text = read("skills/acceptance-design/SKILL.md")

        self.assertRegex(text, r"(?m)^name:\s+acceptance-design$")
        self.assertIn("# acceptance-design", text)

    def test_scenario_contract_is_versioned_traceable_and_qa_executable(self) -> None:
        text = " ".join(read("skills/acceptance-design/SKILL.md").split())

        for marker in (
            "<spec-id>/acceptance-vN",
            "stable SC-ID",
            "stable AC-ID",
            "SC-ID → AC-ID",
            "P0",
            "P1",
            "surface",
            "Given",
            "When",
            "Then",
            "negative assertion",
            "QA-executable seam",
            "fixture/data needs",
            "QA assurance profile",
        ):
            self.assertIn(marker, text)

    def test_acceptance_design_stops_before_implementation_or_qa_execution(self) -> None:
        text = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())

        self.assertIn("design only", text)
        self.assertIn("stop", text)
        self.assertRegex(text, r"do not (begin|start|run) qa execution")
        self.assertIn("do not implement", text)

    def test_dev_workflow_invokes_acceptance_design_at_the_acceptance_gate(self) -> None:
        text = read("skills/dev-workflow/SKILL.md")
        stage = text.split("## Stage 3 — Acceptance contract", maxsplit=1)[1].split(
            "## Stage 4 — Tickets", maxsplit=1
        )[0]

        self.assertRegex(stage, r"Run \*\*`acceptance-design`\*\*")
        self.assertNotIn("Stage 1 of `testing-workflow`", stage)
        self.assertIn("<spec-id>/acceptance-vN", stage)

    def test_spec_routes_scenario_authoring_to_acceptance_design(self) -> None:
        text = read("skills/spec/SKILL.md")
        normalized = " ".join(text.lower().split())

        self.assertIn("`acceptance-design` turns these criteria into", normalized)
        self.assertIn("acceptance-scenario design is `acceptance-design`'s job", normalized)
        self.assertNotRegex(
            normalized,
            r"testing-workflow.{0,80}(acceptance contract|scenario design|scenario authoring)",
        )

    def test_testing_workflow_executes_approved_scenarios_but_does_not_author_them(self) -> None:
        text = read("skills/testing-workflow/SKILL.md")
        normalized = " ".join(text.lower().split())

        self.assertNotIn("## Stage 1 — Journeys → scenarios", text)
        self.assertNotRegex(normalized, r"testing-workflow.{0,80}(design|author).{0,80}scenario")
        self.assertIn("approved acceptance contract", normalized)
        self.assertIn("do not redesign", normalized)
        self.assertIn("integration + e2e", normalized)

    def test_v06_preimplementation_calls_redirect_without_starting_qa(self) -> None:
        text = " ".join(read("skills/testing-workflow/SKILL.md").split())
        compatibility = text.split("v0.6 compatibility", maxsplit=1)[1].split(
            "## Stage 2", maxsplit=1
        )[0]

        self.assertIn("pre-implementation", compatibility)
        self.assertIn("`acceptance-design`", compatibility)
        self.assertRegex(compatibility.lower(), r"do not (begin|start|run) qa execution")
        self.assertIn("one minor release", compatibility.lower())

    def test_existing_execution_stage_ids_and_references_remain_stable(self) -> None:
        text = read("skills/testing-workflow/SKILL.md")

        for heading in (
            "## Stage 2 — Route approved scenarios by ownership",
            "## Stage 3 — Execute E2E",
            "## Stage 4 — Anti-fake-green gate",
            "## Stage 5 — Acceptance report",
            "## Stage 6 — Bug loopback",
        ):
            self.assertIn(heading, text)
        self.assertIn("acceptance-report-template.md", text)

    def test_readme_and_plugin_metadata_advertise_acceptance_design_v06(self) -> None:
        readme = read("README.md")

        self.assertRegex(readme, r"(?m)^\| `acceptance-design` \|")
        self.assertIn("eight self-contained blocks", readme)
        self.assertIn("v0.6.0 migration", readme)

        for manifest in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ):
            payload = json.loads(read(manifest))
            self.assertEqual(payload["version"], "0.6.0")
            self.assertIn("acceptance-design", payload["keywords"])

        codex = json.loads(read(".codex-plugin/plugin.json"))
        self.assertTrue(
            any("acceptance" in prompt.lower() for prompt in codex["interface"]["defaultPrompt"])
        )

        marketplace = json.loads(read(".claude-plugin/marketplace.json"))["plugins"][0]
        self.assertIn("eight self-contained blocks", marketplace["description"])
        self.assertIn("acceptance-design", marketplace["keywords"])


if __name__ == "__main__":
    unittest.main()
