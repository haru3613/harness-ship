"""Behavioural tests for the independent-verifier boundary gate."""

from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "role_binding_contract.py"

spec = importlib.util.spec_from_file_location("role_binding_contract", HELPER)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

CONFIG = f"## harness-ship\n- **Config version:** `{gate.SUPPORTED_CONFIG_VERSION}`\n"
CLAUDE = {"CLAUDECODE": "1"}
OTHER_HOST = {}


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
        self.assertEqual(gate.preflight(CONFIG, env=CLAUDE)["assurance"], "host-enforced")


class DriftTests(unittest.TestCase):
    """Loosening the packaged agent must fail, and must name the field."""

    def drift(self, **overrides) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            return gate.preflight(CONFIG, agent_file(Path(directory), **overrides), env=CLAUDE)

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
            gate.preflight(CONFIG, ROOT / "agents" / "does-not-exist.md", env=CLAUDE)

    def test_config_text_cannot_override_a_drifted_agent(self) -> None:
        """The agent file is the authority; nothing written in config outranks it."""
        claimed = CONFIG + "- **Independent verifier:** mode=read-only, write=none, effort=high\n"
        with tempfile.TemporaryDirectory() as directory:
            drifted = agent_file(Path(directory), tools=["Read", "Edit"], effort="low")
            result = gate.preflight(claimed, drifted, env=CLAUDE)

        self.assertEqual(result["status"], "fail")
        self.assertEqual(set(result["violations"]), {"tools", "effort"})


class HostResolutionTests(unittest.TestCase):
    """The verifier comes from the running host, never from config or a caller."""

    def test_claude_code_resolves_the_packaged_verifier(self) -> None:
        result = gate.preflight(CONFIG, env=CLAUDE)

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["assurance"], "host-enforced")
        self.assertEqual(result["profile_id"], gate.CLAUDE_PROFILE_ID)

    def test_another_host_cannot_establish_independence(self) -> None:
        result = gate.preflight(CONFIG, env=OTHER_HOST)

        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["assurance"], "independence: not established")

    def test_degraded_is_not_a_boundary_failure(self) -> None:
        """A missing verifier and a broken one are different problems."""
        result = gate.preflight(CONFIG, env=OTHER_HOST)

        self.assertNotIn("violations", result)
        self.assertNotEqual(result.get("reason_code"), "unsafe-verifier-boundary")

    def test_config_cannot_assert_its_way_to_host_enforced(self) -> None:
        """The old design let the config name the host. This one reads the runtime."""
        claiming = CONFIG + (
            f"- **Independent verifier:** `claude-code` / `{gate.CLAUDE_PROFILE_ID}`\n"
        )

        self.assertEqual(gate.preflight(claiming, env=OTHER_HOST)["status"], "degraded")

    def test_a_stale_binding_line_is_ignored_not_rejected(self) -> None:
        stale = CONFIG + "- **Independent verifier:** `codex` / `Codex/verifier` — mode=read-only\n"

        self.assertEqual(gate.preflight(stale, env=CLAUDE)["status"], "pass")


class ConfigVersionTests(unittest.TestCase):
    """The plugin version records what wrote the block; only the schema is a gate."""

    def test_any_plugin_version_leaves_a_valid_config_working(self) -> None:
        for plugin_version in ("0.7.0", "0.7.1", "0.8.3", "1.2.0"):
            with self.subTest(plugin_version=plugin_version):
                config = CONFIG.replace(
                    "## harness-ship\n",
                    f"## harness-ship\n- **Plugin version:** `{plugin_version}`\n",
                )

                self.assertEqual(gate.preflight(config, env=CLAUDE)["status"], "pass")

    def test_an_older_config_schema_fails_with_an_actionable_message(self) -> None:
        older = gate.SUPPORTED_CONFIG_VERSION - 1
        config = CONFIG.replace(
            f"`{gate.SUPPORTED_CONFIG_VERSION}`", f"`{older}`", 1
        )

        with self.assertRaises(gate.ContractError) as caught:
            gate.preflight(config, env=CLAUDE)

        self.assertIn("re-run setup", str(caught.exception))

    def test_a_missing_config_version_fails(self) -> None:
        config = CONFIG.replace(
            f"- **Config version:** `{gate.SUPPORTED_CONFIG_VERSION}`\n", ""
        )

        with self.assertRaises(gate.ContractError):
            gate.preflight(config, env=CLAUDE)

    def test_duplicate_config_versions_fail_in_either_order(self) -> None:
        duplicates = (
            CONFIG.replace("## harness-ship\n", "## harness-ship\n- **Config version:** `2`\n"),
            CONFIG + "- **Config version:** `2`\n",
            CONFIG.replace("## harness-ship\n", "## harness-ship\n- **Config version:** `3.0`\n"),
        )
        for duplicate in duplicates:
            with self.subTest(duplicate=duplicate):
                with self.assertRaises(gate.ContractError) as caught:
                    gate.preflight(duplicate, env=CLAUDE)
                self.assertIn("exactly one Config version", str(caught.exception))

    def test_the_verdict_reports_the_config_version(self) -> None:
        self.assertEqual(gate.preflight(CONFIG, env=CLAUDE)["config_version"], gate.SUPPORTED_CONFIG_VERSION)


class ConfigParsingTests(unittest.TestCase):
    def test_missing_block_fails(self) -> None:
        with self.assertRaises(gate.ContractError):
            gate.preflight("# Some project\n\nNo config here.\n", env=CLAUDE)


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str, env: dict = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(HELPER), *args], capture_output=True, text=True, env=env
        )

    def test_self_test_exits_zero(self) -> None:
        self.assertEqual(self.run_cli("self-test").returncode, 0)

    def test_validate_agent_accepts_the_packaged_agent(self) -> None:
        self.assertEqual(self.run_cli("validate-agent", str(gate.PLUGIN_AGENT)).returncode, 0)

    def test_preflight_exits_two_on_a_malformed_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "AGENTS.md"
            config.write_text("## harness-ship\n- **Issue tracker:** local\n", encoding="utf-8")

            self.assertEqual(self.run_cli("preflight", "--config", str(config)).returncode, 2)

    def test_preflight_exits_two_on_unreadable_config(self) -> None:
        self.assertEqual(self.run_cli("preflight", "--config", "/nonexistent").returncode, 2)

    def test_preflight_exit_code_follows_the_host(self) -> None:
        """0 pass, 1 degraded, 2 broken — a caller can tell the three apart."""
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "AGENTS.md"
            config.write_text(CONFIG, encoding="utf-8")
            args = ["preflight", "--config", str(config)]

            self.assertEqual(self.run_cli(*args, env={**os.environ, "CLAUDECODE": "1"}).returncode, 0)
            stripped = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
            self.assertEqual(self.run_cli(*args, env=stripped).returncode, 1)


if __name__ == "__main__":
    unittest.main()
