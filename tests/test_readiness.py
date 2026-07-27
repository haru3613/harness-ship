"""Behavioural tests for tiered readiness.

The point: a project with only a tracker can plan, and a project with no QA
environment can still implement. A missing capability blocks its own tier and
nothing else — and is never reported ready.
"""

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

PLANNING = f"""## harness-ship

- **Config version:** `{gate.SUPPORTED_CONFIG_VERSION}`
- **Issue tracker:** GitHub issues via `gh`
"""

IMPLEMENTATION = PLANNING + f"""- **Integration branch:** `main`
- **RD API-contract command:** `python3 -m unittest discover -s tests`
- **Independent verifier:** `claude-code` / `{gate.CLAUDE_PROFILE_ID}`
"""

QA = IMPLEMENTATION + """- **QA environment:** staging at https://staging.example.invalid
- **Artifact-provenance source:** GitHub Actions run + full commit SHA
- **QA evidence location:** durable PR comments
- **QA integration command:** `npm run test:integration`
"""


class PlanningTierTests(unittest.TestCase):
    def test_a_tracker_alone_is_enough_to_plan(self) -> None:
        tiers = gate.readiness(PLANNING)

        self.assertTrue(tiers["planning"]["ready"])

    def test_planning_without_a_tracker_is_blocked(self) -> None:
        config = PLANNING.replace("- **Issue tracker:** GitHub issues via `gh`\n", "")
        tiers = gate.readiness(config)

        self.assertFalse(tiers["planning"]["ready"])
        self.assertIn("configure the issue tracker", tiers["planning"]["blockers"])

    def test_a_not_configured_tracker_is_not_ready(self) -> None:
        config = PLANNING.replace("GitHub issues via `gh`", "not-configured")

        self.assertFalse(gate.readiness(config)["planning"]["ready"])

    def test_an_unfilled_placeholder_is_not_ready(self) -> None:
        config = PLANNING.replace("GitHub issues via `gh`", "<system + access method>")

        self.assertFalse(gate.readiness(config)["planning"]["ready"])


class ImplementationTierTests(unittest.TestCase):
    def test_a_planning_only_project_can_still_plan(self) -> None:
        """The headline: a missing verifier must not make planning look unusable."""
        tiers = gate.readiness(PLANNING)

        self.assertTrue(tiers["planning"]["ready"])
        self.assertFalse(tiers["implementation"]["ready"])

    def test_missing_verifier_blocks_implementation_and_names_the_fix(self) -> None:
        config = IMPLEMENTATION.replace(
            f"- **Independent verifier:** `claude-code` / `{gate.CLAUDE_PROFILE_ID}`\n", ""
        )
        blockers = gate.readiness(config)["implementation"]["blockers"]

        self.assertTrue(any("bind an independent verifier" in b for b in blockers))

    def test_a_drifted_verifier_blocks_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{gate.AGENT_NAME}.md"
            fields = {
                "name": gate.AGENT_NAME,
                "description": "d",
                "model": "inherit",
                "effort": "high",
                "tools": ["Read", "Edit"],
            }
            path.write_text(f"---\n{json.dumps(fields)}\n---\n\nBody.\n", encoding="utf-8")
            tiers = gate.readiness(IMPLEMENTATION, path)

        self.assertFalse(tiers["implementation"]["ready"])
        self.assertIn("repair the independent verifier boundary", tiers["implementation"]["blockers"])

    def test_no_rd_command_blocks_implementation(self) -> None:
        config = IMPLEMENTATION.replace(
            "- **RD API-contract command:** `python3 -m unittest discover -s tests`\n",
            "- **RD API-contract command:** `not-configured`\n",
        )
        blockers = gate.readiness(config)["implementation"]["blockers"]

        self.assertIn("configure at least one RD command", blockers)

    def test_a_fully_configured_rd_project_is_implementation_ready(self) -> None:
        self.assertTrue(gate.readiness(IMPLEMENTATION)["implementation"]["ready"])


class QaTierTests(unittest.TestCase):
    def test_no_qa_environment_blocks_only_qa(self) -> None:
        """The other headline: QA gaps must not block planning or implementation."""
        tiers = gate.readiness(IMPLEMENTATION)

        self.assertTrue(tiers["planning"]["ready"])
        self.assertTrue(tiers["implementation"]["ready"])
        self.assertFalse(tiers["qa"]["ready"])
        self.assertIn("configure the qa environment", tiers["qa"]["blockers"])

    def test_a_fully_configured_project_is_ready_everywhere(self) -> None:
        tiers = gate.readiness(QA)

        self.assertEqual([t for t in gate.TIERS if tiers[t]["ready"]], list(gate.TIERS))

    def test_a_manual_qa_procedure_counts_as_configured(self) -> None:
        config = QA.replace(
            "- **QA integration command:** `npm run test:integration`",
            "- **QA integration command:** manual: log in, place an order, screenshot the receipt",
        )

        self.assertTrue(gate.readiness(config)["qa"]["ready"])

    def test_qa_inherits_an_implementation_blocker_rather_than_hiding_it(self) -> None:
        config = QA.replace(
            f"- **Independent verifier:** `claude-code` / `{gate.CLAUDE_PROFILE_ID}`\n", ""
        )
        tiers = gate.readiness(config)

        self.assertFalse(tiers["qa"]["ready"])
        self.assertIn("implementation is not ready", tiers["qa"]["blockers"])

    def test_missing_qa_capability_is_never_reported_ready(self) -> None:
        for field in ("QA environment", "Artifact-provenance source", "QA evidence location"):
            with self.subTest(field=field):
                config = "\n".join(
                    line for line in QA.splitlines() if not line.startswith(f"- **{field}:**")
                )

                self.assertFalse(gate.readiness(config)["qa"]["ready"])


class CliTests(unittest.TestCase):
    def run_cli(self, text: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(HELPER), "readiness", "--config", str(path)],
                capture_output=True,
                text=True,
            )

    def test_a_planning_only_project_exits_zero(self) -> None:
        result = self.run_cli(PLANNING)

        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["implementation"]["ready"])

    def test_an_unconfigured_project_exits_two(self) -> None:
        config = PLANNING.replace("- **Issue tracker:** GitHub issues via `gh`\n", "")

        self.assertEqual(self.run_cli(config).returncode, 2)


if __name__ == "__main__":
    unittest.main()
