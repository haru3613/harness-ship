from pathlib import Path
import json
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
        fields = json.loads(frontmatter)

        self.assertEqual(
            set(fields),
            {"name", "description", "model", "effort", "tools"},
        )
        self.assertEqual(fields["name"], "harness-ship-independent-verifier")
        self.assertEqual(
            fields["description"],
            "Used after implementation for fresh independent outcome verification.",
        )
        self.assertEqual(fields["model"], "inherit")
        self.assertEqual(fields["effort"], "high")
        self.assertEqual(
            fields["tools"],
            ["Read", "Grep", "Glob"],
        )

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
        self.assertIn("preserve an explicit valid project binding", text)
        self.assertIn("update only the current host section", text)
        self.assertIn("preserve the other host section", text)
        self.assertIn("role_binding_contract.py resolve", text)
        self.assertIn("stop with zero mutation", text)
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
        self.assertIn("canonical plugin provenance", text)
        self.assertIn("authoritative live host profiles", text)
        self.assertIn("do not hard-code a universal model family", text)
        self.assertIn("`preserved`", text)
        self.assertIn("`selected`", text)
        self.assertIn("`ambiguous`", text)
        self.assertIn("`missing`", text)
        self.assertIn("one load-bearing candidate choice", text)
        self.assertIn("actionable missing-profile", text)
        self.assertIn("zero mutation", text)

    def test_binding_schema_and_digest_are_canonical_for_both_hosts(self) -> None:
        setup_raw = read("skills/setup/SKILL.md")
        setup = normalized("skills/setup/SKILL.md")
        implement = normalized("skills/implement/SKILL.md")
        expected_header = (
            "| Work nature | Host / profile ID | Definition source | Definition digest | "
            "Mode / sandbox | Model | Effort | Write scope | Effective tools/capabilities | "
            "MCP/plugins | Fresh context | May spawn | Boundary digest |"
        )

        self.assertEqual(setup_raw.count(expected_header), 2)
        self.assertIn("executable reference", setup)
        self.assertIn("restricted rfc 8785-compatible", setup)
        self.assertIn("role_binding_contract.py resolve", setup)
        self.assertIn("role_binding_contract.py preflight", implement)
        self.assertIn("post-launch reconciliation", implement)

    def test_implement_preflights_verifier_before_phase_zero_or_side_effects(self) -> None:
        text = normalized("skills/implement/SKILL.md")
        preflight = text.index("mandatory independent-verifier preflight")
        phase_zero = text.index("## phase 0")

        self.assertLess(preflight, phase_zero)
        for marker in (
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
        self.assertIn("missing host launch metadata", text)
        self.assertIn("immediately before every dispatch", text)
        self.assertIn("verifier output is untrusted", text)
        self.assertIn("root confirms every cited file and line", text)

    def test_lifecycle_semantically_validates_agent_inventory(self) -> None:
        lifecycle = normalized("scripts/validate_plugin_lifecycle.sh")
        readme = normalized("README.md")

        self.assertIn("agents/harness-ship-independent-verifier.md", lifecycle)
        self.assertIn("scripts/role_binding_contract.py", lifecycle)
        self.assertIn("validate-agent", lifecycle)
        self.assertIn("self-test", lifecycle)
        self.assertIn("command -v claude", lifecycle)
        self.assertIn(r"agents \(1\)", lifecycle)
        self.assertIn("agent_count=", lifecycle)
        self.assertIn("discovered-agents=", lifecycle)
        self.assertIn("install supplies the verifier capability", readme)
        self.assertIn("project setup performs the current-host binding", readme)
        self.assertIn("never copies agents into `~/.claude/agents`", readme)
        self.assertIn("never overwrites global agents or settings", readme)

    def test_v062_requires_one_digest_migration_and_describes_host_supply(self) -> None:
        readme = normalized("README.md")
        versions = {
            json.loads(read(path))["version"]
            for path in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json")
        }

        self.assertEqual(versions, {"0.6.2"})
        self.assertEqual(readme.count("**v0.6.2 migration:**"), 2)
        self.assertIn("every config v1 project must run", readme)
        self.assertIn("codex installation supplies skills only", readme)
        self.assertIn("it does not supply an independent verifier", readme)
        self.assertIn("claude plugin agent", readme)


if __name__ == "__main__":
    unittest.main()
