"""Behavioural tests for the independent-verifier boundary gate."""

from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "role_binding_contract.py"

spec = importlib.util.spec_from_file_location("role_binding_contract", HELPER)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

PACKAGED = (
    f"## harness-ship\n- **Independent verifier:** `claude-code` / `{gate.CLAUDE_PROFILE_ID}`\n"
)
CODEX_DECLARATION = "mode=read-only, write=none, spawn=no, context=fresh, effort=high"
CODEX = (
    "## harness-ship\n"
    f"- **Independent verifier:** `codex` / `Codex/verifier` — {CODEX_DECLARATION}\n"
)


def agent_file(directory: Path, **overrides) -> Path:
    fields = {
        "name": gate.AGENT_NAME,
        "description": "Used after implementation for fresh independent outcome verification.",
        "model": "inherit",
        "effort": "high",
        "tools": ["Read", "Grep", "Glob"],
    }
    fields.update(overrides)
    path = directory / f"{gate.AGENT_NAME}.md"
    path.write_text(f"---\n{json.dumps(fields)}\n---\n\nBody.\n", encoding="utf-8")
    return path


class PackagedVerifierTests(unittest.TestCase):
    """The shipped agent must satisfy the boundary it claims."""

    def test_shipped_agent_passes_its_own_boundary(self) -> None:
        self.assertEqual(gate.self_test()["status"], "pass")

    def test_claude_assurance_is_host_enforced(self) -> None:
        self.assertEqual(gate.preflight(PACKAGED)["assurance"], "host-enforced")


class DriftTests(unittest.TestCase):
    """Loosening the packaged agent must fail, and must name the field."""

    def drift(self, **overrides) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            return gate.preflight(PACKAGED, agent_file(Path(directory), **overrides))

    def test_added_write_tool_fails_and_names_tools(self) -> None:
        result = self.drift(tools=["Read", "Grep", "Glob", "Edit"])

        self.assertEqual(result["status"], "fail")
        self.assertEqual(set(result["violations"]), {"tools"})
        self.assertIn("Edit", result["violations"]["tools"]["observed"])

    def test_added_agent_tool_fails(self) -> None:
        """No Agent tool in the whitelist is what makes no-spawn physical."""
        self.assertEqual(self.drift(tools=["Read", "Grep", "Glob", "Agent"])["status"], "fail")

    def test_lowered_effort_fails_and_names_effort(self) -> None:
        result = self.drift(effort="medium")

        self.assertEqual(set(result["violations"]), {"effort"})
        self.assertEqual(result["violations"]["effort"]["observed"], "medium")

    def test_pinned_model_fails_and_names_model(self) -> None:
        result = self.drift(model="claude-haiku-4-5-20251001")

        self.assertEqual(set(result["violations"]), {"model"})

    def test_several_drifts_are_reported_together(self) -> None:
        result = self.drift(tools=["Read", "Write"], effort="low", model="pinned")

        self.assertEqual(set(result["violations"]), {"tools", "effort", "model"})

    def test_higher_effort_is_accepted(self) -> None:
        self.assertEqual(self.drift(effort="xhigh")["status"], "pass")

    def test_missing_agent_file_fails_closed(self) -> None:
        with self.assertRaises(gate.ContractError):
            gate.preflight(PACKAGED, ROOT / "agents" / "does-not-exist.md")

    def test_config_cannot_self_certify_over_a_drifted_agent(self) -> None:
        """The old contract accepted a caller-supplied record as evidence. This does not.

        Writing the required boundary into the config is not evidence that the
        agent has it — the agent file is the authority for Claude Code.
        """
        claimed = PACKAGED.rstrip("\n") + " — mode=read-only, write=none, effort=high\n"
        with tempfile.TemporaryDirectory() as directory:
            drifted = agent_file(Path(directory), tools=["Read", "Edit"], effort="low")
            result = gate.preflight(claimed, drifted)

        self.assertEqual(result["status"], "fail")
        self.assertEqual(set(result["violations"]), {"tools", "effort"})


class CodexDeclarationTests(unittest.TestCase):
    """Codex exposes nothing live; the declaration is re-asserted, not assumed."""

    def test_complete_declaration_passes_as_operator_declared(self) -> None:
        result = gate.preflight(CODEX)

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["assurance"], "operator-declared")

    def test_missing_declaration_fails(self) -> None:
        config = "## harness-ship\n- **Independent verifier:** `codex` / `Codex/verifier`\n"

        self.assertEqual(gate.preflight(config)["status"], "fail")

    def test_wrong_declared_boundary_fails_and_names_the_key(self) -> None:
        result = gate.preflight(CODEX.replace("write=none", "write=task worktree"))

        self.assertEqual(set(result["violations"]), {"write"})

    def test_lowered_declared_effort_fails(self) -> None:
        result = gate.preflight(CODEX.replace("effort=high", "effort=medium"))

        self.assertEqual(set(result["violations"]), {"effort"})


class BindingParsingTests(unittest.TestCase):
    def test_missing_block_fails(self) -> None:
        with self.assertRaises(gate.ContractError):
            gate.preflight("# Some project\n\nNo config here.\n")

    def test_missing_binding_fails(self) -> None:
        with self.assertRaises(gate.ContractError):
            gate.preflight("## harness-ship\n- **Integration branch:** `main`\n")

    def test_duplicate_bindings_fail(self) -> None:
        with self.assertRaises(gate.ContractError):
            gate.preflight(PACKAGED + "- **Independent verifier:** `codex` / `Codex/verifier`\n")

    def test_unsupported_host_fails(self) -> None:
        with self.assertRaises(gate.ContractError):
            gate.preflight("## harness-ship\n- **Independent verifier:** `cursor` / `x`\n")

    def test_claude_binding_must_be_the_packaged_profile(self) -> None:
        config = (
            "## harness-ship\n- **Independent verifier:** `claude-code` / `Claude/user/mine`\n"
        )

        with self.assertRaises(gate.ContractError):
            gate.preflight(config)

    def test_malformed_declaration_fails(self) -> None:
        with self.assertRaises(gate.ContractError):
            gate.preflight("## harness-ship\n- **Independent verifier:** `codex` / `C/v` — read-only\n")


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(HELPER), *args], capture_output=True, text=True)

    def test_self_test_exits_zero(self) -> None:
        self.assertEqual(self.run_cli("self-test").returncode, 0)

    def test_validate_agent_accepts_the_packaged_agent(self) -> None:
        self.assertEqual(self.run_cli("validate-agent", str(gate.PLUGIN_AGENT)).returncode, 0)

    def test_preflight_exits_two_on_violation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "AGENTS.md"
            config.write_text(CODEX.replace("effort=high", "effort=low"), encoding="utf-8")
            result = self.run_cli("preflight", "--config", str(config))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["reason_code"], "unsafe-verifier-boundary")

    def test_preflight_exits_two_on_unreadable_config(self) -> None:
        self.assertEqual(self.run_cli("preflight", "--config", "/nonexistent").returncode, 2)

    def test_preflight_exits_zero_on_the_packaged_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "AGENTS.md"
            config.write_text(PACKAGED, encoding="utf-8")

            self.assertEqual(self.run_cli("preflight", "--config", str(config)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
