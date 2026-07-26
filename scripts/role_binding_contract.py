#!/usr/bin/env python3
"""Executable role-binding contract for harness-ship setup and implement."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any, Dict, List, Mapping


SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}")
PROFILE_FIELDS = {
    "host",
    "profile_id",
    "definition_source",
    "authoritative_definition_digest",
    "mode_sandbox",
    "model",
    "effort",
    "write_scope",
    "may_spawn",
    "fresh_context",
    "effective_tools_capabilities",
    "mcp_plugins",
}
PROFILE_INPUT_FIELDS = PROFILE_FIELDS - {"authoritative_definition_digest"}
BINDING_FIELDS = PROFILE_FIELDS | {"boundary_digest"}
CANDIDATE_FIELDS = {"binding", "source_kind", "source"}
RAW_CANDIDATE_FIELDS = {"profile", "source_kind", "source"}
DOCUMENT_FIELDS = {"current_host", "bindings", "candidates", "global_settings"}
HOSTS = {"codex", "claude-code"}
STRING_FIELDS = {
    "host",
    "profile_id",
    "definition_source",
    "authoritative_definition_digest",
    "mode_sandbox",
    "model",
    "effort",
    "write_scope",
}
BOOL_FIELDS = {"may_spawn", "fresh_context"}
ARRAY_FIELDS = {"effective_tools_capabilities", "mcp_plugins"}
AGENT_FIELDS = {"name", "description", "model", "effort", "tools"}
CLAUDE_PROFILE_ID = "harness-ship:harness-ship-independent-verifier"
PLUGIN_AGENT = (
    Path(__file__).resolve().parents[1]
    / "agents"
    / "harness-ship-independent-verifier.md"
).resolve()
HIGH_OR_HIGHER = {"high", "xhigh", "max", "ultra"}
UNSAFE_CAPABILITY_PARTS = {
    "agent",
    "bash",
    "delete",
    "edit",
    "exec",
    "mcp",
    "network",
    "shell",
    "skill",
    "spawn",
    "web",
    "write",
}
GOLDEN_PROFILE = {
    "host": "codex",
    "profile_id": "Codex/驗證器",
    "definition_source": "host-registry://codex/驗證器",
    "authoritative_definition_digest": (
        "sha256:264d06309cfa3b2281d74ce8e71f7cfc9ad446d0ca46a0001e8e3941c0a87465"
    ),
    "mode_sandbox": "read-only",
    "model": "模型-α",
    "effort": "high",
    "write_scope": "none",
    "may_spawn": False,
    "fresh_context": True,
    "effective_tools_capabilities": ["Glob", "Read", "讀取"],
    "mcp_plugins": [],
}
GOLDEN_BOUNDARY_DIGEST = (
    "sha256:f4305cf8ef26a3b166db90deefe5be38caeb91aecadfb20a69a28f8f396b2f4f"
)


class ContractError(ValueError):
    """Fail-closed role binding or agent contract violation."""


def _require_exact_keys(value: Mapping[str, Any], expected: set, label: str) -> None:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise ContractError(f"{label} fields mismatch: missing={missing} unknown={unknown}")


def _validate_nfc_string(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise ContractError(f"{label} must be a nonempty string")
    if unicodedata.normalize("NFC", value) != value:
        raise ContractError(f"{label} must be NFC-normalized")
    return value


def _validate_string_array(value: Any, label: str) -> List[str]:
    if type(value) is not list:
        raise ContractError(f"{label} must be an array")
    validated = [_validate_nfc_string(item, f"{label}[]") for item in value]
    if len(set(validated)) != len(validated):
        raise ContractError(f"{label} entries must be unique")
    if validated != sorted(validated):
        raise ContractError(f"{label} must be sorted by Unicode code point")
    return validated


def validate_profile(profile: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate and return the exact restricted no-number boundary schema."""
    _require_exact_keys(profile, PROFILE_FIELDS, "profile")
    result: Dict[str, Any] = {}
    for field in STRING_FIELDS:
        result[field] = _validate_nfc_string(profile[field], field)
    for field in BOOL_FIELDS:
        if type(profile[field]) is not bool:
            raise ContractError(f"{field} must be a boolean")
        result[field] = profile[field]
    for field in ARRAY_FIELDS:
        result[field] = _validate_string_array(profile[field], field)
    if result["host"] not in HOSTS:
        raise ContractError("host must be codex or claude-code")
    if not SHA256_RE.fullmatch(result["authoritative_definition_digest"]):
        raise ContractError("authoritative_definition_digest must be lowercase sha256")
    return {key: result[key] for key in profile}


def _canonical_json_bytes(profile: Mapping[str, Any]) -> bytes:
    validated = validate_profile(profile)
    return json.dumps(
        validated,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def boundary_digest(profile: Mapping[str, Any]) -> str:
    """Return the restricted RFC 8785-compatible canonical boundary digest."""
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(profile)).hexdigest()


def _source_bytes(source_kind: str, source: str, definition_source: str) -> bytes:
    _validate_nfc_string(source_kind, "source_kind")
    _validate_nfc_string(source, "source")
    if source_kind == "file":
        path = Path(source)
        resolved = path.resolve(strict=True)
        if source != str(resolved) or definition_source != str(resolved):
            raise ContractError("file definition source must be its canonical absolute path")
        for component in (resolved,) + tuple(resolved.parents):
            if component.is_symlink():
                raise ContractError("definition source must not contain symlinks")
        if not resolved.is_file():
            raise ContractError("definition source must be a regular file")
        return resolved.read_bytes()
    if source_kind == "host-record":
        if not definition_source.startswith("host-registry://"):
            raise ContractError("host record requires canonical host-registry provenance")
        return source.encode("utf-8")
    raise ContractError("source_kind must be file or host-record")


def _parse_agent_bytes(source_bytes: bytes, expected_name: str) -> Dict[str, Any]:
    try:
        text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError("agent source must be UTF-8") from error
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ContractError("invalid agent frontmatter delimiters")
    try:
        closing_index = lines.index("---", 1)
    except ValueError as error:
        raise ContractError("invalid agent frontmatter delimiters") from error
    try:
        fields = _strict_json_loads("\n".join(lines[1:closing_index]))
    except (json.JSONDecodeError, ContractError) as error:
        raise ContractError(f"malformed JSON agent frontmatter: {error}") from error
    _require_exact_keys(fields, AGENT_FIELDS, "agent frontmatter")
    for field in ("name", "description", "model", "effort"):
        _validate_nfc_string(fields[field], field)
    if fields["name"] != expected_name:
        raise ContractError("agent name must match its authoritative identity")
    if fields["name"] != "harness-ship-independent-verifier":
        raise ContractError("unexpected agent name")
    if fields["description"] != (
        "Used after implementation for fresh independent outcome verification."
    ):
        raise ContractError("unexpected agent description")
    if fields["model"] != "inherit" or fields["effort"] != "high":
        raise ContractError("unsafe agent model or effort")
    if fields["tools"] != ["Read", "Grep", "Glob"]:
        raise ContractError("unsafe agent tools")
    if not "\n".join(lines[closing_index + 1 :]).strip():
        raise ContractError("empty agent body")
    return fields


def _validate_source_semantics(
    profile: Mapping[str, Any], source_kind: str, source_bytes: bytes
) -> None:
    if profile["host"] == "claude-code":
        if source_kind != "file" or profile["profile_id"] != CLAUDE_PROFILE_ID:
            raise ContractError("Claude verifier requires scoped plugin file provenance")
        fields = _parse_agent_bytes(
            source_bytes, "harness-ship-independent-verifier"
        )
        if (
            profile["model"] != fields["model"]
            or profile["effort"] != fields["effort"]
            or profile["effective_tools_capabilities"] != sorted(fields["tools"])
            or profile["may_spawn"]
            or not profile["fresh_context"]
            or profile["mode_sandbox"] != "read-only tools"
            or profile["write_scope"] != "none"
            or profile["mcp_plugins"]
        ):
            raise ContractError("Claude profile boundary disagrees with agent source")
        return

    if source_kind != "host-record":
        raise ContractError("Codex verifier requires a canonical host registry record")
    try:
        record_text = source_bytes.decode("utf-8")
        record = _strict_json_loads(record_text)
    except (UnicodeDecodeError, json.JSONDecodeError, ContractError) as error:
        raise ContractError(f"invalid Codex host registry record: {error}") from error
    _require_exact_keys(record, PROFILE_INPUT_FIELDS, "Codex host registry record")
    canonical_record = json.dumps(
        profile,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if record != profile or record_text != canonical_record:
        raise ContractError("Codex host registry record disagrees with supplied profile")


def build_candidate(
    profile: Mapping[str, Any], source_kind: str, source: str
) -> Dict[str, Any]:
    """Build a live candidate from authoritative source evidence."""
    _require_exact_keys(profile, PROFILE_INPUT_FIELDS, "candidate profile")
    definition_source = _validate_nfc_string(
        profile["definition_source"], "definition_source"
    )
    definition_bytes = _source_bytes(source_kind, source, definition_source)
    _validate_source_semantics(profile, source_kind, definition_bytes)
    complete = dict(profile)
    complete["authoritative_definition_digest"] = (
        "sha256:" + hashlib.sha256(definition_bytes).hexdigest()
    )
    validated = validate_profile(complete)
    binding = dict(validated)
    binding["boundary_digest"] = boundary_digest(validated)
    return {"binding": binding, "source_kind": source_kind, "source": source}


def validate_candidate(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    _require_exact_keys(candidate, CANDIDATE_FIELDS, "candidate")
    binding = validate_binding(candidate["binding"])
    profile = {key: binding[key] for key in PROFILE_FIELDS}
    validated = validate_profile(profile)
    source_bytes = _source_bytes(
        candidate["source_kind"],
        candidate["source"],
        validated["definition_source"],
    )
    source_digest = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    if source_digest != validated["authoritative_definition_digest"]:
        raise ContractError("authoritative definition digest mismatch")
    source_profile = {
        key: binding[key]
        for key in PROFILE_INPUT_FIELDS
    }
    _validate_source_semantics(source_profile, candidate["source_kind"], source_bytes)
    return deepcopy(candidate)


def validate_binding(binding: Mapping[str, Any]) -> Dict[str, Any]:
    _require_exact_keys(binding, BINDING_FIELDS, "binding")
    profile = {key: binding[key] for key in PROFILE_FIELDS}
    validated = validate_profile(profile)
    if binding["boundary_digest"] != boundary_digest(validated):
        raise ContractError("boundary digest mismatch")
    return deepcopy(binding)


def _materialize_candidate(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    if isinstance(candidate, dict) and set(candidate) == RAW_CANDIDATE_FIELDS:
        return build_candidate(**candidate)
    return validate_candidate(candidate)


def _safe_materialized_candidate(candidate: Mapping[str, Any], host: str) -> bool:
    binding = candidate["binding"]
    if binding["host"] != host:
        return False
    if (
        binding["may_spawn"]
        or not binding["fresh_context"]
        or binding["mcp_plugins"]
        or "read-only" not in binding["mode_sandbox"].lower()
        or binding["write_scope"].lower() not in {"none", "no source edits"}
        or binding["effort"].lower() not in HIGH_OR_HIGHER
    ):
        return False
    capabilities = binding["effective_tools_capabilities"]
    if not capabilities:
        return False
    if any(
        unsafe in capability.lower()
        for capability in capabilities
        for unsafe in UNSAFE_CAPABILITY_PARTS
    ):
        return False
    if host == "claude-code":
        return (
            binding["profile_id"] == CLAUDE_PROFILE_ID
            and candidate["source_kind"] == "file"
            and binding["definition_source"] == str(PLUGIN_AGENT)
            and candidate["source"] == str(PLUGIN_AGENT)
            and capabilities == ["Glob", "Grep", "Read"]
        )
    return (
        candidate["source_kind"] == "host-record"
        and binding["definition_source"].startswith("host-registry://codex/")
    )


def resolve_document(document: Mapping[str, Any]) -> Dict[str, Any]:
    """Resolve one current-host binding without mutating other host/global state."""
    _require_exact_keys(document, DOCUMENT_FIELDS, "resolver document")
    host = document["current_host"]
    if host not in HOSTS:
        raise ContractError("current_host must be codex or claude-code")
    bindings = document["bindings"]
    _require_exact_keys(bindings, HOSTS, "bindings")
    if type(document["candidates"]) is not list:
        raise ContractError("candidates must be an array")

    result_bindings = deepcopy(bindings)
    result_global = deepcopy(document["global_settings"])
    valid = []
    for candidate in document["candidates"]:
        try:
            materialized = _materialize_candidate(candidate)
        except (ContractError, OSError, UnicodeError):
            continue
        if _safe_materialized_candidate(materialized, host):
            valid.append(materialized)
    explicit = bindings[host]
    if isinstance(explicit, dict):
        matching = [
            candidate
            for candidate in valid
            if candidate["binding"] == explicit
        ]
        if len(matching) == 1:
            return {
                "status": "preserved",
                "mutation": False,
                "bindings": result_bindings,
                "global_settings": result_global,
            }
    if len(valid) == 1:
        result_bindings[host] = deepcopy(valid[0]["binding"])
        return {
            "status": "selected",
            "mutation": result_bindings != bindings,
            "bindings": result_bindings,
            "global_settings": result_global,
        }
    if len(valid) > 1:
        return {
            "status": "ambiguous",
            "mutation": False,
            "bindings": result_bindings,
            "global_settings": result_global,
            "candidates": [candidate["binding"]["profile_id"] for candidate in valid],
        }
    return {
        "status": "missing",
        "mutation": False,
        "bindings": result_bindings,
        "global_settings": result_global,
        "actionable": (
            f"Install or configure one live-verifiable {host} independent verifier "
            "with authoritative provenance, then rerun setup."
        ),
    }


def _candidate_digest(candidate: Mapping[str, Any]) -> str:
    validated = _materialize_candidate(candidate)
    return validated["binding"]["boundary_digest"]


def preflight_document(document: Mapping[str, Any]) -> Dict[str, Any]:
    """Fail before Phase 0 unless persisted, live, and launch-plan metadata agree."""
    expected = {"persisted", "live", "launch_plan"}
    try:
        _require_exact_keys(document, expected, "preflight document")
        if any(document[field] is None for field in expected):
            raise ContractError("persisted, live, and launch metadata are required")
        persisted = validate_binding(document["persisted"])
        live = _materialize_candidate(document["live"])
        launch_plan = _materialize_candidate(document["launch_plan"])
        bindings = {
            "persisted": persisted,
            "live": live["binding"],
            "launch_plan": launch_plan["binding"],
        }
        digests = {
            field: bindings[field]["boundary_digest"]
            for field in expected
        }
        if len(set(digests.values())) != 1 or not (
            bindings["persisted"] == bindings["live"] == bindings["launch_plan"]
        ):
            raise ContractError("persisted, live, and launch metadata mismatch")
        host = bindings["persisted"]["host"]
        if not all(
            _safe_materialized_candidate(candidate, host)
            for candidate in (live, launch_plan)
        ):
            raise ContractError("unsafe verifier boundary")
        return {"status": "pass", "before_phase_0": True, "digests": digests}
    except (ContractError, KeyError, TypeError, OSError, UnicodeError) as error:
        return {"status": "fail", "before_phase_0": True, "error": str(error)}


def reconcile_post_launch(
    persisted: Mapping[str, Any],
    live: Mapping[str, Any],
    loaded: Mapping[str, Any],
) -> Dict[str, Any]:
    """Verify actual loaded metadata before trusting verifier output."""
    result = preflight_document(
        {"persisted": persisted, "live": live, "launch_plan": loaded}
    )
    result["post_launch"] = True
    return result


def post_launch_document(document: Mapping[str, Any]) -> Dict[str, Any]:
    _require_exact_keys(
        document, {"persisted", "live", "loaded"}, "post-launch document"
    )
    return reconcile_post_launch(
        document["persisted"], document["live"], document["loaded"]
    )


def validate_agent(path: Path) -> Dict[str, Any]:
    """Validate the exact JSON-form YAML frontmatter agent schema."""
    return _parse_agent_bytes(path.read_bytes(), path.stem)


def self_test() -> None:
    if boundary_digest(GOLDEN_PROFILE) != GOLDEN_BOUNDARY_DIGEST:
        raise ContractError("multilingual golden boundary digest mismatch")


def _reject_duplicate_keys(pairs: List[Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_json_loads(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=lambda constant: (_ for _ in ()).throw(
            ContractError(f"invalid JSON constant: {constant}")
        ),
    )


def _load_json(path: str) -> Dict[str, Any]:
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8")
    value = _strict_json_loads(text)
    if not isinstance(value, dict):
        raise ContractError("input must be a JSON object")
    return value


def _emit(payload: Mapping[str, Any]) -> None:
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("resolve", "preflight", "post-launch"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--input", required=True)
    agent_parser = subparsers.add_parser("validate-agent")
    agent_parser.add_argument("path")
    subparsers.add_parser("self-test")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-agent":
            _emit({"status": "pass", "agent": validate_agent(Path(args.path))["name"]})
            return 0
        if args.command == "self-test":
            self_test()
            _emit({"status": "pass"})
            return 0
        if args.command == "resolve":
            result = resolve_document(_load_json(args.input))
            _emit(result)
            return 0 if result["status"] in {"preserved", "selected"} else 2
        if args.command == "preflight":
            result = preflight_document(_load_json(args.input))
        else:
            result = post_launch_document(_load_json(args.input))
        _emit(result)
        return 0 if result["status"] == "pass" else 2
    except (ContractError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
