#!/usr/bin/env python3
"""Fail-open, zero-LLM Stop/UserPromptSubmit/PostToolUse detector."""

from __future__ import annotations

import json
import re
import sys

SESSION_END = frozenset(
    {"sessionend", "session_end", "session-end", "session end"}
)
EVENT_ALIASES = {
    "stop": "Stop",
    "userpromptsubmit": "UserPromptSubmit",
    "user_prompt_submit": "UserPromptSubmit",
    "posttooluse": "PostToolUse",
    "post_tool_use": "PostToolUse",
}

GREEN_AS_PROOF = re.compile(
    r"(tests? are green|all tests pass(?:ed)?|suite is green|"
    r"ready to (?:merge|release|deploy)|this is a GO\b)",
    re.I,
)
JOURNEY_RISK = re.compile(
    r"\b(journey|e2e|end-to-end|handler|login|checkout|payment|deploy)\b",
    re.I,
)
AUTOMATE_WITHOUT_EXPLORE = re.compile(
    r"(wrote|added|adding)\s+(an?\s+)?(automated\s+)?tests?"
    r"|(playwright|cypress|selenium).{0,40}(test|spec)",
    re.I,
)
EXPLORED = re.compile(
    r"\b(exploratory|black-box|manually (?:tested|verified)|clicked through)\b",
    re.I,
)
DEFAULT_E2E = re.compile(
    r"(install(?:ing)?|add(?:ing)?)\s+(playwright|cypress|selenium|an e2e stack)"
    r"|the project has no e2e",
    re.I,
)
CHEAPER_SEAM = re.compile(r"cheaper (?:existing )?seam|cannot catch", re.I)
NO_SHA = re.compile(
    r"(ready for release|release evidence|this (?:is|was) tested)\b",
    re.I,
)
HAS_SHA = re.compile(r"\b([0-9a-f]{40}|candidate SHA|full (?:source )?SHA)\b", re.I)
POST_RELEASE = re.compile(
    r"\b(merged|tagged|deployed|published)\b.{0,80}\b(done|shipped|complete)\b"
    r"|\b(done|shipped|complete)\b.{0,80}\b(merged|tagged|deployed|published)\b",
    re.I,
)
SMOKE = re.compile(r"\bsmoke\b", re.I)
PROD_SEED = re.compile(
    r"(seed|fake|synthetic).{0,60}(production|prod dsn|prod database)"
    r"|(production|prod dsn|prod database).{0,60}(seed|fake|synthetic)",
    re.I,
)


def _text(payload: dict) -> str:
    parts = [
        payload.get("lastAssistantMessage"),
        payload.get("last_assistant_message"),
        payload.get("prompt"),
        payload.get("userPrompt"),
    ]
    tool = payload.get("toolInput") or payload.get("tool_input") or {}
    if isinstance(tool, dict):
        parts.extend(str(v) for v in tool.values() if isinstance(v, (str, int)))
    return "\n".join(p for p in parts if isinstance(p, str))


def _event(payload: dict) -> str:
    raw = (
        payload.get("hookEventName")
        or payload.get("hook_event_name")
        or payload.get("event")
        or ""
    )
    key = str(raw).replace(" ", "").replace("-", "_").lower()
    if key in SESSION_END:
        return "SessionEnd"
    return EVENT_ALIASES.get(key, str(raw))


def note_for(text: str) -> str | None:
    if not text.strip():
        return None
    if PROD_SEED.search(text):
        return (
            "Harness Ship: synthetic seed data aimed at a production DSN — stop. "
            "Staging and local only."
        )
    if DEFAULT_E2E.search(text) and not CHEAPER_SEAM.search(text):
        return (
            "Harness Ship: do not add Playwright/E2E because the project has none. "
            "Name the failure a cheaper existing seam cannot catch."
        )
    if AUTOMATE_WITHOUT_EXPLORE.search(text) and not EXPLORED.search(text):
        return (
            "Harness Ship: user-visible behaviour needs a black-box pass on a "
            "non-production surface before automated tests."
        )
    if GREEN_AS_PROOF.search(text) and JOURNEY_RISK.search(text):
        return (
            "Harness Ship: green tests are not product proof when the risk is a "
            "journey, handler, or external boundary."
        )
    if NO_SHA.search(text) and not HAS_SHA.search(text):
        return (
            "Harness Ship: observations are not release evidence without a candidate "
            "SHA or the candidate owner's external build identifier."
        )
    if POST_RELEASE.search(text) and not SMOKE.search(text):
        return (
            "Harness Ship: after merge, tag, or deploy, smoke that exact candidate "
            "on the real surface."
        )
    return None


def emit(event_name: str, note: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": note,
        }
    }


def main(argv: list[str] | None = None) -> int:
    del argv
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0
        event_name = _event(payload)
        if event_name == "SessionEnd":
            return 0
        note = note_for(_text(payload))
        if note:
            sys.stdout.write(json.dumps(emit(event_name or "Stop", note)))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
