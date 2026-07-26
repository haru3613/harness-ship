#!/usr/bin/env python3
"""Executable role-binding contract for harness-ship setup and implement."""

from __future__ import annotations

import argparse
from copy import deepcopy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import unicodedata
from typing import Any, Dict, List, Mapping


SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}")
PROFILE_FIELDS = {
    "host",
    "origin_scope",
    "profile_id",
    "definition_source",
    "authoritative_definition_digest",
    "mode_sandbox",
    "model",
    "effective_model",
    "effort",
    "work_nature",
    "write_scope",
    "may_spawn",
    "fresh_context",
    "effective_tools_capabilities",
    "mcp_plugins",
}
PROFILE_INPUT_FIELDS = PROFILE_FIELDS - {"authoritative_definition_digest"}
BINDING_FIELDS = PROFILE_FIELDS | {"boundary_digest"}
CANDIDATE_FIELDS = {"binding", "source_kind", "source", "discovery_receipt"}
RAW_CANDIDATE_FIELDS = {"profile", "source_kind", "source", "discovery_receipt"}
DISCOVERY_RECEIPT_FIELDS = {
    "adapter",
    "host",
    "origin_scope",
    "profile_id",
    "definition_source",
    "authoritative_definition_digest",
    "effective_model",
    "host_default",
}
DOCUMENT_FIELDS = {"current_host", "bindings", "candidates", "global_settings"}
CONFIG_RECONCILE_FIELDS = {"config_text", "current_host", "candidates"}
CONFIG_PLAN_FIELDS = {"repo_root", "target_basename", "current_host", "candidates"}
CONFIG_APPLY_FIELDS = CONFIG_PLAN_FIELDS | {"plan", "confirmed_plan_id"}
HOSTS = {"codex", "claude-code"}
PLUGIN_VERSION = "0.7.0"
CONFIG_VERSION = "2"
BINDING_CONTRACT_VERSION = "2"
HELPER_VERSION = "2"
PLAN_VERSION = "2"
PLAN_DOMAIN = b"harness-ship.role-binding-config-plan.v2\x00"
TARGET_BASENAMES = {"AGENTS.md", "CLAUDE.md"}
VERSION_ENVELOPE = {
    "helper_version": HELPER_VERSION,
    "plugin_version": PLUGIN_VERSION,
    "config_version": CONFIG_VERSION,
    "verifier_binding_contract_version": BINDING_CONTRACT_VERSION,
}
HOST_ORIGIN_SCOPES = {
    "codex": {"builtin", "project", "user"},
    "claude-code": {"plugin", "project", "user"},
}
STRING_FIELDS = {
    "host",
    "origin_scope",
    "profile_id",
    "definition_source",
    "authoritative_definition_digest",
    "mode_sandbox",
    "model",
    "effective_model",
    "effort",
    "work_nature",
    "write_scope",
}
BOOL_FIELDS = {"may_spawn", "fresh_context"}
ARRAY_FIELDS = {"effective_tools_capabilities", "mcp_plugins"}
AGENT_FIELDS = {"name", "description", "model", "effort", "tools"}
CLAUDE_PROFILE_ID = "harness-ship:harness-ship-independent-verifier"
CLAUDE_PLUGIN_DEFINITION_SOURCE = (
    "plugin://harness-ship/agents/harness-ship-independent-verifier.md"
)
PLUGIN_AGENT = (
    Path(__file__).resolve().parents[1]
    / "agents"
    / "harness-ship-independent-verifier.md"
).resolve()
HIGH_OR_HIGHER = {"high", "xhigh", "max", "ultra"}
HOST_BOUNDARIES = {
    "claude-code": {
        "mode_sandbox": "read-only tools",
        "write_scope": "none",
        "effective_tools_capabilities": ["Glob", "Grep", "Read"],
    },
    "codex": {
        "mode_sandbox": "read-only",
        "write_scope": "no source edits",
        "effective_tools_capabilities": ["Glob", "Grep", "Read"],
    },
}
VERIFIER_REMEDIATION = [
    (
        "Upgrade and activate the current Harness Ship release, then restart the "
        "host so it reloads verifier metadata."
    ),
    (
        "Configure or select one safe live verifier whose permissions match the "
        "required host-enforced boundary; Harness Ship does not mutate global profiles."
    ),
    (
        "After reviewing the mismatch, explicitly clear or repair only the project's "
        "current-host binding."
    ),
    (
        "Rerun setup to reconcile Config v1, then rerun preflight before implementation."
    ),
]
CODEX_PROFILE_RE = re.compile(r"Codex/([A-Za-z0-9][A-Za-z0-9._-]*)")
CLAUDE_CUSTOM_PROFILE_RE = re.compile(
    r"Claude/(project|user)/([A-Za-z0-9][A-Za-z0-9._-]*)"
)
INDEPENDENT_VERIFICATION = "independent verification"
LEGACY_TABLE_HEADER = (
    "| Work nature | Host / profile ID | Definition source | Definition digest | "
    "Mode / sandbox | Model | Effort | Write scope | Effective tools/capabilities | "
    "MCP/plugins | Fresh context | May spawn | Boundary digest |"
)
TABLE_SEPARATOR = "|" + "---|" * 13
GOLDEN_PROFILE = {
    "host": "codex",
    "origin_scope": "builtin",
    "profile_id": "Codex/驗證器",
    "definition_source": "host-registry://codex/builtin/驗證器",
    "authoritative_definition_digest": (
        "sha256:264d06309cfa3b2281d74ce8e71f7cfc9ad446d0ca46a0001e8e3941c0a87465"
    ),
    "mode_sandbox": "read-only",
    "model": "模型-α",
    "effective_model": "有效模型-β",
    "effort": "high",
    "work_nature": "independent verification",
    "write_scope": "none",
    "may_spawn": False,
    "fresh_context": True,
    "effective_tools_capabilities": ["Glob", "Read", "讀取"],
    "mcp_plugins": [],
}
GOLDEN_BOUNDARY_DIGEST = (
    "sha256:67100a2be5d0bf243c0a4bc8d23f84c80d86f14a4954551b7bf01a3e382277c6"
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
    if result["origin_scope"] not in HOST_ORIGIN_SCOPES[result["host"]]:
        raise ContractError("invalid origin_scope for host")
    if result["work_nature"] != INDEPENDENT_VERIFICATION:
        raise ContractError("work_nature must be independent verification")
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
        if source != str(resolved):
            raise ContractError("file source must be its canonical absolute path")
        for component in (resolved,) + tuple(resolved.parents):
            if component.is_symlink():
                raise ContractError("definition source must not contain symlinks")
        if not resolved.is_file():
            raise ContractError("definition source must be a regular file")
        if (
            definition_source != CLAUDE_PLUGIN_DEFINITION_SOURCE
            or resolved != PLUGIN_AGENT
        ):
            raise ContractError(
                "packaged Claude definition source must resolve to the current plugin agent"
            )
        return resolved.read_bytes()
    if source_kind == "host-record":
        return source.encode("utf-8")
    raise ContractError("source_kind must be file or host-record")


def _identity_kind(profile: Mapping[str, Any], source_kind: str) -> str:
    """Validate an exact host/profile/source identity and return its role kind."""
    host = profile["host"]
    origin_scope = profile["origin_scope"]
    profile_id = profile["profile_id"]
    definition_source = profile["definition_source"]
    if host == "codex":
        match = CODEX_PROFILE_RE.fullmatch(profile_id)
        if (
            source_kind != "host-record"
            or match is None
            or definition_source
            != f"host-registry://codex/{origin_scope}/{match.group(1)}"
        ):
            raise ContractError("invalid Codex profile or definition-source identity")
        return "host-record"
    if (
        profile_id == CLAUDE_PROFILE_ID
        and origin_scope == "plugin"
        and definition_source == CLAUDE_PLUGIN_DEFINITION_SOURCE
        and source_kind == "file"
    ):
        return "claude-packaged"
    match = CLAUDE_CUSTOM_PROFILE_RE.fullmatch(profile_id)
    if (
        source_kind != "host-record"
        or match is None
        or origin_scope != match.group(1)
        or definition_source
        != f"host-registry://claude-code/{match.group(1)}/{match.group(2)}"
    ):
        raise ContractError("invalid Claude profile or definition-source identity")
    return "host-record"


def _validate_discovery_receipt(
    receipt: Mapping[str, Any],
    profile: Mapping[str, Any],
    source_digest: str,
    identity_kind: str,
) -> Dict[str, Any]:
    """Validate trusted controller discovery evidence exhaustively.

    The receipt is a capability emitted by an allowed live-host adapter. It is
    not configuration or repository input; callers must preserve that trust
    boundary before invoking this structural validator.
    """
    _require_exact_keys(receipt, DISCOVERY_RECEIPT_FIELDS, "discovery receipt")
    result = {}
    for field in DISCOVERY_RECEIPT_FIELDS - {"host_default"}:
        result[field] = _validate_nfc_string(receipt[field], f"receipt.{field}")
    if type(receipt["host_default"]) is not bool:
        raise ContractError("receipt.host_default must be a boolean")
    result["host_default"] = receipt["host_default"]
    expected_adapter = {
        ("codex", "builtin"): "codex-runtime",
        ("codex", "project"): "codex-runtime",
        ("codex", "user"): "codex-runtime",
        ("claude-code", "plugin"): "claude-plugin-runtime",
        ("claude-code", "project"): "claude-code-runtime",
        ("claude-code", "user"): "claude-code-runtime",
    }[(profile["host"], profile["origin_scope"])]
    if result["adapter"] != expected_adapter:
        raise ContractError("unknown or invalid discovery adapter")
    for field in (
        "host",
        "origin_scope",
        "profile_id",
        "definition_source",
        "effective_model",
    ):
        if result[field] != profile[field]:
            raise ContractError(f"discovery receipt {field} mismatch")
    if result["authoritative_definition_digest"] != source_digest:
        raise ContractError("discovery receipt source digest mismatch")
    if result["host_default"] and profile["origin_scope"] not in {
        "builtin",
        "plugin",
    }:
        raise ContractError("project or user verifier cannot be host default")
    if identity_kind == "claude-packaged" and not result["host_default"]:
        raise ContractError("packaged Claude verifier must be host-declared default")
    return result


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
    profile: Mapping[str, Any],
    source_kind: str,
    source_bytes: bytes,
    identity_kind: str,
) -> None:
    if identity_kind == "claude-packaged":
        fields = _parse_agent_bytes(
            source_bytes, "harness-ship-independent-verifier"
        )
        if (
            profile["model"] != fields["model"]
            or profile["effort"] != fields["effort"]
            or profile["work_nature"] != INDEPENDENT_VERIFICATION
            or profile["effective_tools_capabilities"] != sorted(fields["tools"])
            or profile["may_spawn"]
            or not profile["fresh_context"]
            or profile["mode_sandbox"] != "read-only tools"
            or profile["write_scope"] != "none"
            or profile["mcp_plugins"]
        ):
            raise ContractError("Claude profile boundary disagrees with agent source")
        return

    try:
        record_text = source_bytes.decode("utf-8")
        record = _strict_json_loads(record_text)
    except (UnicodeDecodeError, json.JSONDecodeError, ContractError) as error:
        raise ContractError(f"invalid host registry record: {error}") from error
    _require_exact_keys(record, PROFILE_INPUT_FIELDS, "host registry record")
    canonical_record = json.dumps(
        profile,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if record != profile or record_text != canonical_record:
        raise ContractError("host registry record disagrees with supplied profile")


def build_candidate(
    profile: Mapping[str, Any],
    source_kind: str,
    source: str,
    discovery_receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build a live candidate from authoritative source evidence."""
    _require_exact_keys(profile, PROFILE_INPUT_FIELDS, "candidate profile")
    preliminary = dict(profile)
    preliminary["authoritative_definition_digest"] = "sha256:" + ("0" * 64)
    validated_preliminary = validate_profile(preliminary)
    profile = {
        key: validated_preliminary[key]
        for key in PROFILE_INPUT_FIELDS
    }
    definition_source = _validate_nfc_string(
        profile["definition_source"], "definition_source"
    )
    identity_kind = _identity_kind(profile, source_kind)
    definition_bytes = _source_bytes(source_kind, source, definition_source)
    _validate_source_semantics(profile, source_kind, definition_bytes, identity_kind)
    source_digest = "sha256:" + hashlib.sha256(definition_bytes).hexdigest()
    validated_receipt = _validate_discovery_receipt(
        discovery_receipt, profile, source_digest, identity_kind
    )
    complete = dict(profile)
    complete["authoritative_definition_digest"] = source_digest
    validated = validate_profile(complete)
    binding = dict(validated)
    binding["boundary_digest"] = boundary_digest(validated)
    return {
        "binding": binding,
        "source_kind": source_kind,
        "source": source,
        "discovery_receipt": validated_receipt,
    }


def validate_candidate(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    _require_exact_keys(candidate, CANDIDATE_FIELDS, "candidate")
    binding = validate_binding(candidate["binding"])
    profile = {key: binding[key] for key in PROFILE_FIELDS}
    validated = validate_profile(profile)
    identity_kind = _identity_kind(validated, candidate["source_kind"])
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
    _validate_source_semantics(
        source_profile, candidate["source_kind"], source_bytes, identity_kind
    )
    _validate_discovery_receipt(
        candidate["discovery_receipt"],
        source_profile,
        source_digest,
        identity_kind,
    )
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
    if _boundary_violations(binding, host):
        return False
    if host == "claude-code":
        return _identity_kind(binding, candidate["source_kind"]) in {
            "claude-packaged",
            "host-record",
        }
    return (
        candidate["source_kind"] == "host-record"
        and _identity_kind(binding, candidate["source_kind"]) == "host-record"
    )


def _required_boundary(host: str) -> Dict[str, Any]:
    boundary = HOST_BOUNDARIES[host]
    return {
        "host": host,
        "mode_sandbox": boundary["mode_sandbox"],
        "write_scope": boundary["write_scope"],
        "effort": "high or higher",
        "work_nature": INDEPENDENT_VERIFICATION,
        "may_spawn": False,
        "fresh_context": True,
        "effective_tools_capabilities": deepcopy(
            boundary["effective_tools_capabilities"]
        ),
        "mcp_plugins": [],
    }


def _boundary_violations(
    binding: Mapping[str, Any], expected_host: str
) -> Dict[str, Dict[str, Any]]:
    required = _required_boundary(expected_host)
    violations: Dict[str, Dict[str, Any]] = {}
    exact_fields = (
        "host",
        "mode_sandbox",
        "write_scope",
        "work_nature",
        "may_spawn",
        "fresh_context",
        "effective_tools_capabilities",
        "mcp_plugins",
    )
    for field in exact_fields:
        if binding[field] != required[field]:
            violations[field] = {
                "observed": deepcopy(binding[field]),
                "required": deepcopy(required[field]),
            }
    if binding["effort"].lower() not in HIGH_OR_HIGHER:
        violations["effort"] = {
            "observed": binding["effort"],
            "required": required["effort"],
        }
    return violations


def _boundary_observation(
    binding: Mapping[str, Any], expected_host: str
) -> Dict[str, Any]:
    return {
        "profile_id": binding["profile_id"],
        "definition_source": binding["definition_source"],
        "boundary_digest": binding["boundary_digest"],
        "violations": _boundary_violations(binding, expected_host),
    }


def _unsafe_boundary_fields(
    host: str, observed: Mapping[str, Any]
) -> Dict[str, Any]:
    return {
        "reason_code": "unsafe-verifier-boundary",
        "observed": deepcopy(observed),
        "required": _required_boundary(host),
        "remediation": deepcopy(VERIFIER_REMEDIATION),
    }


def _is_default_candidate(candidate: Mapping[str, Any], host: str) -> bool:
    binding = candidate["binding"]
    if not candidate["discovery_receipt"]["host_default"]:
        return False
    if host == "claude-code":
        return (
            binding["profile_id"] == CLAUDE_PROFILE_ID
            and binding["definition_source"] == CLAUDE_PLUGIN_DEFINITION_SOURCE
        )
    return True


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
    current_host_candidates = []
    for candidate in document["candidates"]:
        try:
            materialized = _materialize_candidate(candidate)
        except (ContractError, OSError, UnicodeError):
            continue
        if materialized["binding"]["host"] == host:
            current_host_candidates.append(materialized)
    profile_ids = [
        candidate["binding"]["profile_id"] for candidate in current_host_candidates
    ]
    definition_sources = [
        candidate["binding"]["definition_source"]
        for candidate in current_host_candidates
    ]
    if len(profile_ids) != len(set(profile_ids)) or len(definition_sources) != len(
        set(definition_sources)
    ):
        return {
            "status": "collision",
            "mutation": False,
            "bindings": result_bindings,
            "global_settings": result_global,
            "actionable": (
                f"Multiple trusted {host} verifier candidates collide on profile "
                "or definition-source identity. Reconcile discovery before setup."
            ),
        }
    safe_candidates = [
        candidate
        for candidate in current_host_candidates
        if _safe_materialized_candidate(candidate, host)
    ]
    unsafe_candidates = [
        candidate
        for candidate in current_host_candidates
        if not _safe_materialized_candidate(candidate, host)
    ]
    explicit = bindings[host]
    binding_absent = explicit is None or explicit == "not-configured"
    if not binding_absent:
        try:
            validated_explicit = validate_binding(explicit)
        except (ContractError, KeyError, TypeError, UnicodeError):
            validated_explicit = None
        if (
            validated_explicit is not None
            and _boundary_violations(validated_explicit, host)
        ):
            return {
                "status": "stale-invalid",
                "mutation": False,
                "bindings": result_bindings,
                "global_settings": result_global,
                "actionable": (
                    "The existing verifier binding has an unsafe effective boundary. "
                    "Follow the ordered remediation without allowing setup to mutate it."
                ),
                **_unsafe_boundary_fields(
                    host,
                    {
                        "persisted": _boundary_observation(
                            validated_explicit, host
                        )
                    },
                ),
            }
        matching = [
            candidate
            for candidate in safe_candidates
            if candidate["binding"] == explicit
        ]
        if matching:
            return {
                "status": "preserved",
                "mutation": False,
                "bindings": result_bindings,
                "global_settings": result_global,
            }
        extra = {}
        if unsafe_candidates:
            extra = _unsafe_boundary_fields(
                host,
                {
                    "candidates": [
                        _boundary_observation(candidate["binding"], host)
                        for candidate in unsafe_candidates
                    ]
                },
            )
        return {
            "status": "stale-invalid",
            "mutation": False,
            "bindings": result_bindings,
            "global_settings": result_global,
            "actionable": (
                f"The existing {host} verifier binding is stale, invalid, or "
                "not matched by authoritative live metadata. Reconcile it explicitly "
                "before setup may select a replacement."
            ),
            **extra,
        }
    valid = [
        candidate
        for candidate in safe_candidates
        if _is_default_candidate(candidate, host)
    ]
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
            "candidates": [
                {
                    "profile_id": candidate["binding"]["profile_id"],
                    "definition_source": candidate["binding"]["definition_source"],
                    "boundary_digest": candidate["binding"]["boundary_digest"],
                }
                for candidate in valid
            ],
        }
    if unsafe_candidates:
        return {
            "status": "missing",
            "mutation": False,
            "bindings": result_bindings,
            "global_settings": result_global,
            "actionable": (
                f"The discovered {host} verifier candidate has an unsafe effective "
                "boundary. Follow the ordered remediation, then rerun setup."
            ),
            **_unsafe_boundary_fields(
                host,
                {
                    "candidates": [
                        _boundary_observation(candidate["binding"], host)
                        for candidate in unsafe_candidates
                    ]
                },
            ),
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


def _config_result(
    original: Any, status: str, actionable: str, **extra: Any
) -> Dict[str, Any]:
    result = {
        "status": status,
        "mutation": False,
        "config_text": original,
        "actionable": actionable,
    }
    result.update(extra)
    return result


def _table_cells(line: str, expected_count: int) -> List[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise ContractError("malformed role binding table row")
    cells = [cell.strip() for cell in stripped[1:-1].split("|")]
    if len(cells) != expected_count or any(not cell for cell in cells):
        raise ContractError("malformed role binding table row")
    return cells


def _config_json_cell(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return rendered.replace("|", "\\u007c")


def _serialize_binding_row(binding: Mapping[str, Any]) -> str:
    validated = validate_binding(binding)
    values = [
        validated["work_nature"],
        validated["profile_id"],
        validated["definition_source"],
        validated["authoritative_definition_digest"],
        validated["mode_sandbox"],
        {
            "declared": validated["model"],
            "effective": validated["effective_model"],
        },
        validated["effort"],
        validated["write_scope"],
        validated["effective_tools_capabilities"],
        validated["mcp_plugins"],
        validated["fresh_context"],
        validated["may_spawn"],
        validated["boundary_digest"],
    ]
    return "  | " + " | ".join(_config_json_cell(value) for value in values) + " |"


def _serialize_binding_section(host: str, binding: Mapping[str, Any]) -> str:
    label = "Codex" if host == "codex" else "Claude Code"
    return (
        f"- **Agent role bindings — {label}:**\n\n"
        f"  {LEGACY_TABLE_HEADER}\n"
        f"  {TABLE_SEPARATOR}\n"
        f"{_serialize_binding_row(binding)}\n"
    )


def _decode_config_cell(cell: str) -> Any:
    try:
        return _strict_json_loads(cell)
    except (json.JSONDecodeError, ContractError) as error:
        raise ContractError(f"malformed canonical role binding cell: {error}") from error


def _derive_origin_scope(
    host: str, profile_id: str, definition_source: str
) -> str:
    if host == "codex":
        profile_match = CODEX_PROFILE_RE.fullmatch(profile_id)
        source_match = re.fullmatch(
            r"host-registry://codex/(builtin|project|user)/"
            r"([A-Za-z0-9][A-Za-z0-9._-]*)",
            definition_source,
        )
        if (
            profile_match is None
            or source_match is None
            or profile_match.group(1) != source_match.group(2)
        ):
            raise ContractError("canonical Codex identity does not encode one origin")
        return source_match.group(1)
    if (
        profile_id == CLAUDE_PROFILE_ID
        and definition_source == CLAUDE_PLUGIN_DEFINITION_SOURCE
    ):
        return "plugin"
    profile_match = CLAUDE_CUSTOM_PROFILE_RE.fullmatch(profile_id)
    source_match = re.fullmatch(
        r"host-registry://claude-code/(project|user)/"
        r"([A-Za-z0-9][A-Za-z0-9._-]*)",
        definition_source,
    )
    if (
        profile_match is None
        or source_match is None
        or profile_match.groups() != source_match.groups()
    ):
        raise ContractError("canonical Claude identity does not encode one origin")
    return source_match.group(1)


def _parse_canonical_binding(cells_raw: List[str], host: str) -> Dict[str, Any]:
    cells = [_decode_config_cell(cell) for cell in cells_raw]
    (
        work_nature,
        profile_id,
        definition_source,
        definition_digest,
        mode_sandbox,
        models,
        effort,
        write_scope,
        tools,
        mcp_plugins,
        fresh_context,
        may_spawn,
        digest,
    ) = cells
    _require_exact_keys(models, {"declared", "effective"}, "canonical Model cell")
    binding = {
        "host": host,
        "origin_scope": _derive_origin_scope(host, profile_id, definition_source),
        "profile_id": profile_id,
        "definition_source": definition_source,
        "authoritative_definition_digest": definition_digest,
        "mode_sandbox": mode_sandbox,
        "model": models["declared"],
        "effective_model": models["effective"],
        "effort": effort,
        "work_nature": work_nature,
        "write_scope": write_scope,
        "may_spawn": may_spawn,
        "fresh_context": fresh_context,
        "effective_tools_capabilities": tools,
        "mcp_plugins": mcp_plugins,
        "boundary_digest": digest,
    }
    return validate_binding(binding)


def _legacy_cell(cell: str) -> str:
    if len(cell) >= 2 and cell[0] == "`" and cell[-1] == "`":
        return cell[1:-1]
    return cell


def _legacy_binding_matches(binding: Mapping[str, Any], cells: List[str]) -> bool:
    values = [_legacy_cell(cell) for cell in cells]
    (
        work_nature,
        profile_id,
        definition_source,
        definition_digest,
        mode_sandbox,
        model,
        effort,
        write_scope,
        tools_text,
        plugins_text,
        fresh_text,
        spawn_text,
        digest,
    ) = values
    host = binding["host"]
    if host == "codex":
        if (
            binding["origin_scope"] != "builtin"
            or profile_id != "Codex/verifier"
            or definition_source != "host-registry://codex/verifier"
        ):
            return False
    else:
        path = Path(definition_source)
        if (
            binding["origin_scope"] != "plugin"
            or profile_id != CLAUDE_PROFILE_ID
            or not path.is_absolute()
            or ".." in path.parts
            or path.parts[-2:]
            != ("agents", "harness-ship-independent-verifier.md")
        ):
            return False
    tools = [] if tools_text == "none" else tools_text.split(", ")
    plugins = [] if plugins_text == "none" else plugins_text.split(", ")
    if fresh_text not in {"true", "false"} or spawn_text not in {"true", "false"}:
        return False
    if model not in {binding["model"], binding["effective_model"]}:
        return False
    legacy_profile = {
        "host": host,
        "profile_id": profile_id,
        "definition_source": definition_source,
        "authoritative_definition_digest": definition_digest,
        "mode_sandbox": mode_sandbox,
        "model": model,
        "effort": effort,
        "work_nature": work_nature,
        "write_scope": write_scope,
        "may_spawn": spawn_text == "true",
        "fresh_context": fresh_text == "true",
        "effective_tools_capabilities": tools,
        "mcp_plugins": plugins,
    }
    legacy_source_profile = dict(legacy_profile)
    del legacy_source_profile["authoritative_definition_digest"]
    if host == "codex":
        legacy_source_bytes = json.dumps(
            legacy_source_profile,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        expected_definition_digest = (
            "sha256:" + hashlib.sha256(legacy_source_bytes).hexdigest()
        )
    else:
        expected_definition_digest = binding["authoritative_definition_digest"]
    expected_boundary_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            legacy_profile,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    expected = [
        binding["work_nature"],
        binding["profile_id"],
        definition_source,
        expected_definition_digest,
        binding["mode_sandbox"],
        model,
        binding["effort"],
        binding["write_scope"],
        ", ".join(binding["effective_tools_capabilities"])
        if binding["effective_tools_capabilities"]
        else "none",
        ", ".join(binding["mcp_plugins"]) if binding["mcp_plugins"] else "none",
        str(binding["fresh_context"]).lower(),
        str(binding["may_spawn"]).lower(),
        expected_boundary_digest,
    ]
    return values == expected


def _parse_binding_table(
    lines: List[str], candidates: List[Mapping[str, Any]], host: str
) -> Dict[str, Any]:
    if len(lines) < 5 or lines[1] != "":
        raise ContractError("role binding table must contain at least one row")
    if lines[2].strip() != LEGACY_TABLE_HEADER:
        raise ContractError("malformed role binding header")
    separator = _table_cells(lines[3], 13)
    if separator != ["---"] * 13:
        raise ContractError("malformed role binding separator")
    rows = []
    verifier_rows = []
    for index, line in enumerate(lines[4:], start=4):
        cells = _table_cells(line, 13)
        rows.append((index, cells))
        work_nature = _legacy_cell(cells[0])
        if work_nature != INDEPENDENT_VERIFICATION:
            try:
                work_nature = _decode_config_cell(cells[0])
            except ContractError:
                pass
        if work_nature == INDEPENDENT_VERIFICATION:
            verifier_rows.append((index, cells))
    if len(verifier_rows) != 1:
        raise ContractError(
            "role binding table must contain exactly one independent verification row"
        )
    row_index, cells = verifier_rows[0]
    try:
        binding = _parse_canonical_binding(cells, host)
        return {"binding": binding, "legacy": False, "row_index": row_index}
    except ContractError:
        pass
    matches = []
    for candidate in candidates:
        try:
            materialized = _materialize_candidate(candidate)
        except (ContractError, OSError, UnicodeError):
            continue
        if (
            materialized["binding"]["host"] == host
            and _legacy_binding_matches(materialized["binding"], cells)
        ):
            matches.append(materialized["binding"])
    if len(matches) != 1:
        raise ContractError(
            "legacy role binding is stale or does not match exactly one trusted candidate"
        )
    return {"binding": matches[0], "legacy": True, "row_index": row_index}


def _reconcile_config_text_v1(
    config_text: Any,
    current_host: str,
    candidates: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Reconcile a Config v1 current-host binding from raw persisted text only."""
    original = config_text
    if isinstance(config_text, bytes):
        try:
            config_text = config_text.decode("utf-8")
        except UnicodeDecodeError:
            return _config_result(
                original, "invalid-config", "Config input must be exact UTF-8."
            )
    if type(config_text) is not str:
        return _config_result(
            original, "invalid-config", "Config input must be exact UTF-8 text."
        )
    if (
        type(current_host) is not str
        or current_host not in HOSTS
        or type(candidates) is not list
    ):
        return _config_result(
            original,
            "invalid-config",
            "Current host and trusted live candidate array are required.",
        )
    try:
        headings = list(
            re.finditer(r"(?m)^## harness-ship[ \t]*$", config_text)
        )
        if len(headings) != 1:
            raise ContractError("expected exactly one ## harness-ship block")
        block_start = headings[0].start()
        next_heading = re.search(
            r"(?m)^## (?!harness-ship(?:[ \t]*$)).*$",
            config_text[headings[0].end() :],
        )
        block_end = (
            headings[0].end() + next_heading.start()
            if next_heading
            else len(config_text)
        )
        block = config_text[block_start:block_end]
        versions = re.findall(
            r"(?m)^- \*\*Config version:\*\* `([^`]+)`[ \t]*$", block
        )
        if versions != ["1"]:
            raise ContractError("unsupported or malformed Config version")
        label = "Codex" if current_host == "codex" else "Claude Code"
        marker = f"- **Agent role bindings — {label}:**"
        marker_matches = list(re.finditer(rf"(?m)^{re.escape(marker)}.*$", block))
        if len(marker_matches) != 1:
            raise ContractError("expected exactly one current-host role section")
        marker_match = marker_matches[0]
        payload_start = block_start + marker_match.start()
        after_marker = block[marker_match.end() :]
        next_field = re.search(r"(?m)^- \*\*[^\n]+$", after_marker)
        payload_end = (
            block_start + marker_match.end() + next_field.start()
            if next_field
            else block_end
        )
        raw_payload = config_text[payload_start:payload_end]
        payload = raw_payload.rstrip("\n")
        lines = payload.splitlines()
        legacy = False
        row_index = None
        if lines == [f"{marker} `not-configured`"]:
            explicit = None
        else:
            if not lines or lines[0] != marker:
                raise ContractError("current-host table marker must be exact")
            parsed_table = _parse_binding_table(lines, candidates, current_host)
            explicit = parsed_table["binding"]
            legacy = parsed_table["legacy"]
            row_index = parsed_table["row_index"]
        other_host = "claude-code" if current_host == "codex" else "codex"
        resolved = resolve_document(
            {
                "current_host": current_host,
                "bindings": {current_host: explicit, other_host: None},
                "candidates": candidates,
                "global_settings": {},
            }
        )
        if resolved["status"] not in {"selected", "preserved"}:
            diagnostic = {
                key: deepcopy(resolved[key])
                for key in (
                    "reason_code",
                    "observed",
                    "required",
                    "remediation",
                )
                if key in resolved
            }
            return _config_result(
                original,
                resolved["status"],
                resolved.get(
                    "actionable",
                    "Reconcile the current-host verifier candidates explicitly.",
                ),
                candidates=resolved.get("candidates", []),
                **diagnostic,
            )
        if resolved["status"] == "preserved" and not legacy:
            return {
                "status": "preserved",
                "mutation": False,
                "config_text": original,
            }
        if legacy:
            payload_lines = raw_payload.splitlines(keepends=True)
            old_row = payload_lines[row_index]
            newline = "\n" if old_row.endswith("\n") else ""
            payload_lines[row_index] = (
                _serialize_binding_row(resolved["bindings"][current_host]) + newline
            )
            replacement = "".join(payload_lines)
        else:
            replacement = _serialize_binding_section(
                current_host, resolved["bindings"][current_host]
            )
        reconciled = (
            config_text[:payload_start] + replacement + config_text[payload_end:]
        )
        return {
            "status": "migrated" if legacy else "selected",
            "mutation": reconciled != config_text,
            "config_text": reconciled,
        }
    except (ContractError, KeyError, TypeError, OSError, UnicodeError) as error:
        return _config_result(original, "invalid-config", str(error))


def _config_block_span(config_text: str) -> tuple:
    headings = list(re.finditer(r"(?m)^## harness-ship[ \t]*$", config_text))
    if len(headings) != 1:
        raise ContractError("expected exactly one ## harness-ship block")
    next_heading = re.search(
        r"(?m)^## (?!harness-ship(?:[ \t]*$)).*$",
        config_text[headings[0].end() :],
    )
    end = (
        headings[0].end() + next_heading.start()
        if next_heading
        else len(config_text)
    )
    return headings[0].start(), end


def _exact_version_field(block: str, label: str) -> List[str]:
    return re.findall(
        rf"(?m)^- \*\*{re.escape(label)}:\*\* `([^`]+)`[ \t]*$",
        block,
    )


def _normalize_config_newlines(config_text: str) -> tuple:
    if "\r" not in config_text:
        return config_text, "\n"
    if re.search(r"\r(?!\n)|(?<!\r)\n", config_text):
        raise ContractError("mixed or malformed config newlines")
    return config_text.replace("\r\n", "\n"), "\r\n"


def _propose_v2_config_text(
    config_text: str,
    current_host: str,
    candidates: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    normalized, newline = _normalize_config_newlines(config_text)
    block_start, block_end = _config_block_span(normalized)
    block = normalized[block_start:block_end]
    plugin_versions = _exact_version_field(block, "Plugin version")
    config_versions = _exact_version_field(block, "Config version")
    binding_versions = _exact_version_field(
        block, "Verifier binding-contract version"
    )
    if config_versions == ["1"] and not plugin_versions and not binding_versions:
        legacy = normalized
        source_version = "1"
    elif (
        plugin_versions == [PLUGIN_VERSION]
        and config_versions == [CONFIG_VERSION]
        and binding_versions == [BINDING_CONTRACT_VERSION]
    ):
        source_version = CONFIG_VERSION
        legacy_block = re.sub(
            r"(?m)^- \*\*Plugin version:\*\* `[^\n]+`\n",
            "",
            block,
            count=1,
        )
        legacy_block = re.sub(
            r"(?m)^- \*\*Verifier binding-contract version:\*\* `[^\n]+`\n",
            "",
            legacy_block,
            count=1,
        )
        legacy_block = re.sub(
            r"(?m)^- \*\*Config version:\*\* `2`[ \t]*$",
            "- **Config version:** `1`",
            legacy_block,
            count=1,
        )
        legacy = normalized[:block_start] + legacy_block + normalized[block_end:]
    else:
        raise ContractError(
            "missing, duplicate, unsupported, or mismatched config version envelope; "
            "Config v1 users must run setup"
        )
    reconciled = _reconcile_config_text_v1(legacy, current_host, candidates)
    if reconciled["status"] not in {"preserved", "selected", "migrated"}:
        return reconciled
    proposed_legacy = reconciled["config_text"]
    proposed_start, proposed_end = _config_block_span(proposed_legacy)
    proposed_block = proposed_legacy[proposed_start:proposed_end]
    envelope = (
        f"- **Plugin version:** `{PLUGIN_VERSION}`\n"
        f"- **Config version:** `{CONFIG_VERSION}`\n"
        f"- **Verifier binding-contract version:** `{BINDING_CONTRACT_VERSION}`"
    )
    proposed_block, substitutions = re.subn(
        r"(?m)^- \*\*Config version:\*\* `1`[ \t]*$",
        envelope,
        proposed_block,
        count=1,
    )
    if substitutions != 1:
        raise ContractError("Config v1 migration source is malformed")
    proposed = (
        proposed_legacy[:proposed_start]
        + proposed_block
        + proposed_legacy[proposed_end:]
    )
    if source_version == CONFIG_VERSION and proposed == normalized:
        status = "preserved"
    else:
        status = "planned"
    if newline == "\r\n":
        proposed = proposed.replace("\n", "\r\n")
    return {
        "status": status,
        "mutation": False,
        "proposed_config": proposed,
    }


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _read_all(fd: int) -> bytes:
    chunks = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _identity(st: os.stat_result) -> Dict[str, int]:
    return {
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode": st.st_mode,
        "links": st.st_nlink,
        "size": st.st_size,
    }


def _open_owned_repo(repo_root: Any) -> tuple:
    if isinstance(repo_root, Path):
        path = repo_root
    elif type(repo_root) is str:
        path = Path(repo_root)
    else:
        raise ContractError("repo_root must be an explicit absolute path")
    if not path.is_absolute():
        raise ContractError("repo_root must be an explicit absolute path")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise ContractError("repo_root must not contain symlinks or aliases")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(str(path), flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISDIR(st.st_mode):
            raise ContractError("repo_root must be a directory")
        if st.st_uid != os.geteuid():
            raise ContractError("repo_root must be owned by the executing user")
        if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise ContractError("repo_root must not be group/world writable")
        return path, fd, st
    except Exception:
        os.close(fd)
        raise


def _open_target(dir_fd: int, basename: Any) -> tuple:
    if type(basename) is not str or basename not in TARGET_BASENAMES:
        raise ContractError("target must be the direct child AGENTS.md or CLAUDE.md")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(basename, flags, dir_fd=dir_fd)
    try:
        st = os.fstat(fd)
        lst = os.stat(basename, dir_fd=dir_fd, follow_symlinks=False)
        if not stat.S_ISREG(st.st_mode) or not stat.S_ISREG(lst.st_mode):
            raise ContractError("target must be a regular file")
        if (st.st_dev, st.st_ino) != (lst.st_dev, lst.st_ino):
            raise ContractError("target identity changed while opening")
        if st.st_nlink != 1:
            raise ContractError("target hard links are not allowed")
        if st.st_uid != os.geteuid():
            raise ContractError("target must be owned by the executing user")
        if st.st_mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX):
            raise ContractError("target has unsupported special permission bits")
        if getattr(st, "st_flags", 0):
            raise ContractError("target has unsupported filesystem flags")
        if hasattr(os, "listxattr") and os.listxattr(fd):
            raise ContractError(
                "target extended attributes/ACL metadata are unsupported"
            )
        return fd, st
    except Exception:
        os.close(fd)
        raise


def _candidate_plan_inputs(candidates: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for candidate in candidates:
        materialized = _materialize_candidate(candidate)
        result.append(
            {
                "binding": materialized["binding"],
                "source_kind": materialized["source_kind"],
                "source_sha256": materialized["binding"][
                    "authoritative_definition_digest"
                ],
            }
        )
    return result


def plan_config_reconciliation(
    repo_root: Any,
    target_basename: str,
    current_host: str,
    candidates: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Return a canonical review plan without mutating the target."""
    dir_fd = target_fd = None
    try:
        repo_path, dir_fd, repo_stat = _open_owned_repo(repo_root)
        target_fd, target_stat = _open_target(dir_fd, target_basename)
        original_bytes = _read_all(target_fd)
        try:
            original_text = original_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ContractError("config target must be exact UTF-8") from error
        proposal = _propose_v2_config_text(
            original_text, current_host, candidates
        )
        if proposal["status"] not in {"planned", "preserved"}:
            return proposal
        proposed_text = proposal["proposed_config"]
        proposed_bytes = proposed_text.encode("utf-8")
        semantic_candidates = _candidate_plan_inputs(candidates)
        diff = "".join(
            difflib.unified_diff(
                original_text.splitlines(keepends=True),
                proposed_text.splitlines(keepends=True),
                fromfile=target_basename,
                tofile=target_basename,
                lineterm="\n",
            )
        )
        plan = {
            "helper_version": HELPER_VERSION,
            "plan_version": PLAN_VERSION,
            "plugin_version": PLUGIN_VERSION,
            "config_version": CONFIG_VERSION,
            "verifier_binding_contract_version": BINDING_CONTRACT_VERSION,
            "repo_root": str(repo_path),
            "target_basename": target_basename,
            "repo_identity": _identity(repo_stat),
            "target_identity": _identity(target_stat),
            "original_sha256": _sha256_bytes(original_bytes),
            "proposed_sha256": _sha256_bytes(proposed_bytes),
            "current_host": current_host,
            "semantic_candidates": semantic_candidates,
            "binding_source_digests": [
                {
                    "boundary_digest": item["binding"]["boundary_digest"],
                    "source_sha256": item["source_sha256"],
                }
                for item in semantic_candidates
            ],
            "operations": (
                []
                if original_bytes == proposed_bytes
                else [
                    {
                        "operation": "replace-file",
                        "target": target_basename,
                        "preserve_mode": stat.S_IMODE(target_stat.st_mode),
                    }
                ]
            ),
            "diff": diff,
        }
        canonical = json.dumps(
            plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        plan_id = "sha256:" + hashlib.sha256(PLAN_DOMAIN + canonical).hexdigest()
        return {
            "status": "preserved" if original_bytes == proposed_bytes else "planned",
            "mutation": False,
            "plan_id": plan_id,
            "plan": plan,
            "proposed_config": proposed_text,
        }
    except (ContractError, KeyError, TypeError, OSError, UnicodeError) as error:
        return {
            "status": "invalid-config",
            "mutation": False,
            "error": str(error),
        }
    finally:
        if target_fd is not None:
            os.close(target_fd)
        if dir_fd is not None:
            os.close(dir_fd)


def _plan_id(plan: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        plan,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(PLAN_DOMAIN + canonical).hexdigest()


def _write_all(fd: int, value: bytes) -> None:
    offset = 0
    while offset < len(value):
        written = os.write(fd, value[offset:])
        if written <= 0:
            raise OSError("incomplete config write")
        offset += written


def _unlink_created(dir_fd: int, name: str, identity: tuple) -> None:
    observed = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    if (observed.st_dev, observed.st_ino) != identity:
        raise ContractError(f"refusing identity-unsafe cleanup of {name}")
    os.unlink(name, dir_fd=dir_fd)


def apply_config_reconciliation(
    repo_root: Any,
    target_basename: str,
    current_host: str,
    candidates: List[Mapping[str, Any]],
    plan: Mapping[str, Any],
    confirmed_plan_id: str,
) -> Dict[str, Any]:
    """Apply only an exactly confirmed plan after fresh target/candidate validation."""
    try:
        supplied_plan_id = _plan_id(plan)
    except (TypeError, ValueError, UnicodeError) as error:
        return {"status": "invalid-plan", "mutation": False, "error": str(error)}
    if type(confirmed_plan_id) is not str or confirmed_plan_id != supplied_plan_id:
        return {
            "status": "confirmation-required",
            "mutation": False,
            "required_plan_id": supplied_plan_id,
        }
    fresh = plan_config_reconciliation(
        repo_root, target_basename, current_host, candidates
    )
    if fresh.get("status") not in {"planned", "preserved"}:
        return fresh
    if fresh["plan_id"] != confirmed_plan_id or fresh["plan"] != plan:
        return {
            "status": "stale-plan",
            "mutation": False,
            "confirmed_plan_id": confirmed_plan_id,
            "fresh_plan_id": fresh["plan_id"],
        }
    if fresh["status"] == "preserved":
        return {
            "status": "preserved",
            "mutation": False,
            "plan_id": confirmed_plan_id,
        }

    dir_fd = target_fd = lock_fd = temp_fd = None
    lock_name = None
    lock_guard_name = ".harness-ship-role-binding.lock"
    temp_name = None
    lock_identity = lock_guard_identity = temp_identity = None
    replaced = False
    cleanup_errors = []
    outcome = None
    try:
        _, dir_fd, repo_stat = _open_owned_repo(repo_root)
        if _identity(repo_stat) != plan["repo_identity"]:
            raise ContractError("repo identity changed after planning")
        target_fd, target_stat = _open_target(dir_fd, target_basename)
        original_bytes = _read_all(target_fd)
        if (
            _identity(target_stat) != plan["target_identity"]
            or _sha256_bytes(original_bytes) != plan["original_sha256"]
        ):
            raise ContractError("target identity or bytes changed after planning")
        proposed_bytes = fresh["proposed_config"].encode("utf-8")
        if _sha256_bytes(proposed_bytes) != plan["proposed_sha256"]:
            raise ContractError("fresh proposed bytes do not match confirmed plan")

        nonce = secrets.token_hex(32)
        creation_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        creation_flags |= getattr(os, "O_NOFOLLOW", 0)
        creation_flags |= getattr(os, "O_CLOEXEC", 0)
        lock_name = f".harness-ship-role-binding.{nonce}.lock"
        lock_fd = os.open(
            lock_name, creation_flags, 0o600, dir_fd=dir_fd
        )
        lock_stat = os.fstat(lock_fd)
        if (
            not stat.S_ISREG(lock_stat.st_mode)
            or lock_stat.st_uid != os.geteuid()
            or lock_stat.st_nlink != 1
        ):
            raise ContractError("new lock entry failed identity validation")
        lock_identity = (lock_stat.st_dev, lock_stat.st_ino)
        _write_all(lock_fd, (nonce + "\n").encode("ascii"))
        os.fsync(lock_fd)
        os.link(
            lock_name,
            lock_guard_name,
            src_dir_fd=dir_fd,
            dst_dir_fd=dir_fd,
            follow_symlinks=False,
        )
        lock_guard_stat = os.stat(
            lock_guard_name, dir_fd=dir_fd, follow_symlinks=False
        )
        if (
            not stat.S_ISREG(lock_guard_stat.st_mode)
            or (lock_guard_stat.st_dev, lock_guard_stat.st_ino) != lock_identity
            or lock_guard_stat.st_uid != os.geteuid()
            or lock_guard_stat.st_nlink != 2
        ):
            raise ContractError("cooperative lock guard failed identity validation")
        lock_guard_identity = lock_identity

        temp_name = f".{target_basename}.harness-ship.{secrets.token_hex(32)}.tmp"
        temp_fd = os.open(
            temp_name, creation_flags, 0o600, dir_fd=dir_fd
        )
        temp_stat = os.fstat(temp_fd)
        temp_identity = (temp_stat.st_dev, temp_stat.st_ino)
        _write_all(temp_fd, proposed_bytes)
        os.fchown(temp_fd, target_stat.st_uid, target_stat.st_gid)
        os.fchmod(temp_fd, stat.S_IMODE(target_stat.st_mode))
        temp_stat = os.fstat(temp_fd)
        if (
            not stat.S_ISREG(temp_stat.st_mode)
            or temp_stat.st_uid != target_stat.st_uid
            or temp_stat.st_gid != target_stat.st_gid
            or temp_stat.st_nlink != 1
            or stat.S_IMODE(temp_stat.st_mode) != stat.S_IMODE(target_stat.st_mode)
        ):
            raise ContractError("new target metadata does not match the original")
        os.fsync(temp_fd)

        observed = os.stat(
            target_basename, dir_fd=dir_fd, follow_symlinks=False
        )
        if (
            (observed.st_dev, observed.st_ino)
            != (target_stat.st_dev, target_stat.st_ino)
            or observed.st_nlink != 1
        ):
            raise ContractError("target changed immediately before replace")
        os.replace(
            temp_name,
            target_basename,
            src_dir_fd=dir_fd,
            dst_dir_fd=dir_fd,
        )
        replaced = True
        temp_name = None
        temp_identity = None
        try:
            os.fsync(dir_fd)
        except OSError as error:
            observed_fd = observed_target = None
            try:
                observed_fd, _ = _open_target(dir_fd, target_basename)
                observed_target = _sha256_bytes(_read_all(observed_fd))
            except (ContractError, OSError):
                observed_target = None
            finally:
                if observed_fd is not None:
                    os.close(observed_fd)
            outcome = {
                "status": "indeterminate",
                "mutation": observed_target == plan["proposed_sha256"],
                "error": f"directory fsync failed after replace: {error}",
                "observed_sha256": observed_target,
                "expected_sha256": plan["proposed_sha256"],
                "plan_id": confirmed_plan_id,
            }
            return outcome
        outcome = {
            "status": "applied",
            "mutation": True,
            "plan_id": confirmed_plan_id,
            "observed_sha256": plan["proposed_sha256"],
        }
        return outcome
    except (ContractError, KeyError, TypeError, OSError, UnicodeError) as error:
        outcome = {
            "status": "indeterminate" if replaced else "apply-failed",
            "mutation": replaced,
            "error": str(error),
            "plan_id": confirmed_plan_id,
        }
        return outcome
    finally:
        for fd_name in ("temp_fd", "lock_fd", "target_fd"):
            fd = locals()[fd_name]
            if fd is not None:
                try:
                    os.close(fd)
                except OSError as error:
                    cleanup_errors.append(f"close {fd_name}: {error}")
        if dir_fd is not None:
            if temp_name is not None and temp_identity is not None:
                try:
                    _unlink_created(dir_fd, temp_name, temp_identity)
                except (ContractError, OSError) as error:
                    cleanup_errors.append(f"temp cleanup: {error}")
            if lock_guard_identity is not None:
                try:
                    _unlink_created(
                        dir_fd, lock_guard_name, lock_guard_identity
                    )
                except (ContractError, OSError) as error:
                    cleanup_errors.append(f"lock guard cleanup: {error}")
            if lock_name is not None and lock_identity is not None:
                try:
                    _unlink_created(dir_fd, lock_name, lock_identity)
                except (ContractError, OSError) as error:
                    cleanup_errors.append(f"lock cleanup: {error}")
            try:
                os.close(dir_fd)
            except OSError as error:
                cleanup_errors.append(f"close dir_fd: {error}")
        if cleanup_errors and outcome is not None:
            outcome["cleanup_errors"] = cleanup_errors
            if outcome["status"] == "applied":
                outcome["status"] = "applied-with-cleanup-error"


def reconcile_config_text(
    config_text: Any,
    current_host: str,
    candidates: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Compatibility surface that cannot produce directly writable config."""
    return _config_result(
        config_text,
        "confirmation-required",
        "Direct reconciliation is disabled; use plan_config_reconciliation, "
        "review its exact plan_id and diff, then use apply_config_reconciliation.",
    )


def _candidate_digest(candidate: Mapping[str, Any]) -> str:
    validated = _materialize_candidate(candidate)
    return validated["binding"]["boundary_digest"]


def preflight_document(document: Mapping[str, Any]) -> Dict[str, Any]:
    """Fail before Phase 0 unless persisted, live, and launch-plan metadata agree."""
    expected = {"versions", "persisted", "live", "launch_plan"}
    try:
        _require_exact_keys(document, expected, "preflight document")
        _require_exact_keys(
            document["versions"], set(VERSION_ENVELOPE), "version envelope"
        )
        if document["versions"] != VERSION_ENVELOPE:
            raise ContractError(
                "helper, plugin, Config, and verifier binding-contract versions "
                "must agree exactly; Config v1 users must run setup"
            )
        if any(
            document[field] is None
            for field in ("persisted", "live", "launch_plan")
        ):
            raise ContractError("persisted, live, and launch metadata are required")
        persisted = validate_binding(document["persisted"])
        live = _materialize_candidate(document["live"])
        launch_plan = _materialize_candidate(document["launch_plan"])
        bindings = {
            "persisted": persisted,
            "live": live["binding"],
            "launch_plan": launch_plan["binding"],
        }
        host = bindings["persisted"]["host"]
        unsafe_observed = {
            source: _boundary_observation(binding, host)
            for source, binding in bindings.items()
            if _boundary_violations(binding, host)
        }
        if unsafe_observed:
            return {
                "status": "fail",
                "before_phase_0": True,
                "mutation": False,
                "error": "unsafe verifier boundary",
                **_unsafe_boundary_fields(host, unsafe_observed),
            }
        digests = {
            field: bindings[field]["boundary_digest"]
            for field in ("persisted", "live", "launch_plan")
        }
        if len(set(digests.values())) != 1 or not (
            bindings["persisted"] == bindings["live"] == bindings["launch_plan"]
        ):
            raise ContractError("persisted, live, and launch metadata mismatch")
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
    versions: Mapping[str, Any] = None,
) -> Dict[str, Any]:
    """Verify actual loaded metadata before trusting verifier output."""
    result = preflight_document(
        {
            "versions": versions,
            "persisted": persisted,
            "live": live,
            "launch_plan": loaded,
        }
    )
    result["post_launch"] = True
    return result


def post_launch_document(document: Mapping[str, Any]) -> Dict[str, Any]:
    _require_exact_keys(
        document, {"versions", "persisted", "live", "loaded"}, "post-launch document"
    )
    if document["versions"] != VERSION_ENVELOPE:
        return {
            "status": "fail",
            "post_launch": True,
            "error": "helper, plugin, Config, and verifier binding-contract versions must agree exactly",
        }
    return reconcile_post_launch(
        document["persisted"],
        document["live"],
        document["loaded"],
        document["versions"],
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
    for command in (
        "resolve",
        "reconcile-config",
        "plan-config",
        "apply-config",
        "preflight",
        "post-launch",
    ):
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
        if args.command == "reconcile-config":
            raise ContractError(
                "reconcile-config cannot apply Config v2; run plan-config, review "
                "its exact plan_id and diff, then run apply-config with confirmation"
            )
        if args.command == "plan-config":
            document = _load_json(args.input)
            _require_exact_keys(document, CONFIG_PLAN_FIELDS, "config plan document")
            result = plan_config_reconciliation(
                document["repo_root"],
                document["target_basename"],
                document["current_host"],
                document["candidates"],
            )
            _emit(result)
            return 0 if result["status"] in {"planned", "preserved"} else 2
        if args.command == "apply-config":
            document = _load_json(args.input)
            _require_exact_keys(
                document, CONFIG_APPLY_FIELDS, "config apply document"
            )
            result = apply_config_reconciliation(
                document["repo_root"],
                document["target_basename"],
                document["current_host"],
                document["candidates"],
                document["plan"],
                document["confirmed_plan_id"],
            )
            _emit(result)
            return 0 if result["status"] in {
                "applied",
                "preserved",
            } else 2
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
