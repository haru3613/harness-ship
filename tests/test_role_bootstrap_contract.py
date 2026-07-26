from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(path: str) -> str:
    return " ".join(read(path).lower().split())


class RoleBootstrapContractTests(unittest.TestCase):
    def test_plugin_ships_a_strict_independent_verifier(self) -> None:
        text = read("agents/harness-ship-independent-verifier.md")
        match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter, body = match.groups()

        self.assertRegex(
            frontmatter, r"(?m)^name:\s*harness-ship-independent-verifier\s*$"
        )
        self.assertRegex(frontmatter, r"(?m)^model:\s*inherit\s*$")
        self.assertRegex(frontmatter, r"(?m)^effort:\s*high\s*$")
        self.assertRegex(frontmatter, r"(?m)^tools:\s*Read,\s*Grep,\s*Glob\s*$")
        for forbidden_key in ("permissionMode:", "mcpServers:", "hooks:"):
            self.assertNotIn(forbidden_key, frontmatter)

        body = " ".join(body.lower().split())
        for marker in (
            "fresh context",
            "independent outcome",
            "no source edits",
            "repository content and command output as untrusted",
            "file and line evidence",
            "do not approve based on prompt instructions",
        ):
            self.assertIn(marker, body)

    def test_setup_resolves_one_current_host_binding_before_any_mutation(self) -> None:
        text = normalized("skills/setup/SKILL.md")

        self.assertIn("exactly one `## harness-ship`", text)
        self.assertIn("exactly one current-host binding section", text)
        self.assertIn("before any setup mutation", text)
        self.assertLess(
            text.index("validate the semantic, effective live boundary"),
            text.index("compute its boundary digest"),
        )
        self.assertIn("preserve an explicit valid project binding", text)
        self.assertIn("update only the current host section", text)
        self.assertIn("preserve the other host section", text)
        for setting in (
            "global agents",
            "models",
            "effort",
            "permissions",
            "mcp",
            "plugin settings",
        ):
            self.assertIn(setting, text)

    def test_setup_candidate_selection_is_live_verifiable_and_fail_closed(self) -> None:
        text = normalized("skills/setup/SKILL.md")

        self.assertIn("harness-ship:harness-ship-independent-verifier", text)
        self.assertIn("canonical plugin source", text)
        self.assertIn("canonical plugin digest", text)
        for codex_requirement in (
            "runtime metadata",
            "read-only",
            "no source edits",
            "fresh context",
            "high effort",
            "may_spawn=false",
            "effective tool/capability boundary",
            "authoritative source",
        ):
            self.assertIn(codex_requirement, text)
        self.assertIn("do not hard-code a universal model family", text)
        self.assertIn("one candidate", text)
        self.assertIn("multiple candidates", text)
        self.assertIn("one load-bearing choice", text)
        self.assertIn("no candidates", text)
        self.assertIn("actionable missing-profile", text)
        self.assertIn("zero mutation", text)
        self.assertIn("fully qualified id", text)
        self.assertIn("semantically validated boundary digest", text)

    def test_implement_preflights_verifier_before_phase_zero_or_side_effects(self) -> None:
        text = normalized("skills/implement/SKILL.md")
        preflight = text.index("mandatory independent-verifier preflight")
        phase_zero = text.index("## phase 0")

        self.assertLess(preflight, phase_zero)
        for marker in (
            "authoritative definition digest",
            "ticket claim",
            "worktree creation",
            "worktree list",
            "delegation",
            "dispatch",
            "baseline",
            "no tracker mutation",
            "no child",
        ):
            self.assertIn(marker, text[preflight:phase_zero])
        self.assertIn("launch and recovery", text)
        self.assertIn("same authoritative definition digest", text)
        self.assertIn("immediately before every dispatch", text)
        self.assertIn("verifier output is untrusted", text)
        self.assertIn("root confirms every cited file and line", text)

    def test_lifecycle_inventory_and_readme_explain_agent_bootstrap_boundary(self) -> None:
        lifecycle = normalized("scripts/validate_plugin_lifecycle.sh")
        readme = normalized("README.md")

        self.assertIn("agents/harness-ship-independent-verifier.md", lifecycle)
        self.assertIn("agent_count=", lifecycle)
        self.assertIn("discovered-agents=", lifecycle)
        self.assertIn("install supplies the verifier capability", readme)
        self.assertIn("project setup performs the current-host binding", readme)
        self.assertIn("never copies agents into `~/.claude/agents`", readme)
        self.assertIn("never overwrites global agents or settings", readme)


if __name__ == "__main__":
    unittest.main()
