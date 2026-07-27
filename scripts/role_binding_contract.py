#!/usr/bin/env python3
"""Packaged Claude verifier diagnostic and project-readiness report.

Claude Code's packaged verifier must remain read-only, unable to spawn children,
and high effort. This helper checks that definition for lifecycle validation.
Reviewer routing itself happens at invocation and does not gate implementation
readiness.

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
CONFIG_VERSION_RE = re.compile(r"(?mi)^\s*[-*]\s*\*\*Config version:\*\*\s*`?(?P<version>\d+)`?\s*$")

AGENT_FIELDS = {"name", "description", "model", "effort", "tools"}
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
SECTION_RE = re.compile(r"(?m)^## harness-ship\s*$")
# Readiness is tiered so a missing QA environment blocks QA and nothing else.
# Modelled on skills/review/SKILL.md's `independence: not established`: degrade
# and say so, rather than bricking every workflow.
FIELD_RE = re.compile(r"(?m)^\s*[-*]\s*\*\*(?P<name>[^*]+?):\*\*\s*(?P<value>.*?)\s*$")
PLACEHOLDER_RE = re.compile(r"^<.*>$")
UNSET_VALUES = {"", "not-configured", "not configured", "tbd"}
EXPLANATION_RE = re.compile(r"\s+(?:[—–]|--)\s+")
TIERS = ("planning", "implementation", "qa")

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
    match = CONFIG_VERSION_RE.search(config_text)
    if not match:
        raise ContractError("config declares no Config version")
    version = int(match.group("version"))
    if version != SUPPORTED_CONFIG_VERSION:
        raise ContractError(
            f"config is version {version}, this release reads version "
            f"{SUPPORTED_CONFIG_VERSION}; re-run setup to regenerate the block"
        )
    return version


def preflight(
    config_text: str,
    agent_path: Path = PLUGIN_AGENT,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Inspect the packaged Claude verifier when the running host can load it."""
    config_version = read_config_version(config_text)
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


def read_fields(config_text: str) -> Dict[str, str]:
    """Every `- **Name:** value` line in the block, backticks stripped."""
    return {
        m.group("name").strip(): m.group("value").strip().strip("`").strip()
        for m in FIELD_RE.finditer(config_text)
    }


def is_set(value: Optional[str]) -> bool:
    """An explained absence is still an absence.

    Operators document *why* a capability is missing, so compare the leading
    segment rather than the whole string — otherwise `not-configured — nothing
    is deployed` reads as configured and the tier is reported ready.
    """
    if value is None:
        return False
    head = EXPLANATION_RE.split(value.strip(), maxsplit=1)[0].strip().strip("`").strip()
    return bool(head) and head.lower() not in UNSET_VALUES and not PLACEHOLDER_RE.match(head)


def readiness(
    config_text: str,
    agent_path: Path = PLUGIN_AGENT,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Report planning / implementation / QA readiness independently.

    A capability that is absent blocks only the tier that needs it. Nothing is
    ever reported ready on the strength of a missing field.
    """
    fields = read_fields(config_text)
    result: Dict[str, Any] = {}

    def tier(name: str, blockers: List[str], inherits: Optional[str] = None) -> None:
        if inherits and not result[inherits]["ready"]:
            blockers = [f"{inherits} is not ready"] + blockers
        result[name] = (
            {"ready": True} if not blockers else {"ready": False, "blockers": blockers}
        )

    tier("planning", [] if is_set(fields.get("Issue tracker")) else ["configure the issue tracker"])

    blockers: List[str] = []
    if not is_set(fields.get("Integration branch")):
        blockers.append("configure the integration branch")
    if not any(is_set(fields.get(f"RD {kind} command")) for kind in ("unit", "API-contract")):
        blockers.append("configure at least one RD command")
    tier("implementation", blockers, inherits="planning")

    blockers = [
        f"configure the {name.lower()}"
        for name in ("QA environment", "Artifact-provenance source", "QA evidence location")
        if not is_set(fields.get(name))
    ]
    if not any(
        is_set(fields.get(f"QA {kind} command")) for kind in ("integration", "P0", "full-suite")
    ):
        blockers.append("configure at least one QA command or manual procedure")
    tier("qa", blockers, inherits="implementation")
    return result


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
    readiness_parser = subparsers.add_parser("readiness")
    readiness_parser.add_argument("--config", required=True, type=Path)
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
        if args.command == "readiness":
            tiers = readiness(config_text)
            print(json.dumps(tiers, sort_keys=True))
            return 0 if tiers["planning"]["ready"] else 2
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
