"""Structural checks that survive rewording.

These replace the former *_contract.py suites, which asserted that arbitrary
English phrases appeared in instruction prose. Only load-bearing runtime
guarantees are pinned below.

What is a contract: skill discoverability and link integrity.
"""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)#]+\.md)[^)]*\)")


def frontmatter(path: Path) -> str:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    assert match, f"{path} has no frontmatter"
    return match.group(1)

class SkillStructureTests(unittest.TestCase):
    def test_every_skill_is_discoverable_under_its_own_name(self) -> None:
        for skill in sorted(s for s in SKILLS.iterdir() if s.is_dir()):
            with self.subTest(skill=skill.name):
                name = re.search(r"(?m)^name:\s*(\S+)\s*$", frontmatter(skill / "SKILL.md"))
                self.assertIsNotNone(name, "SKILL.md frontmatter has no name")
                self.assertEqual(name.group(1), skill.name)

    def test_no_development_helpers_remain(self) -> None:
        helpers = {"clarify", "spike", "spec", "tickets", "implement", "tdd", "review"}
        present = {skill.name for skill in SKILLS.iterdir() if skill.is_dir()}
        self.assertEqual(helpers & present, set(), "a development helper skill reappeared")

        claude = {
            skill.name
            for skill in SKILLS.iterdir()
            if skill.is_dir()
            and re.search(
                r"(?m)^disable-model-invocation:\s*true\s*$",
                frontmatter(skill / "SKILL.md"),
            )
        }
        policy_block = "policy:\n  allow_implicit_invocation: false\n"
        codex = {
            skill.name
            for skill in SKILLS.iterdir()
            if (skill / "agents" / "openai.yaml").is_file()
            and policy_block in (skill / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            )
        }
        self.assertEqual(claude, set(), "a remaining skill is user-invoked only")
        self.assertEqual(codex, set(), "a remaining skill carries a Codex helper policy")

    def test_every_markdown_link_resolves(self) -> None:
        for source in sorted(SKILLS.rglob("*.md")):
            for target in MD_LINK.findall(source.read_text(encoding="utf-8")):
                with self.subTest(source=str(source.relative_to(ROOT)), target=target):
                    self.assertTrue((source.parent / target).resolve().is_file())

    def test_record_paths_agree_across_every_skill(self) -> None:
        """One skill writing a record another cannot find is a silent failure.

        Nothing at runtime resolves these strings, so a typo or an invented
        variant costs nothing until `release-gate` reports NO-GO because it
        looked in the wrong place. Pin the vocabulary instead.
        """
        canonical = {
            ".harness-ship/",
            ".harness-ship/quality-report.md",
            ".harness-ship/test-contract.md",
            ".harness-ship/test-contract.draft.md",
            ".harness-ship/bugs/",
            ".harness-ship/bugs/<BUG-ID>.md",
            ".harness-ship/candidates/",
            ".harness-ship/candidates/<short-sha>/",
            ".harness-ship/candidates/<short-sha>/handoff.md",
            ".harness-ship/candidates/<short-sha>/ledger.md",
            ".harness-ship/candidates/<short-sha>/report.md",
            ".harness-ship/watch/",
            ".harness-ship/watch/detect.py",
            ".harness-ship/watch/RULES.md",
        }
        # README and the upgrade guide cite these paths too. Their tree diagrams
        # list bare filenames inside fenced blocks and are not covered here —
        # what is pinned is every backticked path an agent is told to act on.
        sources = [*SKILLS.rglob("*.md"), ROOT / "README.md", ROOT / "docs" / "upgrade-guide.md"]
        # Only inside backticks: the tree in test-plan's table and any prose that
        # names a path. A bare mention in a sentence is not a path reference.
        cited = {
            path
            for source in sources
            for path in re.findall(
                r"`(\.harness-ship[^`]*)`", source.read_text(encoding="utf-8")
            )
        }
        self.assertTrue(cited, "no skill names a record path")
        self.assertEqual(
            cited - canonical, set(), "skill cites a record path outside the layout"
        )

        # The writers must actually be present; a layout nothing writes is dead.
        for skill, path in (
            ("advise", ".harness-ship/quality-report.md"),
            ("test-plan", ".harness-ship/test-contract.md"),
            ("release-gate", ".harness-ship/test-contract.md"),
            ("bug-workflow", ".harness-ship/bugs/<BUG-ID>.md"),
            ("diagnose", ".harness-ship/bugs/<BUG-ID>.md"),
            ("hs-setup", ".harness-ship/watch/detect.py"),
        ):
            with self.subTest(skill=skill):
                text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"`{path}`", text)

    def test_test_confidence_surface_replaces_dev_orchestration(self) -> None:
        for removed in (
            "dev-workflow",
            "acceptance-design",
            "clarify",
            "spike",
            "spec",
            "tickets",
            "implement",
            "tdd",
            "review",
        ):
            self.assertFalse((SKILLS / removed).exists())
        self.assertFalse((SKILLS / "setup").exists())
        for current in (
            "hs-setup",
            "advise",
            "test-plan",
            "exploratory-testing",
            "testing-workflow",
            "release-gate",
        ):
            self.assertTrue((SKILLS / current / "SKILL.md").is_file())

        active_skill_text = "\n".join(
            path.read_text(encoding="utf-8") for path in SKILLS.rglob("*.md")
        )
        self.assertNotIn("`dev-workflow`", active_skill_text)
        self.assertNotIn("`acceptance-design`", active_skill_text)
        self.assertTrue((SKILLS / "exploratory-testing" / "tests.md").is_file())
        self.assertTrue((SKILLS / "exploratory-testing" / "mocking.md").is_file())

    def test_testing_workflow_projects_one_human_candidate_thread(self) -> None:
        skill = (SKILLS / "testing-workflow" / "SKILL.md").read_text(encoding="utf-8")
        handoff = (
            SKILLS / "testing-workflow" / "candidate-handoff-template.md"
        ).read_text(encoding="utf-8")
        thread = (
            SKILLS / "testing-workflow" / "human-thread-template.md"
        ).read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("[human-thread-template.md](human-thread-template.md)", skill)
        self.assertIn("**Review target:**", handoff)
        self.assertIn("**User-visible change:**", handoff)
        self.assertEqual(
            thread.count("<!-- harness-ship:testing:<candidate-key> -->"), 1
        )
        self.assertLess(
            thread.index("**<Ready for testing | Ready for release gate | Not ready>**"),
            thread.index("> Human-readable projection"),
        )
        for heading in (
            "## QA handoff",
            "### What changed",
            "### Acceptance criteria to verify",
            "### How to reach it",
            "### Known risks",
            "### Already covered",
            "### Not tested yet",
            "## Test result",
            "### User journeys",
            "### Coverage and gaps",
            "### Next action",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, thread)
        for result in ("PASS", "FAIL", "FLAKY", "BLOCKED", "NOT TESTED"):
            with self.subTest(result=result):
                self.assertIn(result, thread)
        for private in ("secrets", "credentials", "raw tokens", "fixture PII", "full logs"):
            with self.subTest(private=private):
                self.assertIn(private, thread)

        self.assertIn("current authenticated identity", skill)
        self.assertIn("code-review/PR host or issue\ntracker", skill)
        self.assertIn("More than one matching comment", skill)
        self.assertIn("does not change the handoff status or test result", skill)
        self.assertIn("only source of truth", thread)
        self.assertIn("QA handoff → Test result", readme)

    def test_setup_skill_id_is_hs_setup(self) -> None:
        skill = (SKILLS / "hs-setup" / "SKILL.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertRegex(skill, r"(?m)^name:\s*hs-setup\s*$")
        self.assertNotIn('"/setup"', skill)
        self.assertNotIn("`/setup`", skill)
        self.assertIn("/harness-ship:hs-setup", readme)
        self.assertIn("$harness-ship:hs-setup", readme)
        self.assertNotIn("/harness-ship:setup\n", readme)
        self.assertNotIn("$harness-ship:setup\n", readme)

if __name__ == "__main__":
    unittest.main()
