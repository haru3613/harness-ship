from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class ImplementSkillContractTests(unittest.TestCase):
    def test_implement_is_a_discoverable_skill(self) -> None:
        text = read("skills/implement/SKILL.md")

        self.assertRegex(text, r"(?m)^name:\s+implement$")
        self.assertIn("# implement", text)

    def test_root_owns_orchestration_and_only_predefined_profiles_are_dispatched(self) -> None:
        text = read("skills/implement/SKILL.md").lower()

        for responsibility in ("planning", "delegation", "integration", "final decision"):
            self.assertIn(responsibility, text)
        self.assertRegex(text, r"pre[- ]defined role profile")
        for property_name in ("mode", "model", "effort"):
            self.assertIn(property_name, text)
        self.assertIn("must not spawn", text)
        self.assertIn("mcp", text)
        self.assertNotRegex(text, r"gpt-\d")

    def test_dispatch_contract_is_bounded_and_writer_safe(self) -> None:
        text = read("skills/implement/SKILL.md").lower()

        for field in (
            "bounded deliverable",
            "allowed files",
            "exact worktree path",
            "working directory",
            "constraints",
            "verification",
        ):
            self.assertIn(field, text)
        self.assertIn("one writer", text)
        self.assertIn("overlapping", text)
        self.assertIn("serialize all write-capable", text)

    def test_implementation_closes_the_delivery_loop(self) -> None:
        text = read("skills/implement/SKILL.md").lower()

        for marker in (
            "fixed point",
            "baseline",
            "red",
            "green",
            "typecheck",
            "full configured suite",
            "review",
            "exact head sha",
            "recompute the fixed point",
            "tracker",
            "cleanup",
            "implementation receipt",
            "deployment receipt",
        ):
            self.assertIn(marker, text)

    def test_setup_records_runtime_role_profiles_without_owning_them(self) -> None:
        text = read("skills/setup/SKILL.md").lower()

        self.assertIn("agent role profiles", text)
        self.assertIn("host", text)
        self.assertIn("mode", text)
        self.assertIn("effort", text)
        self.assertRegex(text, r"do not (create|override)")
        self.assertIn("definition source", text)
        self.assertIn("may spawn", text)
        self.assertIn("unsupported", text)
        self.assertIn("ready criteria", text)
        self.assertIn("claim transition", text)
        self.assertIn("deployment / test environment", text)
        self.assertNotIn("<profile | missing>", text)

    def test_dev_workflow_delegates_stage_five_to_implement(self) -> None:
        text = read("skills/dev-workflow/SKILL.md")
        stage = text.split("## Stage 5 — Implement", maxsplit=1)[1].split(
            "## Stage 6 — Hand to QA", maxsplit=1
        )[0]

        self.assertRegex(stage, r"Run \*\*`implement`\*\*")
        self.assertNotIn("ship-loop", stage)

    def test_review_pins_a_fixed_point_and_reviews_committed_work(self) -> None:
        text = read("skills/review/SKILL.md").lower()

        self.assertIn("fixed point", text)
        self.assertIn("merge-base", text)
        self.assertRegex(text, r"fixed[- ]point\.\.\.head")
        self.assertIn("originating", text)
        self.assertIn("commit list", text)
        self.assertIn("two fresh child runs", text)
        self.assertIn("blocked", text)

    def test_readme_and_manifests_advertise_the_new_minor_version(self) -> None:
        readme = read("README.md")
        self.assertRegex(readme, r"(?m)^\| \*\*`implement`\*\* \|")

        for manifest in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ):
            payload = json.loads(read(manifest))
            self.assertEqual(payload["version"], "0.5.0")

        marketplace = json.loads(read(".claude-plugin/marketplace.json"))
        listing = marketplace["plugins"][0]
        self.assertIn("Three orchestration workflows", listing["description"])
        self.assertIn("implement", listing["keywords"])

    def test_every_skill_has_matching_frontmatter_name(self) -> None:
        skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skill_files), 11)

        for skill_file in skill_files:
            match = re.search(r"(?m)^name:\s+([a-z0-9-]+)$", skill_file.read_text())
            self.assertIsNotNone(match, skill_file)
            self.assertEqual(match.group(1), skill_file.parent.name)

    def test_contract_suite_is_wired_into_ci(self) -> None:
        workflow = read(".github/workflows/ci.yml")

        self.assertIn("python3 -m unittest discover -s tests -v", workflow)
        self.assertIn("jq empty", workflow)


if __name__ == "__main__":
    unittest.main()
