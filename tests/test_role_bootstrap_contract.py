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
        self.assertIn("role_binding_contract.py reconcile-config", text)
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
        for marker in (
            "unsafe-verifier-boundary",
            "observed",
            "required",
            "remediation",
            "do not collapse",
        ):
            self.assertIn(marker, text)

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
        self.assertIn("typed json object", setup)
        self.assertIn("`declared`", setup)
        self.assertIn("`effective`", setup)
        self.assertIn("role_binding_contract.py reconcile-config", setup)
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
        for marker in (
            "unsafe-verifier-boundary",
            "observed",
            "required",
            "remediation",
            "mutation=false",
        ):
            self.assertIn(marker, text[preflight:phase_zero])

    def test_lifecycle_semantically_validates_agent_inventory(self) -> None:
        lifecycle = normalized("scripts/validate_plugin_lifecycle.sh")
        release_contract = normalized("scripts/check_release_contract.py")
        workflow = normalized(".github/workflows/ci.yml")
        readme = normalized("README.md")

        self.assertIn("agents/harness-ship-independent-verifier.md", lifecycle)
        self.assertIn("scripts/role_binding_contract.py", lifecycle)
        self.assertIn("scripts/check_release_contract.py", lifecycle)
        self.assertIn("validate_plugin_lifecycle.sh", workflow)
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
        for protected in (
            ".github/workflows/ci.yml",
            "agents/harness-ship-independent-verifier.md",
            "scripts/check_release_contract.py",
            "scripts/role_binding_contract.py",
            "scripts/validate_plugin_lifecycle.sh",
            "skills/implement/skill.md",
            "skills/setup/skill.md",
        ):
            self.assertIn(protected, release_contract)
        self.assertIn("not a tamper-proof", release_contract)

    def test_v064_requires_actionable_reconciliation_and_retains_v063_history(self) -> None:
        readme = normalized("README.md")
        upgrade = normalized("docs/upgrade-guide.md")
        versions = {
            json.loads(read(path))["version"]
            for path in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json")
        }

        self.assertEqual(versions, {"0.6.4"})
        self.assertEqual(upgrade.count("**v0.6.4 migration:**"), 2)
        self.assertEqual(upgrade.count("**v0.6.3 migration:**"), 2)
        self.assertIn("every config v1 project must run", upgrade)
        self.assertIn("preserves an exact valid binding", upgrade)
        self.assertIn("collision", upgrade)
        self.assertIn("profile removal", upgrade)
        for marker in (
            "restart",
            "safe live verifier",
            "current-host binding",
            "rerun setup",
            "rerun preflight",
            "zero mutation",
        ):
            self.assertIn(marker, upgrade)
        self.assertIn("current release: **v0.6.4**", readme)
        self.assertIn("codex installation supplies skills only", readme)
        self.assertIn("it does not supply an independent verifier", readme)
        self.assertIn("claude plugin agent", readme)

    def test_setup_and_implement_keep_discovery_receipts_out_of_config(self) -> None:
        setup = normalized("skills/setup/SKILL.md")
        implement = normalized("skills/implement/SKILL.md")
        for text in (setup, implement):
            self.assertIn("trusted live adapter capability", text)
            self.assertIn("never config", text)
            self.assertIn("never repository", text)
            self.assertIn("never prompt", text)
            self.assertIn("never user-provided", text)


if __name__ == "__main__":
    unittest.main()
