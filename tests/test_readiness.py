"""Behavioural tests for tiered readiness.

The point: a project with only a tracker can plan, and a project with no QA
environment can still implement. A missing capability blocks its own tier and
nothing else — and is never reported ready.
"""

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

PLANNING = f"""## harness-ship

- **Config version:** `{gate.SUPPORTED_CONFIG_VERSION}`
- **Issue tracker:** GitHub issues via `gh`
"""

IMPLEMENTATION = PLANNING + """- **Integration branch:** `main`
- **RD API-contract command:** `python3 -m unittest discover -s tests`
"""

CLAUDE = {"CLAUDECODE": "1"}
OTHER_HOST = {}

QA = IMPLEMENTATION + """- **QA environment:** staging at https://staging.example.invalid
- **Artifact-provenance source:** GitHub Actions run + full commit SHA
- **QA evidence location:** durable PR comments
- **QA integration command:** `npm run test:integration`
"""


class PlanningTierTests(unittest.TestCase):
    def test_a_tracker_alone_is_enough_to_plan(self) -> None:
        tiers = gate.readiness(PLANNING, env=CLAUDE)

        self.assertTrue(tiers["planning"]["ready"])

    def test_planning_without_a_tracker_is_blocked(self) -> None:
        config = PLANNING.replace("- **Issue tracker:** GitHub issues via `gh`\n", "")
        tiers = gate.readiness(config, env=CLAUDE)

        self.assertFalse(tiers["planning"]["ready"])
        self.assertIn("configure the issue tracker", tiers["planning"]["blockers"])

    def test_a_not_configured_tracker_is_not_ready(self) -> None:
        config = PLANNING.replace("GitHub issues via `gh`", "not-configured")

        self.assertFalse(gate.readiness(config, env=CLAUDE)["planning"]["ready"])

    def test_an_unfilled_placeholder_is_not_ready(self) -> None:
        config = PLANNING.replace("GitHub issues via `gh`", "<system + access method>")

        self.assertFalse(gate.readiness(config, env=CLAUDE)["planning"]["ready"])


class ImplementationTierTests(unittest.TestCase):
    def test_a_planning_only_project_can_still_plan(self) -> None:
        """The headline: a missing verifier must not make planning look unusable."""
        tiers = gate.readiness(PLANNING, env=CLAUDE)

        self.assertTrue(tiers["planning"]["ready"])
        self.assertFalse(tiers["implementation"]["ready"])

    def test_reviewer_profile_does_not_gate_implementation_readiness(self) -> None:
        without_packaged_verifier = gate.readiness(IMPLEMENTATION, env=OTHER_HOST)
        with_packaged_verifier = gate.readiness(IMPLEMENTATION, env=CLAUDE)

        self.assertTrue(without_packaged_verifier["implementation"]["ready"])
        self.assertTrue(with_packaged_verifier["implementation"]["ready"])

    def test_no_rd_command_blocks_implementation(self) -> None:
        config = IMPLEMENTATION.replace(
            "- **RD API-contract command:** `python3 -m unittest discover -s tests`\n",
            "- **RD API-contract command:** `not-configured`\n",
        )
        blockers = gate.readiness(config, env=CLAUDE)["implementation"]["blockers"]

        self.assertIn("configure at least one RD command", blockers)

    def test_a_fully_configured_rd_project_is_implementation_ready(self) -> None:
        self.assertTrue(gate.readiness(IMPLEMENTATION, env=CLAUDE)["implementation"]["ready"])


class QaTierTests(unittest.TestCase):
    def test_no_qa_environment_blocks_only_qa(self) -> None:
        """The other headline: QA gaps must not block planning or implementation."""
        tiers = gate.readiness(IMPLEMENTATION, env=CLAUDE)

        self.assertTrue(tiers["planning"]["ready"])
        self.assertTrue(tiers["implementation"]["ready"])
        self.assertFalse(tiers["qa"]["ready"])
        self.assertIn("configure the qa environment", tiers["qa"]["blockers"])

    def test_a_fully_configured_project_is_ready_everywhere(self) -> None:
        tiers = gate.readiness(QA, env=CLAUDE)

        self.assertEqual([t for t in gate.TIERS if tiers[t]["ready"]], list(gate.TIERS))

    def test_a_manual_qa_procedure_counts_as_configured(self) -> None:
        config = QA.replace(
            "- **QA integration command:** `npm run test:integration`",
            "- **QA integration command:** manual: log in, place an order, screenshot the receipt",
        )

        self.assertTrue(gate.readiness(config, env=CLAUDE)["qa"]["ready"])

    def test_qa_does_not_inherit_a_reviewer_profile_blocker(self) -> None:
        tiers = gate.readiness(QA, env=OTHER_HOST)

        self.assertTrue(tiers["implementation"]["ready"])
        self.assertTrue(tiers["qa"]["ready"])

    def test_missing_qa_capability_is_never_reported_ready(self) -> None:
        for field in ("QA environment", "Artifact-provenance source", "QA evidence location"):
            with self.subTest(field=field):
                config = "\n".join(
                    line for line in QA.splitlines() if not line.startswith(f"- **{field}:**")
                )

                self.assertFalse(gate.readiness(config, env=CLAUDE)["qa"]["ready"])


class UnsetValueTests(unittest.TestCase):
    """An explained absence is still an absence — see #47."""

    def test_not_configured_with_an_explanation_is_still_unset(self) -> None:
        for value in (
            "`not-configured`",
            "`not-configured` — source-only repo, no deployed artifact",
            "not-configured — because reasons",
            "not configured -- nothing to deploy",
        ):
            with self.subTest(value=value):
                self.assertFalse(gate.is_set(value))

    def test_a_real_value_with_an_explanation_is_still_set(self) -> None:
        for value in (
            "`npm test`",
            "staging at https://staging.example.invalid — fixtures A/B",
            "GitHub issues via `gh` — maintainer only",
        ):
            with self.subTest(value=value):
                self.assertTrue(gate.is_set(value))

    def test_an_explained_missing_qa_environment_still_blocks_qa(self) -> None:
        config = QA.replace(
            "- **QA environment:** staging at https://staging.example.invalid",
            "- **QA environment:** `not-configured` — source-only repo, nothing is deployed",
        )
        tiers = gate.readiness(config, env=CLAUDE)

        self.assertFalse(tiers["qa"]["ready"])
        self.assertIn("configure the qa environment", tiers["qa"]["blockers"])


class CliTests(unittest.TestCase):
    def run_cli(self, text: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(HELPER), "readiness", "--config", str(path)],
                capture_output=True,
                text=True,
                env={**os.environ, "CLAUDECODE": "1"},
            )

    def test_a_planning_only_project_exits_zero(self) -> None:
        result = self.run_cli(PLANNING)

        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["implementation"]["ready"])

    def test_an_unconfigured_project_exits_two(self) -> None:
        config = PLANNING.replace("- **Issue tracker:** GitHub issues via `gh`\n", "")

        self.assertEqual(self.run_cli(config).returncode, 2)

    def test_an_unsupported_config_version_exits_two(self) -> None:
        stale = PLANNING.replace(
            f"- **Config version:** `{gate.SUPPORTED_CONFIG_VERSION}`",
            "- **Config version:** `2`",
        )
        result = self.run_cli(stale)

        self.assertEqual(result.returncode, 2)
        self.assertIn("config is version 2", result.stderr)

    def test_stray_fields_without_a_harness_ship_block_exit_two(self) -> None:
        result = self.run_cli(QA.replace("## harness-ship", "## unrelated"))

        self.assertEqual(result.returncode, 2)
        self.assertIn("exactly one ## harness-ship block", result.stderr)

    def test_duplicate_harness_ship_blocks_exit_two(self) -> None:
        duplicate = QA + "\n## harness-ship\n- **Config version:** `2`\n"
        result = self.run_cli(duplicate)

        self.assertEqual(result.returncode, 2)
        self.assertIn("exactly one ## harness-ship block", result.stderr)

    def test_duplicate_config_versions_exit_two_in_either_order(self) -> None:
        duplicates = (
            QA.replace("## harness-ship\n", "## harness-ship\n- **Config version:** `2`\n"),
            QA + "- **Config version:** `2`\n",
            QA + "- **Config version:** `banana`\n",
        )
        for duplicate in duplicates:
            with self.subTest(duplicate=duplicate):
                result = self.run_cli(duplicate)
                self.assertEqual(result.returncode, 2)
                self.assertIn("exactly one Config version", result.stderr)


if __name__ == "__main__":
    unittest.main()
