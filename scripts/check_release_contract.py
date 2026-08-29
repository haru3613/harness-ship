#!/usr/bin/env python3
"""Validate and generate Harness Ship release state.

The PR state machine distinguishes the one-time v0.7.0 bootstrap, normal
source-change PRs, and generated version PRs. This check is not a tamper-proof
authorization boundary; protected branches and attended maintainer review own
merge and publication authority.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Iterable


MANIFESTS = (".codex-plugin/plugin.json", ".claude-plugin/plugin.json")
CATALOGS = (
    ".agents/plugins/marketplace.json",
    ".claude-plugin/marketplace.json",
)
CHANGELOG = "CHANGELOG.md"
POLICY = "release/policy.json"
GENERATED_PATHS = frozenset((*MANIFESTS, *CATALOGS, CHANGELOG, POLICY))
DECLARATION_PREFIX = ".changes/"
DECLARATION_KEYS = {
    "schema_version",
    "id",
    "classification",
    "migration",
    "summary",
    "paths",
}
CLASSIFICATIONS = {"patch", "minor", "breaking"}
MIGRATIONS = {"none", "recommended", "required"}
PRODUCT_DESCRIPTION = (
    "Test and release confidence for AI coding agents: advise the next cuts, plan the "
    "evidence, explore before automating, verify the exact artifact, and keep release "
    "human-owned."
)
PRODUCT_KEYWORDS = [
    "testing",
    "advise",
    "test-planning",
    "exploratory-testing",
    "release-gate",
    "artifact-provenance",
    "qa",
    "evidence",
]
PRODUCT_LONG_DESCRIPTION = (
    "Diagnose a project's test gaps and name the cheapest next cuts, then optionally "
    "create a user-approved Project Test Baseline and Release Delta, explore runnable "
    "features before adding minimum sufficient automation, execute the contract against "
    "an exact candidate, and return an evidence-backed release verdict without "
    "prescribing development or promoting the release."
)
PRODUCT_DEFAULT_PROMPTS = [
    "Set up harness-ship for this repository.",
    "Advise what this project should test next.",
    "Create or update the Test Contract for this project.",
    "Explore this runnable feature before adding the minimum sufficient automated coverage.",
    "Execute the Test Contract against this exact candidate.",
    "Run the release gate for this candidate.",
]
RELEASE_SENSITIVE_EXACT = {
    *GENERATED_PATHS,
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
    "CONTRIBUTING.md",
    "docs/upgrade-guide.md",
    "scripts/check_release_contract.py",
    "scripts/publish_release.py",
    "scripts/validate_plugin_lifecycle.sh",
    "skills/exploratory-testing/SKILL.md",
    "skills/hs-setup/SKILL.md",
}
RELEASE_SENSITIVE_PREFIXES = ("agents/", "skills/")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
TAG_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ReleaseContractError(ValueError):
    """Release metadata or repository state violates the contract."""


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: object, context: str) -> "Version":
        match = SEMVER_RE.fullmatch(raw) if isinstance(raw, str) else None
        if match is None:
            raise ReleaseContractError(f"{context} must be strict three-part semver")
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump(self, classification: str) -> "Version":
        if classification == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        if classification == "minor":
            return Version(self.major, self.minor + 1, 0)
        return Version(self.major + 1, 0, 0)


@dataclass(frozen=True)
class ChangeDeclaration:
    source: str
    identifier: str
    classification: str
    migration: str
    summary: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class ReleasePolicy:
    releases: tuple[tuple[Version, tuple[str, ...]], ...]

    @property
    def current_version(self) -> Version:
        if not self.releases:
            raise ReleaseContractError(f"{POLICY} must record at least one release")
        return self.releases[-1][0]

    @property
    def consumed(self) -> frozenset[str]:
        return frozenset(
            identifier
            for _, identifiers in self.releases
            for identifier in identifiers
        )


def git(repo: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise ReleaseContractError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def resolve_commit(repo: Path, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()


def path_exists_at(repo: Path, ref: str, path: str) -> bool:
    if ref == "WORKTREE":
        return (repo / path).is_file()
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{ref}:{path}"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def read_text_at(repo: Path, ref: str, path: str) -> str:
    if ref == "WORKTREE":
        return (repo / path).read_text(encoding="utf-8")
    return git(repo, "show", f"{ref}:{path}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> object:
    raise ReleaseContractError(f"non-JSON numeric constant: {value}")


def read_json_at(repo: Path, ref: str, path: str) -> object:
    try:
        return json.loads(
            read_text_at(repo, ref, path),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except json.JSONDecodeError as error:
        raise ReleaseContractError(f"{ref}:{path} is not valid JSON") from error


def render_json(payload: object) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def manifest_version(repo: Path, ref: str, path: str) -> Version:
    payload = read_json_at(repo, ref, path)
    if not isinstance(payload, dict) or "version" not in payload:
        raise ReleaseContractError(f"{ref}:{path} must contain version")
    return Version.parse(payload["version"], f"{ref}:{path} version")


def synchronized_version(repo: Path, ref: str) -> Version:
    versions = {manifest_version(repo, ref, path) for path in MANIFESTS}
    if len(versions) != 1:
        raise ReleaseContractError(
            f"{ref} has unsynchronized Codex and Claude plugin versions"
        )
    return versions.pop()


def changed_paths(repo: Path, base: str, current: str) -> list[str]:
    return [
        line
        for line in git(repo, "diff", "--name-only", base, current).splitlines()
        if line
    ]


def is_release_sensitive(path: str) -> bool:
    return path in RELEASE_SENSITIVE_EXACT or path.startswith(
        RELEASE_SENSITIVE_PREFIXES
    )


def declaration_paths(repo: Path, ref: str) -> list[str]:
    if ref == "WORKTREE":
        root = repo / ".changes"
        return (
            sorted(
                str(path.relative_to(repo))
                for path in root.glob("*.json")
                if path.is_file()
            )
            if root.is_dir()
            else []
        )
    return sorted(
        path
        for path in git(
            repo, "ls-tree", "-r", "--name-only", ref, "--", ".changes"
        ).splitlines()
        if path.startswith(DECLARATION_PREFIX) and path.endswith(".json")
    )


def _strict_repo_path(raw: object, source: str) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ReleaseContractError(f"{source} paths must be repository-relative strings")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or str(path) != raw:
        raise ReleaseContractError(f"{source} has unsafe or non-normalized path: {raw}")
    return raw


def load_declarations(
    repo: Path, ref: str, sources: Iterable[str] | None = None
) -> list[ChangeDeclaration]:
    declarations: list[ChangeDeclaration] = []
    identifiers: set[str] = set()
    selected = sorted(sources) if sources is not None else declaration_paths(repo, ref)
    for source in selected:
        payload = read_json_at(repo, ref, source)
        if not isinstance(payload, dict) or set(payload) != DECLARATION_KEYS:
            raise ReleaseContractError(
                f"{source} must contain exactly: {', '.join(sorted(DECLARATION_KEYS))}"
            )
        if payload["schema_version"] != 1:
            raise ReleaseContractError(f"{source} schema_version must be 1")
        identifier = payload["id"]
        if (
            not isinstance(identifier, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9._-]*", identifier) is None
        ):
            raise ReleaseContractError(f"{source} id is invalid")
        if identifier in identifiers:
            raise ReleaseContractError(f"duplicate change declaration id: {identifier}")
        identifiers.add(identifier)
        classification = payload["classification"]
        migration = payload["migration"]
        summary = payload["summary"]
        raw_paths = payload["paths"]
        if classification not in CLASSIFICATIONS:
            raise ReleaseContractError(f"{source} classification is invalid")
        if migration not in MIGRATIONS:
            raise ReleaseContractError(f"{source} migration is invalid")
        if migration == "required" and classification == "patch":
            raise ReleaseContractError(
                f"{source} is underclassified: required migration cannot be patch"
            )
        if not isinstance(summary, str) or not summary.strip():
            raise ReleaseContractError(f"{source} summary must be non-empty")
        if not isinstance(raw_paths, list) or not raw_paths:
            raise ReleaseContractError(f"{source} paths must be a non-empty array")
        paths = tuple(_strict_repo_path(path, source) for path in raw_paths)
        if len(paths) != len(set(paths)):
            raise ReleaseContractError(f"{source} contains duplicate paths")
        declarations.append(
            ChangeDeclaration(
                source,
                identifier,
                classification,
                migration,
                summary.strip(),
                paths,
            )
        )
    return declarations


def validate_coverage(
    changed: Iterable[str],
    declarations: Iterable[ChangeDeclaration],
    *,
    include_generated: bool,
) -> list[ChangeDeclaration]:
    changed_set = set(changed)
    sensitive = sorted(
        path
        for path in changed_set
        if is_release_sensitive(path)
        and (include_generated or path not in GENERATED_PATHS)
    )
    declarations = list(declarations)
    owners: dict[str, list[str]] = {path: [] for path in sensitive}
    for declaration in declarations:
        declared = set(declaration.paths)
        unchanged = sorted(declared - changed_set)
        if unchanged:
            raise ReleaseContractError(
                f"{declaration.source} declares unchanged paths: {', '.join(unchanged)}"
            )
        covered = declared & set(sensitive)
        if not covered:
            raise ReleaseContractError(
                f"{declaration.source} does not cover a release-sensitive changed path"
            )
        for path in covered:
            owners[path].append(declaration.source)
    for path, sources in owners.items():
        if not sources:
            raise ReleaseContractError(
                f"release-sensitive path has no change declaration: {path}"
            )
        if len(sources) > 1:
            raise ReleaseContractError(
                f"release-sensitive path has duplicate declarations: {path} "
                f"({', '.join(sources)})"
            )
    return declarations


def implied_classification(declarations: Iterable[ChangeDeclaration]) -> str:
    ranks = {"patch": 1, "minor": 2, "breaking": 3}
    values = list(declarations)
    if not values:
        raise ReleaseContractError("version PR requires pending declarations")
    return max(values, key=lambda item: ranks[item.classification]).classification


def load_policy(repo: Path, ref: str) -> ReleasePolicy:
    payload = read_json_at(repo, ref, POLICY)
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "releases"}:
        raise ReleaseContractError(
            f"{ref}:{POLICY} must contain exactly schema_version and releases"
        )
    if payload["schema_version"] != 1 or not isinstance(payload["releases"], list):
        raise ReleaseContractError(f"{ref}:{POLICY} has invalid policy schema v1")
    releases: list[tuple[Version, tuple[str, ...]]] = []
    consumed: set[str] = set()
    for index, entry in enumerate(payload["releases"]):
        if not isinstance(entry, dict) or set(entry) != {"version", "declarations"}:
            raise ReleaseContractError(f"{ref}:{POLICY} release {index} is malformed")
        version = Version.parse(entry["version"], f"{ref}:{POLICY} release version")
        identifiers = entry["declarations"]
        if (
            not isinstance(identifiers, list)
            or any(not isinstance(value, str) for value in identifiers)
            or identifiers != sorted(set(identifiers))
        ):
            raise ReleaseContractError(
                f"{ref}:{POLICY} declarations must be sorted and unique"
            )
        duplicate = consumed & set(identifiers)
        if duplicate:
            raise ReleaseContractError(
                f"{ref}:{POLICY} consumes declaration twice: {', '.join(sorted(duplicate))}"
            )
        if releases and version <= releases[-1][0]:
            raise ReleaseContractError(f"{ref}:{POLICY} release versions must increase")
        consumed.update(identifiers)
        releases.append((version, tuple(identifiers)))
    return ReleasePolicy(tuple(releases))


def _remote_source(
    source: object,
    expected_ref: str,
    expected_kind: str,
    context: str,
) -> None:
    if not isinstance(source, dict) or source.get("ref") != expected_ref:
        raise ReleaseContractError(f"{context} must pin ref {expected_ref}")
    kind = source.get("source")
    if kind != expected_kind:
        raise ReleaseContractError(
            f"{context} must use the {expected_kind} source shape"
        )
    if kind == "url":
        if set(source) != {"source", "url", "ref"} or source.get("url") != (
            "https://github.com/haru3613/harness-ship.git"
        ):
            raise ReleaseContractError(
                f"{context} must use the exact official Harness Ship git URL"
            )
    elif kind == "github":
        if set(source) != {"source", "repo", "ref"} or source.get("repo") != (
            "haru3613/harness-ship"
        ):
            raise ReleaseContractError(
                f"{context} must use the exact official Harness Ship GitHub repository"
            )
    else:
        raise ReleaseContractError(
            f"{context} must use a remote url or github source object"
        )


def _catalog_channels(
    payload: object,
    context: str,
    version: Version,
    expected_kind: str,
) -> None:
    if not isinstance(payload, dict) or not isinstance(payload.get("plugins"), list):
        raise ReleaseContractError(f"{context} must contain plugins")
    plugins = payload["plugins"]
    names = [item.get("name") for item in plugins if isinstance(item, dict)]
    if names.count("harness-ship") != 1 or names.count("harness-ship-next") != 1:
        raise ReleaseContractError(
            f"{context} must expose exactly one stable and one next channel"
        )
    by_name = {
        item["name"]: item
        for item in plugins
        if isinstance(item, dict)
        and item.get("name") in {"harness-ship", "harness-ship-next"}
    }
    _remote_source(
        by_name["harness-ship"].get("source"),
        f"v{version}",
        expected_kind,
        f"{context} stable channel",
    )
    _remote_source(
        by_name["harness-ship-next"].get("source"),
        "main",
        expected_kind,
        f"{context} next channel",
    )


def check_version_state(repo: Path, ref: str) -> str:
    if ref != "WORKTREE":
        ref = resolve_commit(repo, ref)
    version = synchronized_version(repo, ref)
    policy = load_policy(repo, ref)
    declared_ids = {
        declaration.identifier for declaration in load_declarations(repo, ref)
    }
    missing_declarations = sorted(policy.consumed - declared_ids)
    if missing_declarations:
        raise ReleaseContractError(
            f"{ref}:{POLICY} consumes missing declarations: "
            f"{', '.join(missing_declarations)}"
        )
    if policy.current_version != version:
        raise ReleaseContractError(
            f"{ref}:{POLICY} current release {policy.current_version} "
            f"does not match manifests {version}"
        )
    for catalog in CATALOGS:
        _catalog_channels(
            read_json_at(repo, ref, catalog),
            f"{ref}:{catalog}",
            version,
            "github" if catalog.startswith(".claude-plugin/") else "url",
        )
    changelog = read_text_at(repo, ref, CHANGELOG)
    heading = re.compile(rf"(?m)^## \[?{re.escape(str(version))}\]?(?:\s|$)")
    if len(heading.findall(changelog)) != 1:
        raise ReleaseContractError(
            f"{ref}:{CHANGELOG} must contain exactly one {version} entry"
        )
    return (
        f"version-state pass: version={version} stable=v{version} next=main "
        f"consumed={len(policy.consumed)}"
    )


def _changed_declarations(changed: Iterable[str]) -> list[str]:
    return sorted(
        path
        for path in changed
        if path.startswith(DECLARATION_PREFIX) and path.endswith(".json")
    )


def check_bootstrap(repo: Path, base: str, current: str, changed: list[str]) -> str:
    if path_exists_at(repo, base, POLICY):
        raise ReleaseContractError("bootstrap is forbidden once base has release policy")
    if not path_exists_at(repo, current, POLICY):
        raise ReleaseContractError("bootstrap must introduce release policy v1")
    sources = _changed_declarations(changed)
    declarations = load_declarations(repo, current, sources)
    if len(declarations) != 1 or declarations[0].identifier != "issue-27":
        raise ReleaseContractError("bootstrap requires exactly issue-27 declaration")
    validate_coverage(changed, declarations, include_generated=True)
    declaration = declarations[0]
    if declaration.classification != "minor":
        raise ReleaseContractError("issue-27 bootstrap must be classified minor")
    base_version = synchronized_version(repo, base)
    current_version = synchronized_version(repo, current)
    if base_version != Version(0, 6, 4) or current_version != Version(0, 7, 0):
        raise ReleaseContractError("bootstrap requires exact version 0.6.4 -> 0.7.0")
    policy = load_policy(repo, current)
    if policy.releases[-1] != (current_version, ("issue-27",)):
        raise ReleaseContractError(
            "bootstrap policy must consume issue-27 in release 0.7.0"
        )
    check_version_state(repo, current)
    return "pr pass: mode=bootstrap version=0.6.4->0.7.0 consumed=issue-27"


def check_normal_change(
    repo: Path, base: str, current: str, changed: list[str]
) -> str:
    if not path_exists_at(repo, current, POLICY):
        raise ReleaseContractError("normal change cannot remove release policy")
    generated = sorted(set(changed) & GENERATED_PATHS)
    if generated:
        raise ReleaseContractError(
            f"normal change PR cannot edit generated release state: {', '.join(generated)}"
        )
    base_policy = load_policy(repo, base)
    current_policy = load_policy(repo, current)
    if current_policy != base_policy:
        raise ReleaseContractError("normal change PR must keep release policy unchanged")
    base_version = synchronized_version(repo, base)
    current_version = synchronized_version(repo, current)
    if current_version != base_version:
        raise ReleaseContractError(
            f"normal change PR must keep version {base_version}; found {current_version}"
        )
    sources = _changed_declarations(changed)
    load_declarations(repo, current)
    declarations = load_declarations(repo, current, sources)
    consumed = sorted(
        item.identifier
        for item in declarations
        if item.identifier in base_policy.consumed
    )
    if consumed:
        raise ReleaseContractError(
            f"change declaration id already consumed: {', '.join(consumed)}"
        )
    validate_coverage(changed, declarations, include_generated=False)
    return (
        f"pr pass: mode=change version={base_version} "
        f"pending={','.join(item.identifier for item in declarations) or 'none'}"
    )


def _pending_declarations(
    repo: Path, ref: str, policy: ReleasePolicy
) -> list[ChangeDeclaration]:
    declarations = load_declarations(repo, ref)
    return sorted(
        (
            declaration
            for declaration in declarations
            if declaration.identifier not in policy.consumed
        ),
        key=lambda item: item.identifier,
    )


def _channel_entry(
    template: dict[str, object], name: str, ref: str, *, claude: bool
) -> dict[str, object]:
    entry = dict(template)
    entry["name"] = name
    entry["source"] = (
        {
            "source": "github",
            "repo": "haru3613/harness-ship",
            "ref": ref,
        }
        if claude
        else {
            "source": "url",
            "url": "https://github.com/haru3613/harness-ship.git",
            "ref": ref,
        }
    )
    if name == "harness-ship-next" and isinstance(entry.get("description"), str):
        description = entry["description"]
        if not description.endswith(" Unstable next channel."):
            entry["description"] = f"{description} Unstable next channel."
    return entry


def expected_generated_state(
    repo: Path, base: str
) -> tuple[Version, list[ChangeDeclaration], dict[str, str]]:
    policy = load_policy(repo, base)
    pending = _pending_declarations(repo, base, policy)
    classification = implied_classification(pending)
    version = policy.current_version.bump(classification)
    expected: dict[str, str] = {}
    for manifest in MANIFESTS:
        payload = read_json_at(repo, base, manifest)
        assert isinstance(payload, dict)
        payload["version"] = str(version)
        payload["description"] = PRODUCT_DESCRIPTION
        payload["keywords"] = PRODUCT_KEYWORDS
        if manifest == ".codex-plugin/plugin.json":
            interface = payload.get("interface")
            if not isinstance(interface, dict):
                interface = {}
                payload["interface"] = interface
            interface["shortDescription"] = "Test and release confidence"
            interface["longDescription"] = PRODUCT_LONG_DESCRIPTION
            interface["defaultPrompt"] = PRODUCT_DEFAULT_PROMPTS
        expected[manifest] = render_json(payload)
    for catalog in CATALOGS:
        payload = read_json_at(repo, base, catalog)
        if not isinstance(payload, dict) or not isinstance(payload.get("plugins"), list):
            raise ReleaseContractError(f"{base}:{catalog} must contain plugins")
        stable = next(
            (
                item
                for item in payload["plugins"]
                if isinstance(item, dict) and item.get("name") == "harness-ship"
            ),
            None,
        )
        if stable is None:
            raise ReleaseContractError(f"{base}:{catalog} has no stable channel")
        unrelated = [
            item
            for item in payload["plugins"]
            if not (
                isinstance(item, dict)
                and item.get("name") in {"harness-ship", "harness-ship-next"}
            )
        ]
        if catalog == ".claude-plugin/marketplace.json":
            payload["description"] = PRODUCT_DESCRIPTION
            stable = dict(stable)
            stable["description"] = PRODUCT_LONG_DESCRIPTION
            stable["keywords"] = PRODUCT_KEYWORDS
        payload["plugins"] = unrelated + [
            _channel_entry(
                stable,
                "harness-ship",
                f"v{version}",
                claude=catalog.startswith(".claude"),
            ),
            _channel_entry(
                stable,
                "harness-ship-next",
                "main",
                claude=catalog.startswith(".claude"),
            ),
        ]
        expected[catalog] = render_json(payload)
    bullets = "\n".join(
        f"- [{item.identifier}] {item.summary} "
        f"(classification: {item.classification}; migration: {item.migration})."
        for item in pending
    )
    entry = f"## {version}\n\n{bullets}\n\n"
    changelog = read_text_at(repo, base, CHANGELOG)
    if changelog.startswith("# Changelog\n"):
        changelog = (
            "# Changelog\n\n"
            + entry
            + changelog[len("# Changelog\n") :].lstrip()
        )
    else:
        changelog = entry + changelog
    expected[CHANGELOG] = changelog
    policy_payload = read_json_at(repo, base, POLICY)
    assert isinstance(policy_payload, dict)
    policy_payload["releases"].append(
        {
            "version": str(version),
            "declarations": [item.identifier for item in pending],
        }
    )
    expected[POLICY] = render_json(policy_payload)
    return version, pending, expected


def check_version_pr(repo: Path, base_ref: str, current_ref: str) -> str:
    base = resolve_commit(repo, base_ref)
    current = resolve_commit(repo, current_ref)
    if not path_exists_at(repo, base, POLICY):
        raise ReleaseContractError("version PR requires policy ledger in base")
    changed = changed_paths(repo, base, current)
    unexpected = sorted(set(changed) - GENERATED_PATHS)
    if unexpected:
        raise ReleaseContractError(
            f"version PR may change only generated release files: {', '.join(unexpected)}"
        )
    version, pending, expected = expected_generated_state(repo, base)
    if set(changed) != set(expected):
        raise ReleaseContractError(
            "version PR must update exactly both manifests, both catalogs, "
            "changelog, and release policy"
        )
    for path, content in expected.items():
        if read_text_at(repo, current, path) != content:
            raise ReleaseContractError(f"version PR has non-generated state: {path}")
    check_version_state(repo, current)
    return (
        f"version-pr pass: {load_policy(repo, base).current_version}->{version} "
        f"consumed={','.join(item.identifier for item in pending)}"
    )


def check_pr(repo: Path, base_ref: str, current_ref: str) -> str:
    base = resolve_commit(repo, base_ref)
    current = resolve_commit(repo, current_ref)
    changed = changed_paths(repo, base, current)
    base_has_policy = path_exists_at(repo, base, POLICY)
    current_has_policy = path_exists_at(repo, current, POLICY)
    if not base_has_policy:
        return check_bootstrap(repo, base, current, changed)
    if not current_has_policy:
        raise ReleaseContractError("release policy cannot be removed")
    if set(changed) & GENERATED_PATHS:
        result = check_version_pr(repo, base, current)
        return result.replace("version-pr pass:", "pr pass: mode=version")
    return check_normal_change(repo, base, current, changed)


def generate_version_state(repo: Path, base_ref: str) -> str:
    base = resolve_commit(repo, base_ref)
    version, pending, expected = expected_generated_state(repo, base)
    for path, content in expected.items():
        destination = repo / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    check_version_state(repo, "WORKTREE")
    return (
        f"version-state generated: version={version} "
        f"consumed={','.join(item.identifier for item in pending)}"
    )


def check_post_merge(
    repo: Path,
    candidate_raw: str,
    main_ref: str,
    tag: str,
    channel: str,
    dry_run: bool,
) -> str:
    if not dry_run:
        raise ReleaseContractError(
            "post-merge contract CLI is validation-only; publication requires "
            "scripts/publish_release.py"
        )
    if channel != "stable":
        raise ReleaseContractError("only the stable channel is publishable")
    candidate = resolve_commit(repo, candidate_raw)
    if candidate_raw != candidate or re.fullmatch(r"[0-9a-f]{40}", candidate_raw) is None:
        raise ReleaseContractError("--candidate must be the full commit SHA")
    intended = resolve_commit(repo, main_ref)
    if candidate != intended:
        raise ReleaseContractError(
            f"candidate is not intended merged main commit: {candidate} != {intended}"
        )
    if TAG_RE.fullmatch(tag) is None:
        raise ReleaseContractError("--tag must be v followed by strict semver")
    state = check_version_state(repo, candidate)
    version = synchronized_version(repo, candidate)
    if tag != f"v{version}":
        raise ReleaseContractError(f"tag {tag} does not match manifest version {version}")
    existing = git(
        repo, "rev-parse", "--verify", f"refs/tags/{tag}^{{}}", check=False
    ).strip()
    if existing and existing != candidate:
        raise ReleaseContractError(
            f"mismatched tag {tag}: existing={existing} candidate={candidate}; "
            "refusing mutation"
        )
    tag_state = "existing-match" if existing else "absent"
    return (
        f"post-merge dry-run pass: channel={channel} tag={tag} sha={candidate} "
        f"versions=codex:{version},claude:{version} tag-state={tag_state}; {state}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("pr", "change-pr", "version-pr"):
        command = commands.add_parser(name)
        command.add_argument("--repo", type=Path, default=Path.cwd())
        command.add_argument("base_ref")
        command.add_argument("current_ref")
    state = commands.add_parser("version-state")
    states = state.add_subparsers(dest="state_command", required=True)
    state_check = states.add_parser("check")
    state_check.add_argument("--repo", type=Path, default=Path.cwd())
    state_check.add_argument("--ref", default="HEAD")
    state_generate = states.add_parser("generate")
    state_generate.add_argument("--repo", type=Path, default=Path.cwd())
    state_generate.add_argument("--base-ref", default="HEAD")
    post = commands.add_parser("post-merge")
    post.add_argument("--repo", type=Path, default=Path.cwd())
    post.add_argument("--candidate", required=True)
    post.add_argument("--main-ref", default="refs/remotes/origin/main")
    post.add_argument("--tag", required=True)
    post.add_argument("--channel", default="stable")
    post.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        repo = args.repo.resolve()
        if args.command == "pr":
            print(check_pr(repo, args.base_ref, args.current_ref))
        elif args.command == "change-pr":
            base = resolve_commit(repo, args.base_ref)
            current = resolve_commit(repo, args.current_ref)
            print(check_normal_change(repo, base, current, changed_paths(repo, base, current)))
        elif args.command == "version-pr":
            print(check_version_pr(repo, args.base_ref, args.current_ref))
        elif args.command == "version-state":
            if args.state_command == "check":
                print(check_version_state(repo, args.ref))
            else:
                print(generate_version_state(repo, args.base_ref))
        else:
            print(
                check_post_merge(
                    repo,
                    args.candidate,
                    args.main_ref,
                    args.tag,
                    args.channel,
                    args.dry_run,
                )
            )
        return 0
    except (OSError, ReleaseContractError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
