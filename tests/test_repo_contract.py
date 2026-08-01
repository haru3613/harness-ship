"""Structural checks that survive rewording.

These replace the former *_contract.py suites, which asserted that arbitrary
English phrases appeared in instruction prose. Only load-bearing runtime
guarantees are pinned below.

What is a contract: the verifier agent's tool boundary (enforced by the host
permission layer, not by prose), skill discoverability, and link integrity.
"""

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
VERIFIER = ROOT / "agents" / "harness-ship-independent-verifier.md"

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)#]+\.md)[^)]*\)")


def frontmatter(path: Path) -> str:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    assert match, f"{path} has no frontmatter"
    return match.group(1)


class VerifierBoundaryTests(unittest.TestCase):
    """The one boundary the host enforces rather than the agent honouring."""

    def test_verifier_cannot_edit(self) -> None:
        meta = json.loads(frontmatter(VERIFIER))

        self.assertEqual(meta["tools"], ["Read", "Grep", "Glob"])
        self.assertEqual(meta["model"], "inherit")
        self.assertEqual(meta["effort"], "high")


class SkillStructureTests(unittest.TestCase):
    def test_every_skill_is_discoverable_under_its_own_name(self) -> None:
        for skill in sorted(SKILLS.iterdir()):
            with self.subTest(skill=skill.name):
                name = re.search(r"(?m)^name:\s*(\S+)\s*$", frontmatter(skill / "SKILL.md"))
                self.assertIsNotNone(name, "SKILL.md frontmatter has no name")
                self.assertEqual(name.group(1), skill.name)

    def test_development_helpers_are_user_invoked_in_both_harnesses(self) -> None:
        helpers = {"clarify", "spike", "spec", "tickets", "implement", "tdd", "review"}
        claude = {
            skill.name
            for skill in SKILLS.iterdir()
            if skill.is_dir()
            and re.search(r"(?m)^disable-model-invocation:\s*true\s*$", frontmatter(skill / "SKILL.md"))
        }
        # Literal block, so the key must sit under `policy:` at the right indent —
        # misfiled under `interface:` it would be ignored by Codex, and must fail here.
        policy_block = "policy:\n  allow_implicit_invocation: false\n"
        codex = {
            skill.name
            for skill in SKILLS.iterdir()
            if (skill / "agents" / "openai.yaml").is_file()
            and policy_block in (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
        }
        # Equality, not subset: a helper losing the key and a testing skill gaining it both fail.
        self.assertEqual(claude, helpers, "Claude Code user-invoked set drifted")
        self.assertEqual(codex, helpers, "Codex user-invoked set drifted from Claude Code")

    def test_every_markdown_link_resolves(self) -> None:
        for source in sorted(SKILLS.rglob("*.md")):
            for target in MD_LINK.findall(source.read_text(encoding="utf-8")):
                with self.subTest(source=str(source.relative_to(ROOT)), target=target):
                    self.assertTrue((source.parent / target).resolve().is_file())

    def test_test_confidence_surface_replaces_dev_orchestration(self) -> None:
        for removed in ("dev-workflow", "acceptance-design"):
            self.assertFalse((SKILLS / removed).exists())
        for current in (
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
        self.assertFalse((SKILLS / "implement" / "defect-repair.md").exists())
        self.assertFalse(
            (SKILLS / "implement" / "defect-repair-receipt-template.md").exists()
        )


class ReviewerRoutingTests(unittest.TestCase):
    def test_reviewer_routing_happens_at_invocation(self) -> None:
        setup = (SKILLS / "setup" / "SKILL.md").read_text(encoding="utf-8")
        implement = (SKILLS / "implement" / "SKILL.md").read_text(encoding="utf-8")
        review = (SKILLS / "review" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Invocation-time reviewer routing", implement)
        self.assertIn("## Dispatch reviewers at invocation", review)
        self.assertNotIn("role_binding_contract.py preflight", setup)
        self.assertNotIn("## Mandatory independent-verifier preflight", implement)

        self.assertIn("## Role-profile gate", implement)
        non_review_routing = implement.split("## Role-profile gate", 1)[1].split(
            "\n## ", 1
        )[0]
        for guarantee in (
            "planning, implementation, and security work",
            "pre-defined role profile",
            "Do not substitute an undefined",
        ):
            self.assertIn(guarantee, non_review_routing)

        implement_routing = implement.split(
            "## Invocation-time reviewer routing", 1
        )[1].split("\n## ", 1)[0]
        for guarantee in (
            "`generic`, `default`, `worker`",
            "`claude-code`",
            "role_binding_contract.py preflight",
            "`harness-ship:harness-ship-independent-verifier`",
            "run identity",
            "`independence: not established`",
            "root performs",
        ):
            self.assertIn(guarantee, implement_routing)

        review_routing = review.split(
            "## Dispatch reviewers at invocation", 1
        )[1].split("\n## ", 1)[0]
        for guarantee in (
            "`generic`, `default`, `worker`",
            "`claude-code`",
            "role_binding_contract.py preflight",
            "`harness-ship:harness-ship-independent-verifier`",
            "run identity",
            "`independence: not established`",
            "`git rev-parse HEAD`",
            "`git rev-parse HEAD^{tree}`",
            "`git status --porcelain`",
            "activity trace",
            "mutate external state",
            "spawn children",
        ):
            self.assertIn(guarantee, review_routing)


if __name__ == "__main__":
    unittest.main()
