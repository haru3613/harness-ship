#!/usr/bin/env python3
"""Packaged Claude verifier boundary diagnostic.

Claude Code's packaged verifier must remain read-only, unable to spawn children,
and high effort. This helper checks that definition for lifecycle validation.
Reviewer routing itself happens at invocation.

Nothing about the verifier is persisted. It is resolved from the running host,
because that is the only thing that determines which agent will actually load:

* **Claude Code** — this plugin ships the verifier agent. Read that file at
  check time and compare its tools, model and effort against the boundary. The
  whitelist is enforced by the host permission layer, so a verifier that cannot
  invoke Edit is not trusting itself to abstain. Real check; names the field
  that drifted.
* **Any other host** — this plugin ships no verifier there, so this diagnostic
  cannot establish independence. Review still resolves a host child at
  invocation and records the assurance it can observe.

Earlier versions recorded the verifier in project config. On Claude Code that
recorded a constant; on Codex it recorded an operator declaration that proved
nothing about the live profile while reading as a partial guarantee. Both are
gone — see issues #34 and #50.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

AGENT_NAME = "harness-ship-independent-verifier"
PLUGIN_AGENT = (Path(__file__).resolve().parents[1] / "agents" / f"{AGENT_NAME}.md").resolve()
CLAUDE_PROFILE_ID = f"harness-ship:{AGENT_NAME}"

# Read, Grep and Glob cannot edit and cannot dispatch a child. The absence of an
# Edit/Write tool and of an Agent tool is what makes the boundary physical.
REQUIRED_TOOLS = ["Glob", "Grep", "Read"]
HIGH_OR_HIGHER = {"high", "xhigh", "max", "ultra"}
# The config schema is what workflows depend on. The plugin version records what
# wrote the block and is deliberately not a gate: a patch or compatible minor
# release must not invalidate a configured project.
SUPPORTED_CONFIG_VERSION = 3
CONFIG_VERSION_RE = re.compile(
    r"(?mi)^[ \t]*[-*][ \t]*\*\*Config version:\*\*[ \t]*(?P<version>.*?)[ \t]*$"
)

AGENT_FIELDS = {"name", "description", "model", "effort", "tools"}
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
SECTION_RE = re.compile(r"(?m)^## harness-ship\s*$")
REMEDIATION = [
    "Upgrade and activate the current Harness Ship release, then restart the host.",
    "Use review to resolve a fresh child from the running host at invocation.",
    "Treat this diagnostic as an assurance label, not an implementation-readiness gate.",
]


class ContractError(ValueError):
    """The verifier binding does not satisfy the required boundary."""


def parse_agent(text: str, expected_name: str) -> Dict[str, Any]:
    """Read an agent definition's JSON frontmatter."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ContractError(f"{expected_name}: agent file has no frontmatter")
    try:
        fields = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise ContractError(f"{expected_name}: frontmatter is not valid JSON: {error}") from error
    if not isinstance(fields, dict) or set(fields) != AGENT_FIELDS:
        raise ContractError(
            f"{expected_name}: frontmatter must contain exactly {sorted(AGENT_FIELDS)}"
        )
    if fields["name"] != expected_name:
        raise ContractError(f"{expected_name}: frontmatter name is {fields['name']!r}")
    return fields


def detect_host(env: Optional[Mapping[str, str]] = None) -> str:
    """Identify the running host from its own runtime, never from an argument.

    A caller that could name its host could also name the one whose guarantee it
    wants, so this reads the environment the host sets for itself.
    """
    environ = os.environ if env is None else env
    return "claude-code" if environ.get("CLAUDECODE") else "unknown"


def _effort_violation(observed: str) -> Optional[Dict[str, str]]:
    if observed.lower() in HIGH_OR_HIGHER:
        return None
    return {"observed": observed, "required": "high or higher"}


def check_claude(agent_path: Path) -> Dict[str, Any]:
    """Compare the packaged agent definition the host will load against the boundary."""
    if not agent_path.is_file():
        raise ContractError(f"packaged verifier agent is missing at {agent_path}")
    fields = parse_agent(agent_path.read_text(encoding="utf-8"), AGENT_NAME)

    violations: Dict[str, Dict[str, Any]] = {}
    if sorted(fields["tools"]) != REQUIRED_TOOLS:
        violations["tools"] = {"observed": fields["tools"], "required": REQUIRED_TOOLS}
    if fields["model"] != "inherit":
        violations["model"] = {"observed": fields["model"], "required": "inherit"}
    effort = _effort_violation(fields["effort"])
    if effort:
        violations["effort"] = effort
    return {"assurance": "host-enforced", "violations": violations}


def read_config_version(config_text: str) -> int:
    """Workflows depend on the config schema, not on which plugin build wrote it."""
    matches = list(CONFIG_VERSION_RE.finditer(config_text))
    if len(matches) != 1:
        raise ContractError(f"config must declare exactly one Config version; found {len(matches)}")
    raw_version = matches[0].group("version")
    version_match = re.fullmatch(
        r"(?:`(?P<quoted>[0-9]+)`|(?P<plain>[0-9]+))", raw_version
    )
    if not version_match:
        raise ContractError(f"Config version must be an integer; found {raw_version!r}")
    version = int(version_match.group("quoted") or version_match.group("plain"))
    if version != SUPPORTED_CONFIG_VERSION:
        raise ContractError(
            f"config is version {version}, this release reads version "
            f"{SUPPORTED_CONFIG_VERSION}; re-run setup to regenerate the block"
        )
    return version


def read_config_block(config_text: str) -> str:
    """Return the one Harness Ship block, excluding later top-level sections."""
    matches = list(SECTION_RE.finditer(config_text))
    if len(matches) != 1:
        raise ContractError(
            f"config must contain exactly one ## harness-ship block; found {len(matches)}"
        )
    match = matches[0]
    tail = config_text[match.end() :]
    next_section = re.search(r"(?m)^##\s+", tail)
    end = match.end() + next_section.start() if next_section else len(config_text)
    return config_text[match.start() : end]


def preflight(
    config_text: str,
    agent_path: Path = PLUGIN_AGENT,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Inspect the packaged Claude verifier when the running host can load it."""
    config_version = read_config_version(read_config_block(config_text))
    host = detect_host(env)
    base = {"config_version": config_version, "host": host}

    if host != "claude-code":
        return {
            **base,
            "status": "degraded",
            "assurance": "independence: not established",
            "reason": (
                "this plugin ships an independent verifier for Claude Code only; "
                f"on {host} it cannot establish independence"
            ),
            "remediation": REMEDIATION,
        }

    outcome = check_claude(agent_path)
    result = {**base, "profile_id": CLAUDE_PROFILE_ID, "assurance": outcome["assurance"]}
    if outcome["violations"]:
        return {
            **result,
            "status": "fail",
            "reason_code": "unsafe-verifier-boundary",
            "violations": outcome["violations"],
            "remediation": REMEDIATION,
        }
    return {**result, "status": "pass"}


def validate_agent(path: Path) -> Dict[str, Any]:
    return parse_agent(path.read_text(encoding="utf-8"), path.stem)


def self_test() -> Dict[str, Any]:
    """Prove the packaged verifier still satisfies its own boundary."""
    config = f"## harness-ship\n- **Config version:** `{SUPPORTED_CONFIG_VERSION}`\n"
    result = preflight(config, env={"CLAUDECODE": "1"})
    if result["status"] != "pass":
        raise ContractError(f"packaged verifier fails its own boundary: {result['violations']}")
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--config", required=True, type=Path)
    agent_parser = subparsers.add_parser("validate-agent")
    agent_parser.add_argument("path", type=Path)
    subparsers.add_parser("self-test")
    args = parser.parse_args(argv)

    try:
        if args.command == "validate-agent":
            print(json.dumps({"status": "pass", "agent": validate_agent(args.path)["name"]}))
            return 0
        if args.command == "self-test":
            print(json.dumps(self_test(), sort_keys=True))
            return 0
        config_text = args.config.read_text(encoding="utf-8")
        result = preflight(config_text)
        print(json.dumps(result, sort_keys=True))
        if result["status"] == "pass":
            return 0
        return 1 if result["status"] == "degraded" else 2
    except (ContractError, OSError, UnicodeError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
