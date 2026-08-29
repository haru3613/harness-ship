"""Pins the zero-LLM test-engineer watch surface."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = ROOT / "watch"
DETECT = WATCH / "detect.py"
SKILL = ROOT / "skills" / "hs-setup" / "SKILL.md"
FORBIDDEN_MODULES = {
    "anthropic",
    "http.client",
    "httpx",
    "openai",
    "requests",
    "subprocess",
    "urllib",
    "urllib.request",
}


def run_detect(payload: dict | str) -> subprocess.CompletedProcess[str]:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(DETECT)],
        input=body,
        text=True,
        capture_output=True,
        check=False,
    )


class WatchContractTests(unittest.TestCase):
    def test_detector_imports_no_llm_or_network(self) -> None:
        tree = ast.parse(DETECT.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
                imported.add(node.module)
        self.assertTrue({"json", "re", "sys"} <= imported)
        self.assertEqual(imported & FORBIDDEN_MODULES, set())

    def test_detector_is_fail_open(self) -> None:
        empty = run_detect("")
        self.assertEqual(empty.returncode, 0)
        self.assertEqual(empty.stdout, "")
        broken = run_detect("not-json")
        self.assertEqual(broken.returncode, 0)
        self.assertEqual(broken.stdout, "")

    def test_session_end_is_a_no_op(self) -> None:
        result = run_detect(
            {
                "hookEventName": "SessionEnd",
                "lastAssistantMessage": "tests are green, ready to merge the checkout journey",
            }
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_stop_notes_are_additional_context_not_a_block(self) -> None:
        result = run_detect(
            {
                "hookEventName": "Stop",
                "lastAssistantMessage": "All tests passed. Ready to merge the checkout journey.",
            }
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        note = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("green tests are not product proof", note.lower())
        self.assertNotIn("decision", payload)

    def test_default_e2e_and_production_seed_are_flagged(self) -> None:
        e2e = run_detect(
            {
                "hookEventName": "Stop",
                "lastAssistantMessage": "Installing Playwright because the project has no e2e.",
            }
        )
        self.assertIn("cheaper existing seam", json.loads(e2e.stdout)["hookSpecificOutput"]["additionalContext"])
        seed = run_detect(
            {
                "hookEventName": "UserPromptSubmit",
                "prompt": "Seed fake users into the production DSN so QA can click around.",
            }
        )
        self.assertIn("production DSN", json.loads(seed.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_adapters_cover_three_hosts_without_session_end_or_home_hooks(self) -> None:
        adapters = {
            "claude": WATCH / "adapters" / "claude.settings.json",
            "codex": WATCH / "adapters" / "codex.hooks.json",
            "grok": WATCH / "adapters" / "grok.hooks.json",
        }
        for name, path in adapters.items():
            with self.subTest(host=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                events = set(data["hooks"])
                self.assertEqual(events, {"UserPromptSubmit", "Stop", "PostToolUse"})
                blob = path.read_text(encoding="utf-8")
                self.assertNotIn("SessionEnd", blob)
                self.assertNotIn("~/.codex/hooks.json", blob)
                self.assertNotIn("~/.claude/settings.json", blob)
                self.assertNotIn("~/.grok/hooks/", blob)
                self.assertIn("python3 .harness-ship/watch/detect.py", blob)

    def test_hs_setup_first_run_and_fast_path_contract(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        rules = (WATCH / "RULES.md").read_text(encoding="utf-8")
        self.assertIn("## harness-ship-watch", skill)
        self.assertIn("**Test engineer watch:**", skill)
        self.assertIn("**Test engineer watch** field means off.", skill)
        self.assertIn("Do not add `## harness-ship-watch`", skill)
        self.assertIn("Never write `~/.codex/hooks.json`", skill)
        self.assertIn("Grok `SessionEnd` stays zero-LLM.", skill)
        self.assertIn("Never spawn Claude, Codex, or Grok from a hook.", skill)
        self.assertIn(".claude/settings.json", skill)
        self.assertIn(".codex/hooks.json", skill)
        self.assertIn(".grok/hooks/harness-ship-watch.json", skill)
        self.assertIn("Do not nag TDD versus BDD", rules)
        self.assertIn("Do not install Playwright or E2E by default", rules)
        self.assertIn("Do not seed production", rules)


if __name__ == "__main__":
    unittest.main()
