#!/usr/bin/env python3
"""Independent-verifier boundary gate.

`implement` must not proceed unless the agent that will serve as independent
verifier is read-only, cannot spawn children, and runs at high effort — checked
now, against the definition the host will actually load, not against something
recorded earlier.

Two hosts, two different strengths of guarantee, stated honestly rather than
papered over:

* **Claude Code** — the packaged agent file is read at check time and its
  declared tools, model and effort are compared against the required boundary.
  The tool whitelist is enforced by the host permission layer, so a verifier
  that cannot invoke Edit is not trusting itself to abstain. This is a real
  check, and it names the field that drifted.
* **Codex** — no Codex interface exposes live profile metadata. The binding
  therefore carries an operator declaration that this gate re-asserts. That
  proves the operator wrote down the right boundary; it cannot prove the live
  profile matches it. `assurance` reports which of the two you got.

This replaces a 2,249-line contract whose Codex digest chain verified the
caller against a re-serialization of the caller's own input, and whose
"discovery receipt" trust boundary was declared in prose addressed to the agent
it was meant to constrain. See issue #34.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

AGENT_NAME = "harness-ship-independent-verifier"
PLUGIN_AGENT = (Path(__file__).resolve().parents[1] / "agents" / f"{AGENT_NAME}.md").resolve()
CLAUDE_PROFILE_ID = f"harness-ship:{AGENT_NAME}"

# Read, Grep and Glob cannot edit and cannot dispatch a child. The absence of an
# Edit/Write tool and of an Agent tool is what makes the boundary physical.
REQUIRED_TOOLS = ["Glob", "Grep", "Read"]
HIGH_OR_HIGHER = {"high", "xhigh", "max", "ultra"}
REQUIRED_DECLARATION = {
    "mode": "read-only",
    "write": "none",
    "spawn": "no",
    "context": "fresh",
}

# The config schema is what workflows depend on. The plugin version records what
# wrote the block and is deliberately not a gate: a patch or compatible minor
# release must not invalidate a configured project.
SUPPORTED_CONFIG_VERSION = 3
CONFIG_VERSION_RE = re.compile(r"(?mi)^\s*[-*]\s*\*\*Config version:\*\*\s*`?(?P<version>\d+)`?\s*$")

SUPPORTED_HOSTS = ("claude-code", "codex")
AGENT_FIELDS = {"name", "description", "model", "effort", "tools"}
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
SECTION_RE = re.compile(r"(?m)^## harness-ship\s*$")
BINDING_RE = re.compile(
    r"(?m)^- \*\*Independent verifier:\*\*\s+`(?P<host>[^`]+)`\s*/\s*"
    r"`(?P<profile>[^`]+)`\s*(?:—\s*(?P<declaration>.+?))?\s*$"
)

# Readiness is tiered so a missing QA environment blocks QA and nothing else.
# Modelled on skills/review/SKILL.md's `independence: not established`: degrade
# and say so, rather than bricking every workflow.
FIELD_RE = re.compile(r"(?m)^\s*[-*]\s*\*\*(?P<name>[^*]+?):\*\*\s*(?P<value>.*?)\s*$")
PLACEHOLDER_RE = re.compile(r"^<.*>$")
UNSET_VALUES = {"", "not-configured", "not configured", "tbd"}
TIERS = ("planning", "implementation", "qa")

REMEDIATION = [
    "Upgrade and activate the current Harness Ship release, then restart the host.",
    "Select a live verifier profile whose permissions match the required boundary;"
    " Harness Ship never mutates global profiles.",
    "Repair only this project's Independent verifier line, then rerun preflight.",
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


def parse_declaration(raw: Optional[str]) -> Dict[str, str]:
    """Parse `mode=read-only, write=none, ...` into a mapping."""
    if not raw:
        return {}
    declaration: Dict[str, str] = {}
    for item in raw.split(","):
        key, separator, value = item.partition("=")
        if not separator:
            raise ContractError(f"malformed verifier declaration near {item.strip()!r}")
        key = key.strip()
        if key in declaration:
            raise ContractError(f"duplicate verifier declaration key {key!r}")
        declaration[key] = value.strip()
    return declaration


def read_binding(config_text: str) -> Dict[str, Any]:
    """Extract the single Independent verifier line from a harness-ship block."""
    if not SECTION_RE.search(config_text):
        raise ContractError("config has no `## harness-ship` block")
    matches = BINDING_RE.findall(config_text)
    if not matches:
        raise ContractError("config declares no Independent verifier")
    if len(matches) > 1:
        raise ContractError(f"config declares {len(matches)} Independent verifier lines, expected 1")
    match = BINDING_RE.search(config_text)
    host = match.group("host")
    if host not in SUPPORTED_HOSTS:
        raise ContractError(f"unsupported verifier host {host!r}; expected one of {list(SUPPORTED_HOSTS)}")
    return {
        "host": host,
        "profile_id": match.group("profile"),
        "declaration": parse_declaration(match.group("declaration")),
    }


def _effort_violation(observed: str) -> Optional[Dict[str, str]]:
    if observed.lower() in HIGH_OR_HIGHER:
        return None
    return {"observed": observed, "required": "high or higher"}


def check_claude(binding: Dict[str, Any], agent_path: Path) -> Dict[str, Any]:
    """Compare the packaged agent definition the host will load against the boundary."""
    if binding["profile_id"] != CLAUDE_PROFILE_ID:
        raise ContractError(
            f"Claude Code verifier must be the packaged {CLAUDE_PROFILE_ID}, "
            f"got {binding['profile_id']!r}"
        )
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


def check_codex(binding: Dict[str, Any]) -> Dict[str, Any]:
    """Re-assert the operator's written declaration. Codex exposes nothing live."""
    declaration = binding["declaration"]
    violations: Dict[str, Dict[str, Any]] = {}
    for key, required in REQUIRED_DECLARATION.items():
        observed = declaration.get(key)
        if observed != required:
            violations[key] = {"observed": observed, "required": required}
    effort = _effort_violation(declaration.get("effort", ""))
    if effort:
        violations["effort"] = effort
    return {"assurance": "operator-declared", "violations": violations}


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


def preflight(config_text: str, agent_path: Path = PLUGIN_AGENT) -> Dict[str, Any]:
    """Return a pass/fail verdict for the configured independent verifier."""
    config_version = read_config_version(config_text)
    binding = read_binding(config_text)
    if binding["host"] == "claude-code":
        outcome = check_claude(binding, agent_path)
    else:
        outcome = check_codex(binding)

    result = {
        "config_version": config_version,
        "host": binding["host"],
        "profile_id": binding["profile_id"],
        "assurance": outcome["assurance"],
    }
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
    if value is None:
        return False
    value = value.strip().strip("`").strip()
    return bool(value) and value.lower() not in UNSET_VALUES and not PLACEHOLDER_RE.match(value)


def readiness(config_text: str, agent_path: Path = PLUGIN_AGENT) -> Dict[str, Any]:
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
    try:
        verdict = preflight(config_text, agent_path)
        if verdict["status"] != "pass":
            blockers.append("repair the independent verifier boundary")
    except ContractError as error:
        blockers.append(f"bind an independent verifier ({error})")
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
    config = (
        "## harness-ship\n"
        f"- **Config version:** `{SUPPORTED_CONFIG_VERSION}`\n"
        f"- **Independent verifier:** `claude-code` / `{CLAUDE_PROFILE_ID}`\n"
    )
    result = preflight(config)
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
        return 0 if result["status"] == "pass" else 2
    except (ContractError, OSError, UnicodeError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
