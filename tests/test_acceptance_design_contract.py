from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class AcceptanceDesignContractTests(unittest.TestCase):
    """HS-QA-BUG/acceptance-v1: SC-001 traces to AC-1 and AC-7."""

    def assert_compatibility_policy(
        self, version: str, testing_workflow: str, readme: str
    ) -> None:
        major, minor, _patch = (int(part) for part in version.split("."))
        normalized = " ".join(testing_workflow.split())

        if (major, minor) >= (0, 7):
            for marker in (
                "v0.6 compatibility",
                "implementation already exists",
                "no approved acceptance contract",
                "one minor release",
            ):
                self.assertNotIn(marker, normalized)
            self.assertNotIn("**v0.6.0 migration:**", readme)
            for command in (
                "$harness-ship:acceptance-design",
                "$harness-ship:testing-workflow",
                "/harness-ship:acceptance-design",
                "/harness-ship:testing-workflow",
            ):
                self.assertNotIn(command, readme)
            return

        self.assertEqual((major, minor), (0, 6))
        compatibility = normalized.split("v0.6 compatibility", maxsplit=1)[1].split(
            "## Stage 2", maxsplit=1
        )[0]
        self.assertIn("pre-implementation", compatibility)
        self.assertIn("`acceptance-design`", compatibility)
        self.assertNotIn("/testing-workflow", compatibility)
        self.assertRegex(compatibility.lower(), r"do not (begin|start|run) qa execution")
        self.assertIn("one minor release", compatibility.lower())
        self.assertIn("implementation already exists", compatibility)
        self.assertIn("no approved acceptance contract", compatibility)
        self.assertIn("original or current stable spec", compatibility)
        self.assertIn("never infer expected behaviour from code", compatibility.lower())
        self.assertIn("stop", compatibility.lower())
        self.assertIn("**v0.6.0 migration:**", readme)
        for command in (
            "$harness-ship:acceptance-design",
            "$harness-ship:testing-workflow",
            "/harness-ship:acceptance-design",
            "/harness-ship:testing-workflow",
        ):
            self.assertIn(command, readme)

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

    def test_acceptance_design_uses_the_joint_acceptance_gate(self) -> None:
        skill = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        dev = " ".join(read("skills/dev-workflow/SKILL.md").lower().split())
        readme = " ".join(read("README.md").lower().split())
        codex = json.loads(read(".codex-plugin/plugin.json"))

        self.assertIn("current stable spec", skill)
        self.assertIn("do not require a separate spec-approval gate", skill)
        self.assertIn("presents the spec criteria and scenario set together", skill)
        self.assertIn("for explicit user approval", skill)
        self.assertIn("spec criteria and scenarios describe the right behaviour", dev)
        self.assertIn("current stable spec", readme)
        self.assertTrue(
            any("current spec" in prompt.lower() for prompt in codex["interface"]["defaultPrompt"])
        )

    def test_only_the_user_can_approve_the_acceptance_contract(self) -> None:
        skill = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        dev = " ".join(read("skills/dev-workflow/SKILL.md").lower().split())

        self.assertIn("only the user may approve", skill)
        self.assertIn("unapproved draft", skill)
        self.assertIn("never self-approve", skill)
        self.assertIn("user confirms", dev)

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

    def test_versioned_compatibility_redirect_and_expiry(self) -> None:
        text = read("skills/testing-workflow/SKILL.md")
        readme = read("README.md")
        version = json.loads(read(".codex-plugin/plugin.json"))["version"]

        self.assert_compatibility_policy(version, text, readme)

    def test_v07_policy_rejects_retained_alias_and_accepts_complete_removal(self) -> None:
        current_workflow = read("skills/testing-workflow/SKILL.md")
        current_readme = read("README.md")

        with self.assertRaises(AssertionError):
            self.assert_compatibility_policy("0.7.0", current_workflow, current_readme)

        future_workflow = re.sub(
            r"## v0\.6 compatibility redirect.*?(?=## Stage 2)",
            "",
            current_workflow,
            flags=re.DOTALL,
        )
        future_readme = re.sub(
            r"\n\*\*v0\.6\.0 migration:\*\*.*?(?=\n\n)",
            "",
            current_readme,
            flags=re.DOTALL,
        )
        self.assert_compatibility_policy("0.7.0", future_workflow, future_readme)

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

    def test_readme_and_plugin_metadata_advertise_acceptance_design(self) -> None:
        readme = read("README.md")

        self.assertRegex(readme, r"(?m)^\| `acceptance-design` \|")
        self.assertIn("eight self-contained blocks", readme)

        versions = set()
        for manifest in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ):
            payload = json.loads(read(manifest))
            versions.add(payload["version"])
            self.assertIn("acceptance-design", payload["keywords"])
        self.assertEqual(len(versions), 1)
        version = versions.pop()
        self.assertGreaterEqual(tuple(int(part) for part in version.split(".")), (0, 6, 0))

        codex = json.loads(read(".codex-plugin/plugin.json"))
        self.assertTrue(
            any("acceptance" in prompt.lower() for prompt in codex["interface"]["defaultPrompt"])
        )

        marketplace = json.loads(read(".claude-plugin/marketplace.json"))["plugins"][0]
        self.assertIn("eight self-contained blocks", marketplace["description"])
        self.assertIn("acceptance-design", marketplace["keywords"])


if __name__ == "__main__":
    unittest.main()
