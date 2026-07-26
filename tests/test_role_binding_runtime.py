from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "role_binding_contract.py"
FIXTURES = ROOT / "tests" / "fixtures" / "role_binding"
CONFIG_FIXTURES = FIXTURES / "configs"
PLUGIN_AGENT = (ROOT / "agents" / "harness-ship-independent-verifier.md").resolve()


def load_contract():
    spec = importlib.util.spec_from_file_location("role_binding_contract", HELPER)
    if spec is None or spec.loader is None:
        raise AssertionError("role binding helper is not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(name: str) -> dict:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    rendered = json.dumps(payload).replace("$PLUGIN_AGENT", str(PLUGIN_AGENT))
    return json.loads(rendered)


def canonical_record(profile: dict) -> str:
    return json.dumps(
        profile,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def refresh_receipt(raw: dict, host_default=None) -> None:
    receipt = raw["discovery_receipt"]
    receipt["host"] = raw["profile"]["host"]
    receipt["origin_scope"] = raw["profile"]["origin_scope"]
    receipt["profile_id"] = raw["profile"]["profile_id"]
    receipt["definition_source"] = raw["profile"]["definition_source"]
    receipt["effective_model"] = raw["profile"]["effective_model"]
    source_bytes = (
        Path(raw["source"]).read_bytes()
        if raw["source_kind"] == "file"
        else raw["source"].encode("utf-8")
    )
    receipt["authoritative_definition_digest"] = (
        "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    )
    if host_default is not None:
        receipt["host_default"] = host_default


class RoleBindingRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contract()
        # Legacy parser coverage remains private migration-unit coverage; the
        # public compatibility surface is separately asserted fail-closed.
        self.contract.reconcile_config_text = (
            self.contract._reconcile_config_text_v1
        )

    def candidate(self, name: str, index: int = 0) -> dict:
        raw = fixture(name)["candidates"][index]
        return self.contract.build_candidate(**raw)

    def document(self, name: str) -> dict:
        return fixture(name)

    def config_text(self, name: str) -> str:
        return (CONFIG_FIXTURES / name).read_text(encoding="utf-8")

    def versions(self) -> dict:
        return deepcopy(self.contract.VERSION_ENVELOPE)

    def test_version_envelope_names_verifier_contract_explicitly(self) -> None:
        self.assertIn(
            "verifier_binding_contract_version",
            self.contract.VERSION_ENVELOPE,
        )
        self.assertNotIn("binding_contract_version", self.contract.VERSION_ENVELOPE)

    def test_plan_config_reconciliation_is_non_mutating_v1_to_v2(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir(mode=0o700)
            target = repo / "AGENTS.md"
            original = self.config_text("codex_not_configured.md").encode("utf-8")
            target.write_bytes(original)

            result = self.contract.plan_config_reconciliation(
                repo.resolve(),
                "AGENTS.md",
                "codex",
                fixture("codex.json")["candidates"],
            )

            self.assertEqual(result["status"], "planned")
            self.assertFalse(result["mutation"])
            self.assertEqual(target.read_bytes(), original)
            self.assertIn("- **Plugin version:** `0.7.0`", result["proposed_config"])
            self.assertIn("- **Config version:** `2`", result["proposed_config"])
            self.assertIn(
                "- **Verifier binding-contract version:** `2`",
                result["proposed_config"],
            )
            self.assertRegex(result["plan_id"], r"\Asha256:[0-9a-f]{64}\Z")
            self.assertNotIn("discovery_receipt", repr(result))

    def test_direct_reconciliation_compatibility_cannot_bypass_confirmation(
        self,
    ) -> None:
        public_contract = load_contract()
        original = self.config_text("codex_not_configured.md")
        result = public_contract.reconcile_config_text(
            original, "codex", fixture("codex.json")["candidates"]
        )
        self.assertEqual(result["status"], "confirmation-required")
        self.assertFalse(result["mutation"])
        self.assertEqual(result["config_text"], original)
        self.assertNotIn("proposed_config", result)

    def test_apply_requires_exact_confirmation_and_revalidates_to_noop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            target = repo / "CLAUDE.md"
            original = self.config_text("claude_not_configured.md").encode("utf-8")
            target.write_bytes(original)
            candidates = fixture("claude.json")["candidates"]
            planned = self.contract.plan_config_reconciliation(
                repo, "CLAUDE.md", "claude-code", candidates
            )

            rejected = self.contract.apply_config_reconciliation(
                repo,
                "CLAUDE.md",
                "claude-code",
                candidates,
                planned["plan"],
                "sha256:" + "0" * 64,
            )
            self.assertEqual(rejected["status"], "confirmation-required")
            self.assertFalse(rejected["mutation"])
            self.assertEqual(target.read_bytes(), original)

            applied = self.contract.apply_config_reconciliation(
                repo,
                "CLAUDE.md",
                "claude-code",
                candidates,
                planned["plan"],
                planned["plan_id"],
            )
            self.assertEqual(applied["status"], "applied")
            self.assertTrue(applied["mutation"])
            self.assertEqual(
                hashlib.sha256(target.read_bytes()).hexdigest(),
                planned["plan"]["proposed_sha256"].removeprefix("sha256:"),
            )

            second = self.contract.plan_config_reconciliation(
                repo, "CLAUDE.md", "claude-code", candidates
            )
            self.assertEqual(second["status"], "preserved")
            self.assertEqual(second["plan"]["operations"], [])
            no_op = self.contract.apply_config_reconciliation(
                repo,
                "CLAUDE.md",
                "claude-code",
                candidates,
                second["plan"],
                second["plan_id"],
            )
            self.assertEqual(no_op["status"], "preserved")
            self.assertFalse(no_op["mutation"])

    def test_config_version_envelope_fails_closed_and_preflight_requires_v2(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            target = repo / "AGENTS.md"
            target.write_text(
                self.config_text("codex_not_configured.md"), encoding="utf-8"
            )
            candidates = fixture("codex.json")["candidates"]
            first = self.contract.plan_config_reconciliation(
                repo, "AGENTS.md", "codex", candidates
            )
            applied = self.contract.apply_config_reconciliation(
                repo,
                "AGENTS.md",
                "codex",
                candidates,
                first["plan"],
                first["plan_id"],
            )
            self.assertEqual(applied["status"], "applied")
            valid_v2 = target.read_text(encoding="utf-8")

            malformed = (
                valid_v2.replace("- **Plugin version:** `0.7.0`\n", ""),
                valid_v2.replace(
                    "- **Plugin version:** `0.7.0`",
                    "- **Plugin version:** `0.7.0`\n"
                    "- **Plugin version:** `0.7.0`",
                ),
                valid_v2.replace("- **Config version:** `2`", "- **Config version:** `3`"),
                valid_v2.replace(
                    "- **Verifier binding-contract version:** `2`",
                    "- **Verifier binding-contract version:** `1`",
                ),
            )
            for index, text in enumerate(malformed):
                target.write_text(text, encoding="utf-8")
                with self.subTest(index=index):
                    result = self.contract.plan_config_reconciliation(
                        repo, "AGENTS.md", "codex", candidates
                    )
                    self.assertEqual(result["status"], "invalid-config")
                    self.assertFalse(result["mutation"])

        candidate = self.candidate("codex.json")
        packet = {
            "versions": {
                **self.versions(),
                "config_version": "1",
            },
            "persisted": candidate["binding"],
            "live": deepcopy(candidate),
            "launch_plan": deepcopy(candidate),
        }
        result = self.contract.preflight_document(packet)
        self.assertEqual(result["status"], "fail")
        self.assertIn("run setup", result["error"])

    def test_plan_and_apply_preserve_crlf_without_mixed_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            target = repo / "AGENTS.md"
            original = self.config_text("codex_not_configured.md")
            target.write_bytes(original.replace("\n", "\r\n").encode("utf-8"))
            candidates = fixture("codex.json")["candidates"]
            planned = self.contract.plan_config_reconciliation(
                repo, "AGENTS.md", "codex", candidates
            )
            self.assertEqual(planned["status"], "planned")
            applied = self.contract.apply_config_reconciliation(
                repo,
                "AGENTS.md",
                "codex",
                candidates,
                planned["plan"],
                planned["plan_id"],
            )
            self.assertEqual(applied["status"], "applied")
            output = target.read_bytes()
            self.assertNotIn(b"\n", output.replace(b"\r\n", b""))
            self.assertTrue(output.startswith(b"# Project instructions\r\n"))
            self.assertTrue(
                output.endswith(
                    b"## Other section\r\n\r\nUnrelated suffix stays byte-for-byte.\r\n"
                )
            )

    def test_plan_rejects_symlink_nonregular_hardlink_and_untrusted_repo(self) -> None:
        candidates = fixture("codex.json")["candidates"]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            source = base / "source.md"
            source.write_text(self.config_text("codex_not_configured.md"))
            cases = []
            symlink_repo = base / "symlink-repo"
            symlink_repo.mkdir()
            (symlink_repo / "AGENTS.md").symlink_to(source)
            cases.append(symlink_repo)
            directory_repo = base / "directory-repo"
            directory_repo.mkdir()
            (directory_repo / "AGENTS.md").mkdir()
            cases.append(directory_repo)
            hardlink_repo = base / "hardlink-repo"
            hardlink_repo.mkdir()
            self.contract.os.link(source, hardlink_repo / "AGENTS.md")
            cases.append(hardlink_repo)
            writable_repo = base / "writable-repo"
            writable_repo.mkdir(mode=0o777)
            writable_repo.chmod(0o777)
            (writable_repo / "AGENTS.md").write_bytes(source.read_bytes())
            cases.append(writable_repo)
            for repo in cases:
                with self.subTest(repo=repo.name):
                    result = self.contract.plan_config_reconciliation(
                        repo, "AGENTS.md", "codex", candidates
                    )
                    self.assertEqual(result["status"], "invalid-config")

    def test_apply_rejects_stale_target_and_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            target = repo / "AGENTS.md"
            target.write_text(self.config_text("codex_not_configured.md"))
            candidates = fixture("codex.json")["candidates"]
            planned = self.contract.plan_config_reconciliation(
                repo, "AGENTS.md", "codex", candidates
            )
            target.write_text(target.read_text() + "\nexternal suffix\n")
            stale_target = self.contract.apply_config_reconciliation(
                repo,
                "AGENTS.md",
                "codex",
                candidates,
                planned["plan"],
                planned["plan_id"],
            )
            self.assertEqual(stale_target["status"], "stale-plan")

            target.write_text(self.config_text("codex_not_configured.md"))
            planned = self.contract.plan_config_reconciliation(
                repo, "AGENTS.md", "codex", candidates
            )
            drift = deepcopy(candidates)
            drift[0]["profile"]["effective_model"] = "different-live-model"
            drift[0]["source"] = canonical_record(drift[0]["profile"])
            refresh_receipt(drift[0])
            stale_candidate = self.contract.apply_config_reconciliation(
                repo,
                "AGENTS.md",
                "codex",
                drift,
                planned["plan"],
                planned["plan_id"],
            )
            self.assertEqual(stale_candidate["status"], "stale-plan")

    def test_apply_reports_write_replace_directory_fsync_and_cleanup_failures(
        self,
    ) -> None:
        candidates = fixture("codex.json")["candidates"]

        def arrange(directory):
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            target = repo / "AGENTS.md"
            target.write_text(self.config_text("codex_not_configured.md"))
            planned = self.contract.plan_config_reconciliation(
                repo, "AGENTS.md", "codex", candidates
            )
            return repo, target, planned

        with tempfile.TemporaryDirectory() as directory:
            repo, target, planned = arrange(directory)
            original = target.read_bytes()
            with mock.patch.object(
                self.contract, "_write_all", side_effect=OSError("write failed")
            ):
                result = self.contract.apply_config_reconciliation(
                    repo, "AGENTS.md", "codex", candidates,
                    planned["plan"], planned["plan_id"],
                )
            self.assertEqual(result["status"], "apply-failed")
            self.assertEqual(target.read_bytes(), original)

        with tempfile.TemporaryDirectory() as directory:
            repo, target, planned = arrange(directory)
            original = target.read_bytes()
            with mock.patch.object(
                self.contract.os, "replace", side_effect=OSError("replace failed")
            ):
                result = self.contract.apply_config_reconciliation(
                    repo, "AGENTS.md", "codex", candidates,
                    planned["plan"], planned["plan_id"],
                )
            self.assertEqual(result["status"], "apply-failed")
            self.assertEqual(target.read_bytes(), original)

        with tempfile.TemporaryDirectory() as directory:
            repo, _, planned = arrange(directory)
            real_fsync = self.contract.os.fsync

            def fail_directory_fsync(fd):
                if stat.S_ISDIR(self.contract.os.fstat(fd).st_mode):
                    raise OSError("directory fsync failed")
                return real_fsync(fd)

            with mock.patch.object(
                self.contract.os, "fsync", side_effect=fail_directory_fsync
            ):
                result = self.contract.apply_config_reconciliation(
                    repo, "AGENTS.md", "codex", candidates,
                    planned["plan"], planned["plan_id"],
                )
            self.assertEqual(result["status"], "indeterminate")
            self.assertEqual(
                result["observed_sha256"], planned["plan"]["proposed_sha256"]
            )

        with tempfile.TemporaryDirectory() as directory:
            repo, _, planned = arrange(directory)
            with mock.patch.object(
                self.contract,
                "_unlink_created",
                side_effect=OSError("cleanup failed"),
            ):
                result = self.contract.apply_config_reconciliation(
                    repo, "AGENTS.md", "codex", candidates,
                    planned["plan"], planned["plan_id"],
                )
            self.assertEqual(result["status"], "applied-with-cleanup-error")
            self.assertIn("cleanup_errors", result)

    def test_apply_uses_unpredictable_lock_and_preserves_target_group(self) -> None:
        candidates = fixture("codex.json")["candidates"]
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            target = repo / "AGENTS.md"
            target.write_text(self.config_text("codex_not_configured.md"))
            planned = self.contract.plan_config_reconciliation(
                repo, "AGENTS.md", "codex", candidates
            )
            target_group = target.stat().st_gid
            real_open = self.contract.os.open
            real_fchown = self.contract.os.fchown
            opened_names = []
            chown_calls = []

            def recording_open(path, *args, **kwargs):
                opened_names.append(path)
                return real_open(path, *args, **kwargs)

            def recording_fchown(fd, uid, gid):
                chown_calls.append((uid, gid))
                return real_fchown(fd, uid, gid)

            with (
                mock.patch.object(
                    self.contract.os, "open", side_effect=recording_open
                ),
                mock.patch.object(
                    self.contract.os, "fchown", side_effect=recording_fchown
                ),
            ):
                result = self.contract.apply_config_reconciliation(
                    repo,
                    "AGENTS.md",
                    "codex",
                    candidates,
                    planned["plan"],
                    planned["plan_id"],
                )

            self.assertEqual(result["status"], "applied")
            lock_names = [
                name
                for name in opened_names
                if isinstance(name, str) and name.endswith(".lock")
            ]
            self.assertEqual(len(lock_names), 1)
            self.assertRegex(
                lock_names[0],
                r"\A\.harness-ship-role-binding\.[0-9a-f]{64}\.lock\Z",
            )
            self.assertIn((self.contract.os.geteuid(), target_group), chown_calls)
            self.assertEqual(target.stat().st_gid, target_group)

    def test_apply_fails_closed_when_cooperative_lock_is_held(self) -> None:
        candidates = fixture("codex.json")["candidates"]
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            target = repo / "AGENTS.md"
            target.write_text(self.config_text("codex_not_configured.md"))
            original = target.read_bytes()
            guard = repo / ".harness-ship-role-binding.lock"
            guard.write_text("held by another apply\n", encoding="utf-8")
            planned = self.contract.plan_config_reconciliation(
                repo, "AGENTS.md", "codex", candidates
            )

            result = self.contract.apply_config_reconciliation(
                repo,
                "AGENTS.md",
                "codex",
                candidates,
                planned["plan"],
                planned["plan_id"],
            )

            self.assertEqual(result["status"], "apply-failed")
            self.assertFalse(result["mutation"])
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(
                guard.read_text(encoding="utf-8"),
                "held by another apply\n",
            )
            self.assertEqual(
                list(repo.glob(".harness-ship-role-binding.*.lock")),
                [],
            )

    def test_reconcile_config_populates_only_current_host_and_is_idempotent(
        self,
    ) -> None:
        for config_name, candidate_name, host, other_label in (
            (
                "codex_not_configured.md",
                "codex.json",
                "codex",
                "- **Agent role bindings — Claude Code:** `not-configured`",
            ),
            (
                "claude_not_configured.md",
                "claude.json",
                "claude-code",
                "- **Agent role bindings — Codex:** `not-configured`",
            ),
        ):
            original = self.config_text(config_name)
            result = self.contract.reconcile_config_text(
                original,
                host,
                fixture(candidate_name)["candidates"],
            )
            with self.subTest(host=host):
                self.assertEqual(result["status"], "selected")
                self.assertTrue(result["mutation"])
                self.assertEqual(result["config_text"].count(other_label), 1)
                self.assertIn(self.contract.LEGACY_TABLE_HEADER, result["config_text"])
                self.assertIn('"declared":', result["config_text"])
                self.assertIn('"effective":', result["config_text"])
                current_marker = (
                    "- **Agent role bindings — Codex:**"
                    if host == "codex"
                    else "- **Agent role bindings — Claude Code:**"
                )
                self.assertEqual(
                    result["config_text"].split(current_marker, 1)[0],
                    original.split(current_marker, 1)[0],
                )
                suffix_marker = (
                    "- **Agent role bindings — Claude Code:**"
                    if host == "codex"
                    else "- **Sentinel after bindings:**"
                )
                self.assertEqual(
                    result["config_text"][
                        result["config_text"].index(suffix_marker) :
                    ],
                    original[original.index(suffix_marker) :],
                )
                second = self.contract.reconcile_config_text(
                    result["config_text"],
                    host,
                    fixture(candidate_name)["candidates"],
                )
                self.assertEqual(second["status"], "preserved")
                self.assertFalse(second["mutation"])
                self.assertEqual(second["config_text"], result["config_text"])

    def test_reconcile_config_upgrades_legacy_rows_only_on_one_exact_match(
        self,
    ) -> None:
        for host, candidate_name, config_name in (
            ("codex", "codex.json", "codex_legacy.md"),
            ("claude-code", "claude.json", "claude_legacy.md"),
        ):
            original = self.config_text(config_name)
            candidates = fixture(candidate_name)["candidates"]
            migrated = self.contract.reconcile_config_text(
                original, host, candidates
            )
            with self.subTest(host=host):
                self.assertEqual(migrated["status"], "migrated")
                self.assertTrue(migrated["mutation"])
                self.assertIn(self.contract.LEGACY_TABLE_HEADER, migrated["config_text"])
                self.assertIn('"declared":', migrated["config_text"])
                self.assertIn('"effective":', migrated["config_text"])
                second = self.contract.reconcile_config_text(
                    migrated["config_text"], host, candidates
                )
                self.assertEqual(second["status"], "preserved")
                self.assertEqual(second["config_text"], migrated["config_text"])

                missing = self.contract.reconcile_config_text(original, host, [])
                self.assertFalse(missing["mutation"])
                self.assertEqual(missing["config_text"], original)

                ambiguous = self.contract.reconcile_config_text(
                    original, host, [deepcopy(candidates[0]), deepcopy(candidates[0])]
                )
                self.assertFalse(ambiguous["mutation"])
                self.assertEqual(ambiguous["config_text"], original)

                digest_matches = list(re.finditer(r"sha256:[0-9a-f]{64}", original))
                last_digest = digest_matches[-1]
                replacement = last_digest.group()[:-1] + (
                    "0" if last_digest.group()[-1] != "0" else "1"
                )
                tampered = (
                    original[: last_digest.start()]
                    + replacement
                    + original[last_digest.end() :]
                )
                blocked = self.contract.reconcile_config_text(
                    tampered, host, candidates
                )
                self.assertFalse(blocked["mutation"])
                self.assertEqual(blocked["config_text"], tampered)

    def test_reconcile_config_migrates_only_verifier_in_realistic_multi_role_table(
        self,
    ) -> None:
        original = self.config_text("codex_multi_legacy.md")
        before = (
            "  | narrow lookup | `Codex/scout` | Codex built-in role registry + "
            "active project instructions | unsupported | read-only | `gpt-5.6-luna` | "
            "low | none | unsupported | none | true | false | unsupported |"
        )
        after = (
            "  | security review | `Codex/security_reviewer` | Codex built-in role "
            "registry + active project instructions | unsupported | read-only "
            "trust-boundary analysis | `gpt-5.6-sol` | xhigh | none | unsupported | "
            "none | true | false | unsupported |"
        )

        result = self.contract.reconcile_config_text(
            original, "codex", fixture("codex.json")["candidates"]
        )

        self.assertEqual(result["status"], "migrated")
        self.assertIn(before, result["config_text"])
        self.assertIn(after, result["config_text"])
        self.assertEqual(
            result["config_text"].split(before, 1)[0],
            original.split(before, 1)[0],
        )
        self.assertEqual(
            result["config_text"].split(after, 1)[1],
            original.split(after, 1)[1],
        )
        self.assertEqual(result["config_text"].count(self.contract.LEGACY_TABLE_HEADER), 1)
        second = self.contract.reconcile_config_text(
            result["config_text"], "codex", fixture("codex.json")["candidates"]
        )
        self.assertEqual(second["status"], "preserved")
        self.assertEqual(second["config_text"], result["config_text"])

        canonical = self.config_text("codex_multi_canonical.md")
        preserved = self.contract.reconcile_config_text(
            canonical, "codex", fixture("codex.json")["candidates"]
        )
        self.assertEqual(preserved["status"], "preserved")
        self.assertFalse(preserved["mutation"])
        self.assertEqual(preserved["config_text"], canonical)

    def test_reconcile_config_rejects_legacy_custom_and_builtin_to_user_laundering(
        self,
    ) -> None:
        raw = fixture("codex.json")["candidates"][0]
        raw["profile"]["origin_scope"] = "project"
        raw["profile"]["profile_id"] = "Codex/project-verifier"
        raw["profile"]["definition_source"] = (
            "host-registry://codex/project/project-verifier"
        )
        raw["source"] = canonical_record(raw["profile"])
        refresh_receipt(raw, host_default=False)
        binding = self.contract.build_candidate(**raw)["binding"]

        legacy_profile = {
            field: binding[field]
            for field in self.contract.PROFILE_FIELDS
            if field not in {"origin_scope", "effective_model"}
        }
        legacy_profile["definition_source"] = (
            "host-registry://codex/project-verifier"
        )
        legacy_source_profile = dict(legacy_profile)
        del legacy_source_profile["authoritative_definition_digest"]
        legacy_profile["authoritative_definition_digest"] = (
            "sha256:"
            + hashlib.sha256(
                canonical_record(legacy_source_profile).encode("utf-8")
            ).hexdigest()
        )
        legacy_digest = "sha256:" + hashlib.sha256(
            canonical_record(legacy_profile).encode("utf-8")
        ).hexdigest()
        values = [
            legacy_profile["work_nature"],
            legacy_profile["profile_id"],
            legacy_profile["definition_source"],
            legacy_profile["authoritative_definition_digest"],
            legacy_profile["mode_sandbox"],
            legacy_profile["model"],
            legacy_profile["effort"],
            legacy_profile["write_scope"],
            ", ".join(legacy_profile["effective_tools_capabilities"]),
            "none",
            "true",
            "false",
            legacy_digest,
        ]
        row = "  | " + " | ".join(f"`{value}`" for value in values) + " |"
        marker = "- **Agent role bindings — Codex:** `not-configured`"
        legacy_section = (
            "- **Agent role bindings — Codex:**\n\n"
            f"  {self.contract.LEGACY_TABLE_HEADER}\n"
            f"  {'|' + '---|' * 13}\n"
            f"{row}"
        )
        original = self.config_text("codex_not_configured.md").replace(
            marker, legacy_section
        )

        migrated = self.contract.reconcile_config_text(
            original, "codex", [raw]
        )

        self.assertEqual(migrated["status"], "invalid-config")
        self.assertFalse(migrated["mutation"])
        self.assertEqual(migrated["config_text"], original)

        laundering = fixture("codex.json")["candidates"][0]
        laundering["profile"]["origin_scope"] = "user"
        laundering["profile"]["definition_source"] = (
            "host-registry://codex/user/verifier"
        )
        laundering["source"] = canonical_record(laundering["profile"])
        refresh_receipt(laundering, host_default=False)
        builtin_legacy = self.config_text("codex_legacy.md")
        blocked = self.contract.reconcile_config_text(
            builtin_legacy, "codex", [laundering]
        )
        self.assertEqual(blocked["status"], "invalid-config")
        self.assertFalse(blocked["mutation"])
        self.assertEqual(blocked["config_text"], builtin_legacy)

    def test_reconcile_config_rejects_malformed_text_with_exact_zero_mutation(
        self,
    ) -> None:
        valid = self.config_text("codex_not_configured.md")
        malformed = (
            b"\xffnot-utf8",
            valid.replace("## harness-ship", "## missing"),
            valid + "\n## harness-ship\n",
            valid.replace("`1`", "`2`", 1),
            valid.replace(
                "- **Agent role bindings — Codex:** `not-configured`",
                "",
            ),
            valid.replace(
                "- **Agent role bindings — Codex:** `not-configured`",
                "- **Agent role bindings — Codex:** `not-configured`\n"
                "- **Agent role bindings — Codex:** `not-configured`",
            ),
            valid.replace(
                "- **Agent role bindings — Codex:** `not-configured`",
                "- **Agent role bindings — Codex:**\n\n  | malformed |",
            ),
            valid.replace(
                "- **Agent role bindings — Codex:** `not-configured`",
                "- **Agent role bindings — Codex:** garbage\n\n"
                f"  {load_contract().LEGACY_TABLE_HEADER}\n"
                f"  {'|' + '---|' * 13}",
            ),
            valid.replace(
                "- **Agent role bindings — Codex:** `not-configured`",
                "- **Agent role bindings — Codex:** `not-configured`\n\n"
                f"  {load_contract().LEGACY_TABLE_HEADER}\n"
                f"  {'|' + '---|' * 13}",
            ),
        )
        for raw in malformed:
            result = self.contract.reconcile_config_text(
                raw, "codex", fixture("codex.json")["candidates"]
            )
            with self.subTest(raw=raw):
                self.assertEqual(result["status"], "invalid-config")
                self.assertFalse(result["mutation"])
                self.assertEqual(result["config_text"], raw)

        unhashable_host = self.contract.reconcile_config_text(
            valid, ["codex"], fixture("codex.json")["candidates"]
        )
        self.assertEqual(unhashable_host["status"], "invalid-config")
        self.assertFalse(unhashable_host["mutation"])
        self.assertEqual(unhashable_host["config_text"], valid)

        multi = self.config_text("codex_multi_legacy.md")
        verifier_line = next(
            line
            for line in multi.splitlines()
            if "`independent verification`" in line
        )
        malformed_tables = (
            multi.replace(verifier_line, f"{verifier_line}\n{verifier_line}"),
            multi.replace(verifier_line, ""),
            multi.replace(
                "| narrow lookup |",
                "| narrow lookup | extra |",
                1,
            ),
        )
        for raw in malformed_tables:
            result = self.contract.reconcile_config_text(
                raw, "codex", fixture("codex.json")["candidates"]
            )
            self.assertEqual(result["status"], "invalid-config")
            self.assertFalse(result["mutation"])
            self.assertEqual(result["config_text"], raw)

    def test_reconcile_config_blocked_live_states_preserve_all_raw_text(self) -> None:
        original = self.config_text("codex_not_configured.md")
        default = fixture("codex.json")["candidates"][0]

        second = deepcopy(default)
        second["profile"]["profile_id"] = "Codex/alternate-verifier"
        second["profile"]["definition_source"] = (
            "host-registry://codex/builtin/alternate-verifier"
        )
        second["source"] = canonical_record(second["profile"])
        refresh_receipt(second, host_default=True)
        ambiguous = self.contract.reconcile_config_text(
            original, "codex", [default, second]
        )
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assertFalse(ambiguous["mutation"])
        self.assertEqual(ambiguous["config_text"], original)
        self.assertEqual(len(ambiguous["candidates"]), 2)
        self.assertIn("explicitly", ambiguous["actionable"])

        for candidates, status in (([], "missing"), ([default, deepcopy(default)], "collision")):
            result = self.contract.reconcile_config_text(
                original, "codex", candidates
            )
            with self.subTest(status=status):
                self.assertEqual(result["status"], status)
                self.assertFalse(result["mutation"])
                self.assertEqual(result["config_text"], original)

        reviewer = deepcopy(default)
        reviewer["profile"]["origin_scope"] = "user"
        reviewer["profile"]["profile_id"] = "Codex/security-reviewer"
        reviewer["profile"]["definition_source"] = (
            "host-registry://codex/user/security-reviewer"
        )
        reviewer["source"] = canonical_record(reviewer["profile"])
        refresh_receipt(reviewer, host_default=False)
        result = self.contract.reconcile_config_text(original, "codex", [reviewer])
        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["config_text"], original)

        expanded = self.contract.reconcile_config_text(
            original, "codex", [default]
        )["config_text"]
        drift_fields = {
            "origin_scope": "user",
            "model": "drifted",
            "effective_model": "drifted",
            "effort": "medium",
            "mode_sandbox": "writable",
            "write_scope": "workspace",
            "effective_tools_capabilities": ["Bash", "Glob", "Grep", "Read"],
            "may_spawn": True,
            "fresh_context": False,
            "mcp_plugins": ["plugin"],
        }
        for field, value in drift_fields.items():
            drift = deepcopy(default)
            drift["profile"][field] = value
            drift["source"] = canonical_record(drift["profile"])
            refresh_receipt(drift)
            result = self.contract.reconcile_config_text(expanded, "codex", [drift])
            with self.subTest(field=field):
                self.assertFalse(result["mutation"])
                self.assertEqual(result["config_text"], expanded)

        claude_original = self.config_text("claude_not_configured.md")
        claude_default = fixture("claude.json")["candidates"][0]
        claude_expanded = self.contract.reconcile_config_text(
            claude_original, "claude-code", [claude_default]
        )["config_text"]
        for field, value in drift_fields.items():
            drift = deepcopy(claude_default)
            drift["profile"][field] = value
            refresh_receipt(drift)
            result = self.contract.reconcile_config_text(
                claude_expanded, "claude-code", [drift]
            )
            with self.subTest(host="claude-code", field=field):
                self.assertFalse(result["mutation"])
                self.assertEqual(result["config_text"], claude_expanded)

    def test_valid_explicit_binding_is_preserved_for_both_hosts(self) -> None:
        for name, host in (("claude.json", "claude-code"), ("codex.json", "codex")):
            document = self.document(name)
            document["bindings"][host] = deepcopy(self.candidate(name)["binding"])

            result = self.contract.resolve_document(document)

            self.assertEqual(result["status"], "preserved")
            self.assertFalse(result["mutation"])
            self.assertEqual(result["bindings"], document["bindings"])
            self.assertEqual(result["global_settings"], document["global_settings"])

    def test_single_defaults_are_selected_without_cross_host_or_global_mutation(self) -> None:
        for name, host, other_host in (
            ("claude.json", "claude-code", "codex"),
            ("codex.json", "codex", "claude-code"),
        ):
            document = self.document(name)
            selected = self.candidate(name)
            original_other = deepcopy(document["bindings"][other_host])
            original_global = deepcopy(document["global_settings"])

            result = self.contract.resolve_document(document)

            self.assertEqual(result["status"], "selected")
            self.assertTrue(result["mutation"])
            self.assertEqual(result["bindings"][host], selected["binding"])
            self.assertEqual(result["bindings"][other_host], original_other)
            self.assertEqual(result["global_settings"], original_global)

    def test_ambiguous_and_missing_candidates_fail_without_mutation(self) -> None:
        document = self.document("codex.json")
        second_raw = fixture("codex.json")["candidates"][0]
        second_raw["profile"]["profile_id"] = "Codex/alternate-verifier"
        second_raw["profile"]["definition_source"] = (
            "host-registry://codex/builtin/alternate-verifier"
        )
        second_raw["profile"]["model"] = "alternate-host-assigned-model"
        second_raw["source"] = canonical_record(second_raw["profile"])
        refresh_receipt(second_raw)
        document["candidates"].append(second_raw)
        original = deepcopy(document)

        ambiguous = self.contract.resolve_document(document)
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assertFalse(ambiguous["mutation"])
        self.assertEqual(ambiguous["bindings"], original["bindings"])
        self.assertEqual(ambiguous["global_settings"], original["global_settings"])
        self.assertEqual(len(ambiguous["candidates"]), 2)
        for descriptor in ambiguous["candidates"]:
            self.assertEqual(
                set(descriptor),
                {"profile_id", "definition_source", "boundary_digest"},
            )
        self.assertEqual(
            len(
                {
                    descriptor["boundary_digest"]
                    for descriptor in ambiguous["candidates"]
                }
            ),
            2,
        )

        document["candidates"] = []
        missing = self.contract.resolve_document(document)
        self.assertEqual(missing["status"], "missing")
        self.assertFalse(missing["mutation"])
        self.assertIn("actionable", missing)
        self.assertEqual(missing["bindings"], original["bindings"])

    def test_codex_modes_and_capabilities_use_positive_allowlists(self) -> None:
        for mode in ("not read-only", "read-only writable", "writable read-only"):
            document = self.document("codex.json")
            document["candidates"][0]["profile"]["mode_sandbox"] = mode
            document["candidates"][0]["source"] = canonical_record(
                document["candidates"][0]["profile"]
            )
            refresh_receipt(document["candidates"][0])
            with self.subTest(mode=mode):
                self.assertEqual(
                    self.contract.resolve_document(document)["status"], "missing"
                )

        for capability in ("ApplyPatch", "apply_patch", "InspectAnything"):
            document = self.document("codex.json")
            capabilities = document["candidates"][0]["profile"][
                "effective_tools_capabilities"
            ]
            capabilities.append(capability)
            capabilities.sort()
            document["candidates"][0]["source"] = canonical_record(
                document["candidates"][0]["profile"]
            )
            refresh_receipt(document["candidates"][0])
            with self.subTest(capability=capability):
                persisted = self.contract.build_candidate(
                    **document["candidates"][0]
                )["binding"]
                packet = {
                    "versions": self.versions(),
                    "persisted": persisted,
                    "live": deepcopy(document["candidates"][0]),
                    "launch_plan": deepcopy(document["candidates"][0]),
                }
                self.assertEqual(
                    (
                        self.contract.resolve_document(document)["status"],
                        self.contract.preflight_document(packet)["status"],
                    ),
                    ("missing", "fail"),
                )

    def test_work_nature_is_required_and_other_purposes_fail_closed(self) -> None:
        for name in ("claude.json", "codex.json"):
            raw = fixture(name)["candidates"][0]
            self.assertEqual(
                raw["profile"]["work_nature"], "independent verification"
            )

            missing = deepcopy(raw)
            del missing["profile"]["work_nature"]
            if missing["source_kind"] == "host-record":
                missing["source"] = canonical_record(missing["profile"])
                refresh_receipt(missing)
            document = self.document(name)
            document["candidates"] = [missing]
            self.assertEqual(
                self.contract.resolve_document(document)["status"], "missing"
            )

            other = deepcopy(raw)
            other["profile"]["work_nature"] = "code implementation"
            if other["source_kind"] == "host-record":
                other["source"] = canonical_record(other["profile"])
                refresh_receipt(other)
            document["candidates"] = [other]
            self.assertEqual(
                self.contract.resolve_document(document)["status"], "missing"
            )

    def test_custom_codex_identity_requires_independent_role_and_explicit_binding(
        self,
    ) -> None:
        document = self.document("codex.json")
        candidate = document["candidates"][0]
        candidate["profile"]["profile_id"] = "Codex/arbitrary-purpose"
        candidate["profile"]["definition_source"] = (
            "host-registry://codex/project/arbitrary-purpose"
        )
        candidate["profile"]["origin_scope"] = "project"
        candidate["profile"]["work_nature"] = "deployment"
        candidate["source"] = canonical_record(candidate["profile"])
        refresh_receipt(candidate, host_default=False)

        self.assertEqual(
            self.contract.resolve_document(document)["status"], "missing"
        )

        candidate["profile"]["profile_id"] = "Codex/custom-independent-verifier"
        candidate["profile"]["definition_source"] = (
            "host-registry://codex/project/custom-independent-verifier"
        )
        candidate["profile"]["work_nature"] = "independent verification"
        candidate["source"] = canonical_record(candidate["profile"])
        refresh_receipt(candidate, host_default=False)
        materialized = self.contract.build_candidate(**candidate)
        document["bindings"]["codex"] = deepcopy(materialized["binding"])
        preserved = self.contract.resolve_document(document)
        self.assertEqual(preserved["status"], "preserved")
        self.assertFalse(preserved["mutation"])

        packet = {
            "versions": self.versions(),
            "persisted": materialized["binding"],
            "live": deepcopy(candidate),
            "launch_plan": deepcopy(candidate),
        }
        self.assertEqual(self.contract.preflight_document(packet)["status"], "pass")

    def test_invalid_existing_binding_is_actionable_and_never_replaced(self) -> None:
        for name, host, other_host in (
            ("claude.json", "claude-code", "codex"),
            ("codex.json", "codex", "claude-code"),
        ):
            document = self.document(name)
            document["bindings"][host] = {"stale": "unverifiable"}
            original = deepcopy(document)

            result = self.contract.resolve_document(document)

            self.assertEqual(result["status"], "stale-invalid")
            self.assertFalse(result["mutation"])
            self.assertIn("actionable", result)
            self.assertEqual(result["bindings"], original["bindings"])
            self.assertEqual(
                result["bindings"][other_host], original["bindings"][other_host]
            )
            self.assertEqual(result["global_settings"], original["global_settings"])

    def test_null_and_not_configured_can_select_one_valid_default(self) -> None:
        for name, host in (("claude.json", "claude-code"), ("codex.json", "codex")):
            for absent in (None, "not-configured"):
                document = self.document(name)
                document["bindings"][host] = absent
                result = self.contract.resolve_document(document)
                with self.subTest(name=name, absent=absent):
                    self.assertEqual(result["status"], "selected")
                    self.assertTrue(result["mutation"])

    def test_same_name_wrong_claude_provenance_is_rejected(self) -> None:
        document = self.document("claude.json")
        wrong_raw = fixture("claude.json")["candidates"][0]
        wrong_raw["source_kind"] = "host-record"
        wrong_raw["source"] = '{"name":"harness-ship-independent-verifier"}'
        wrong_raw["profile"]["definition_source"] = (
            "host-registry://claude-code/harness-ship-independent-verifier"
        )
        document["candidates"] = [wrong_raw]

        result = self.contract.resolve_document(document)

        self.assertEqual(result["status"], "missing")
        self.assertFalse(result["mutation"])

        with tempfile.TemporaryDirectory() as directory:
            user_agent = (
                Path(directory) / "harness-ship-independent-verifier.md"
            )
            user_agent.write_bytes(PLUGIN_AGENT.read_bytes())
            wrong_raw = fixture("claude.json")["candidates"][0]
            wrong_raw["source"] = str(user_agent.resolve())
            refresh_receipt(wrong_raw)
            document["candidates"] = [wrong_raw]
            result = self.contract.resolve_document(document)
            self.assertEqual(result["status"], "missing")
            self.assertFalse(result["mutation"])

    def test_claude_candidate_metadata_must_match_one_agent_byte_snapshot(self) -> None:
        raw = fixture("claude.json")["candidates"][0]
        valid_source = PLUGIN_AGENT.read_text(encoding="utf-8")
        tampered_sources = (
            valid_source.replace(
                '"tools":["Read","Grep","Glob"]',
                '"tools":["Read","Grep","Glob"],"memory":"project"',
            ),
            valid_source.replace(
                '"tools":["Read","Grep","Glob"]',
                '"tools":["Read","Bash"]',
            ),
            valid_source.replace('"model":"inherit"', '"model":"unsafe-model"'),
        )

        with tempfile.TemporaryDirectory() as directory:
            for index, source_text in enumerate(tampered_sources):
                path = (
                    Path(directory)
                    / f"candidate-{index}"
                    / "harness-ship-independent-verifier.md"
                )
                path.parent.mkdir()
                path.write_text(source_text, encoding="utf-8")
                candidate = deepcopy(raw)
                candidate["source"] = str(path.resolve())
                with self.subTest(index=index):
                    with mock.patch.object(
                        self.contract, "PLUGIN_AGENT", path.resolve()
                    ):
                        with self.assertRaisesRegex(
                            self.contract.ContractError,
                            "agent|Claude profile boundary",
                        ):
                            self.contract.build_candidate(**candidate)

    def test_codex_record_semantics_must_equal_supplied_profile(self) -> None:
        raw = fixture("codex.json")["candidates"][0]
        self.contract.build_candidate(**raw)

        tampered = deepcopy(raw)
        record = json.loads(tampered["source"])
        record["model"] = "different-model"
        tampered["source"] = json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        with self.assertRaises(self.contract.ContractError):
            self.contract.build_candidate(**tampered)

    def test_resolve_and_preflight_materialize_each_raw_source_once(self) -> None:
        document = self.document("claude.json")
        with mock.patch.object(
            self.contract,
            "_source_bytes",
            wraps=self.contract._source_bytes,
        ) as source_reader:
            self.assertEqual(
                self.contract.resolve_document(document)["status"], "selected"
            )
            self.assertEqual(source_reader.call_count, 1)

        raw = fixture("codex.json")["candidates"][0]
        persisted = self.contract.build_candidate(**raw)["binding"]
        packet = {
            "versions": self.versions(),
            "persisted": persisted,
            "live": deepcopy(raw),
            "launch_plan": deepcopy(raw),
        }
        with mock.patch.object(
            self.contract,
            "_source_bytes",
            wraps=self.contract._source_bytes,
        ) as source_reader:
            self.assertEqual(self.contract.preflight_document(packet)["status"], "pass")
            self.assertEqual(source_reader.call_count, 2)

    def test_preflight_and_post_launch_require_both_hosts_to_match(self) -> None:
        for name in ("claude.json", "codex.json"):
            candidate = self.candidate(name)
            packet = {
                "versions": self.versions(),
                "persisted": candidate["binding"],
                "live": deepcopy(candidate),
                "launch_plan": deepcopy(candidate),
            }
            with self.subTest(name=name, state="match"):
                self.assertEqual(
                    self.contract.preflight_document(packet)["status"], "pass"
                )
                self.assertEqual(
                    self.contract.reconcile_post_launch(
                        candidate["binding"],
                        deepcopy(candidate),
                        deepcopy(candidate),
                        self.versions(),
                    )["status"],
                    "pass",
                )

            drift = deepcopy(packet)
            drift["live"]["binding"]["model"] = "drifted-model"
            with self.subTest(name=name, state="drift"):
                self.assertEqual(
                    self.contract.preflight_document(drift)["status"], "fail"
                )

            missing = deepcopy(packet)
            missing["launch_plan"] = None
            with self.subTest(name=name, state="missing"):
                self.assertEqual(
                    self.contract.preflight_document(missing)["status"], "fail"
                )

    def test_packaged_claude_binding_survives_relocation_but_not_source_drift(
        self,
    ) -> None:
        original_raw = fixture("claude.json")["candidates"][0]
        original = self.contract.build_candidate(**original_raw)
        config = self.contract.reconcile_config_text(
            self.config_text("claude_not_configured.md"),
            "claude-code",
            [original_raw],
        )["config_text"]
        with tempfile.TemporaryDirectory() as directory:
            relocated = (
                Path(directory)
                / "new-plugin-root"
                / "agents"
                / "harness-ship-independent-verifier.md"
            )
            relocated.parent.mkdir(parents=True)
            relocated.write_bytes(PLUGIN_AGENT.read_bytes())
            moved_raw = deepcopy(original_raw)
            moved_raw["source"] = str(relocated.resolve())
            with mock.patch.object(self.contract, "PLUGIN_AGENT", relocated.resolve()):
                moved = self.contract.build_candidate(**moved_raw)
                self.assertEqual(moved["binding"], original["binding"])
                preserved = self.contract.reconcile_config_text(
                    config, "claude-code", [moved_raw]
                )
                self.assertEqual(preserved["status"], "preserved")
                self.assertEqual(preserved["config_text"], config)

                relocated.write_text("tampered", encoding="utf-8")
                with self.assertRaises(self.contract.ContractError):
                    self.contract.build_candidate(**moved_raw)
                blocked = self.contract.reconcile_config_text(
                    config, "claude-code", [moved_raw]
                )
                self.assertFalse(blocked["mutation"])
                self.assertEqual(blocked["config_text"], config)

                relocated.unlink()
                with self.assertRaises(FileNotFoundError):
                    self.contract.build_candidate(**moved_raw)
                blocked = self.contract.reconcile_config_text(
                    config, "claude-code", [moved_raw]
                )
                self.assertFalse(blocked["mutation"])
                self.assertEqual(blocked["config_text"], config)

            renamed = relocated.with_name("renamed-verifier.md")
            renamed.write_bytes(PLUGIN_AGENT.read_bytes())
            moved_raw["source"] = str(renamed.resolve())
            with mock.patch.object(self.contract, "PLUGIN_AGENT", relocated.resolve()):
                with self.assertRaises(self.contract.ContractError):
                    self.contract.build_candidate(**moved_raw)
                blocked = self.contract.reconcile_config_text(
                    config, "claude-code", [moved_raw]
                )
                self.assertFalse(blocked["mutation"])
                self.assertEqual(blocked["config_text"], config)

    def test_explicit_custom_claude_host_record_is_preserved_but_never_default(
        self,
    ) -> None:
        document = self.document("claude.json")
        raw = deepcopy(document["candidates"][0])
        raw["profile"]["profile_id"] = "Claude/project/custom-verifier"
        raw["profile"]["origin_scope"] = "project"
        raw["profile"]["definition_source"] = (
            "host-registry://claude-code/project/custom-verifier"
        )
        raw["profile"]["model"] = "custom-declared-model"
        raw["profile"]["effective_model"] = "custom-effective-model"
        raw["source_kind"] = "host-record"
        raw["source"] = canonical_record(raw["profile"])
        raw["discovery_receipt"]["adapter"] = "claude-code-runtime"
        refresh_receipt(raw, host_default=False)
        custom = self.contract.build_candidate(**raw)
        document["candidates"] = [raw]

        self.assertEqual(self.contract.resolve_document(document)["status"], "missing")
        document["bindings"]["claude-code"] = deepcopy(custom["binding"])
        self.assertEqual(
            self.contract.resolve_document(document)["status"], "preserved"
        )
        packet = {
            "versions": self.versions(),
            "persisted": custom["binding"],
            "live": deepcopy(raw),
            "launch_plan": deepcopy(raw),
        }
        self.assertEqual(self.contract.preflight_document(packet)["status"], "pass")

    def test_discovery_receipts_are_required_exact_and_adapter_scoped(self) -> None:
        for name in ("claude.json", "codex.json"):
            raw = fixture(name)["candidates"][0]
            invalid = []
            missing = deepcopy(raw)
            del missing["discovery_receipt"]
            invalid.append(missing)
            unknown = deepcopy(raw)
            unknown["discovery_receipt"]["adapter"] = "repository-config"
            invalid.append(unknown)
            mismatch = deepcopy(raw)
            mismatch["discovery_receipt"]["effective_model"] = "other-model"
            invalid.append(mismatch)
            origin_mismatch = deepcopy(raw)
            origin_mismatch["discovery_receipt"]["origin_scope"] = "user"
            invalid.append(origin_mismatch)
            wrong_default = deepcopy(raw)
            if name == "claude.json":
                wrong_default["discovery_receipt"]["host_default"] = False
                invalid.append(wrong_default)
            for candidate in invalid:
                document = self.document(name)
                document["candidates"] = [candidate]
                with self.subTest(name=name, candidate=candidate):
                    self.assertEqual(
                        self.contract.resolve_document(document)["status"], "missing"
                    )
                    self.assertFalse(
                        self.contract.resolve_document(document)["mutation"]
                    )

    def test_strict_profile_and_definition_source_grammar_rejects_uri_attacks(
        self,
    ) -> None:
        attacks = {
            "codex.json": (
                (
                    "Codex/verifier/child",
                    "host-registry://codex/builtin/verifier/child",
                ),
                (
                    "Codex/verifier",
                    "host-registry://codex/builtin/verifier?trusted=true",
                ),
                ("Codex/verifier", "host-registry://codex/builtin/../verifier"),
                ("Codex/other", "host-registry://codex/builtin/verifier"),
            ),
            "claude.json": (
                (
                    "harness-ship:harness-ship-independent-verifier/child",
                    "plugin://harness-ship/agents/harness-ship-independent-verifier.md",
                ),
                (
                    "harness-ship:harness-ship-independent-verifier",
                    "plugin://harness-ship/agents/harness-ship-independent-verifier.md#x",
                ),
                (
                    "harness-ship:harness-ship-independent-verifier",
                    "plugin://harness-ship/agents/../agents/harness-ship-independent-verifier.md",
                ),
            ),
        }
        for name, cases in attacks.items():
            for profile_id, definition_source in cases:
                raw = fixture(name)["candidates"][0]
                raw["profile"]["profile_id"] = profile_id
                raw["profile"]["definition_source"] = definition_source
                refresh_receipt(raw)
                document = self.document(name)
                document["candidates"] = [raw]
                with self.subTest(name=name, source=definition_source):
                    result = self.contract.resolve_document(document)
                    self.assertEqual(result["status"], "missing")
                    self.assertFalse(result["mutation"])

        raw = fixture("claude.json")["candidates"][0]
        raw["profile"]["origin_scope"] = "project"
        raw["profile"]["profile_id"] = "Claude/project/custom-verifier"
        raw["profile"]["definition_source"] = (
            "host-registry://claude-code/user/custom-verifier"
        )
        raw["source_kind"] = "host-record"
        raw["source"] = canonical_record(raw["profile"])
        raw["discovery_receipt"]["adapter"] = "claude-code-runtime"
        refresh_receipt(raw, host_default=False)
        document = self.document("claude.json")
        document["candidates"] = [raw]
        self.assertEqual(self.contract.resolve_document(document)["status"], "missing")

    def test_collisions_precede_preserve_and_nondefault_reviewers_are_not_selected(
        self,
    ) -> None:
        for name, host in (("claude.json", "claude-code"), ("codex.json", "codex")):
            document = self.document(name)
            candidate = self.candidate(name)
            document["bindings"][host] = deepcopy(candidate["binding"])
            document["candidates"].append(deepcopy(document["candidates"][0]))
            collision = self.contract.resolve_document(document)
            with self.subTest(name=name):
                self.assertEqual(collision["status"], "collision")
                self.assertFalse(collision["mutation"])
                self.assertIn("actionable", collision)

        for name in ("codex.json", "claude.json"):
            document = self.document(name)
            reviewer = deepcopy(document["candidates"][0])
            reviewer["profile"]["origin_scope"] = "user"
            if name == "codex.json":
                reviewer["profile"]["profile_id"] = "Codex/security-reviewer"
                reviewer["profile"]["definition_source"] = (
                    "host-registry://codex/user/security-reviewer"
                )
            else:
                reviewer["profile"]["profile_id"] = (
                    "Claude/user/security-reviewer"
                )
                reviewer["profile"]["definition_source"] = (
                    "host-registry://claude-code/user/security-reviewer"
                )
                reviewer["source_kind"] = "host-record"
                reviewer["discovery_receipt"]["adapter"] = "claude-code-runtime"
            reviewer["source"] = canonical_record(reviewer["profile"])
            for host_default in (False, True):
                refresh_receipt(reviewer, host_default=host_default)
                document["candidates"] = [deepcopy(reviewer)]
                with self.subTest(name=name, host_default=host_default):
                    result = self.contract.resolve_document(document)
                    self.assertEqual(result["status"], "missing")
                    self.assertFalse(result["mutation"])

    def test_dual_host_boundary_and_effective_model_drift_fail_preflight(self) -> None:
        mutations = {
            "origin_scope": "user",
            "effective_model": "drifted-effective-model",
            "model": "drifted-declared-model",
            "effort": "medium",
            "mode_sandbox": "writable",
            "write_scope": "workspace",
            "may_spawn": True,
            "fresh_context": False,
            "effective_tools_capabilities": ["Bash", "Glob", "Grep", "Read"],
            "mcp_plugins": ["plugin"],
        }
        for name in ("claude.json", "codex.json"):
            original_raw = fixture(name)["candidates"][0]
            persisted = self.contract.build_candidate(**original_raw)["binding"]
            for field, value in mutations.items():
                drift = deepcopy(original_raw)
                drift["profile"][field] = value
                if drift["source_kind"] == "host-record":
                    drift["source"] = canonical_record(drift["profile"])
                refresh_receipt(drift)
                packet = {
                    "versions": self.versions(),
                    "persisted": persisted,
                    "live": drift,
                    "launch_plan": deepcopy(drift),
                }
                with self.subTest(name=name, field=field):
                    self.assertEqual(
                        self.contract.preflight_document(packet)["status"], "fail"
                    )

    def test_unsafe_boundary_diagnostic_is_complete_and_nonmutating(self) -> None:
        original_raw = fixture("codex.json")["candidates"][0]
        safe = self.contract.build_candidate(**original_raw)
        unsafe_raw = deepcopy(original_raw)
        unsafe_raw["profile"]["mode_sandbox"] = "workspace-write"
        unsafe_raw["profile"]["write_scope"] = "workspace"
        unsafe_raw["profile"]["effective_tools_capabilities"] = [
            "Bash",
            "Glob",
            "Grep",
            "Read",
        ]
        unsafe_raw["source"] = canonical_record(unsafe_raw["profile"])
        refresh_receipt(unsafe_raw)
        unsafe = self.contract.build_candidate(**unsafe_raw)

        packets = {
            "persisted": {
                "versions": self.versions(),
                "persisted": unsafe["binding"],
                "live": deepcopy(safe),
                "launch_plan": deepcopy(safe),
            },
            "live": {
                "versions": self.versions(),
                "persisted": safe["binding"],
                "live": deepcopy(unsafe),
                "launch_plan": deepcopy(safe),
            },
            "launch_plan": {
                "versions": self.versions(),
                "persisted": safe["binding"],
                "live": deepcopy(safe),
                "launch_plan": deepcopy(unsafe),
            },
        }
        for source, packet in packets.items():
            with self.subTest(source=source):
                result = self.contract.preflight_document(packet)
                self.assertEqual(result["status"], "fail")
                self.assertEqual(result["reason_code"], "unsafe-verifier-boundary")
                self.assertFalse(result["mutation"])
                self.assertEqual(result["error"], "unsafe verifier boundary")
                self.assertIn(source, result["observed"])
                violations = result["observed"][source]["violations"]
                self.assertIn("mode_sandbox", violations)
                self.assertEqual(
                    result["required"]["mode_sandbox"],
                    "read-only",
                )
                self.assertEqual(
                    result["required"]["effective_tools_capabilities"],
                    ["Glob", "Grep", "Read"],
                )
                self.assertGreaterEqual(len(result["remediation"]), 4)
                remediation = " ".join(result["remediation"]).lower()
                for marker in (
                    "restart",
                    "safe live verifier",
                    "current-host binding",
                    "rerun setup",
                    "rerun preflight",
                ):
                    self.assertIn(marker, remediation)

    def test_setup_reports_unsafe_candidate_without_mutation(self) -> None:
        document = self.document("codex.json")
        unsafe_raw = deepcopy(document["candidates"][0])
        unsafe_raw["profile"]["mode_sandbox"] = "workspace-write"
        unsafe_raw["profile"]["write_scope"] = "workspace"
        unsafe_raw["source"] = canonical_record(unsafe_raw["profile"])
        refresh_receipt(unsafe_raw)
        document["candidates"] = [unsafe_raw]

        result = self.contract.resolve_document(document)

        self.assertEqual(result["status"], "missing")
        self.assertFalse(result["mutation"])
        self.assertEqual(result["reason_code"], "unsafe-verifier-boundary")
        self.assertIn("candidates", result["observed"])
        self.assertEqual(result["required"]["mode_sandbox"], "read-only")
        self.assertIn("rerun setup", " ".join(result["remediation"]).lower())

        original = self.config_text("codex_not_configured.md")
        reconciled = self.contract.reconcile_config_text(
            original,
            "codex",
            [unsafe_raw],
        )
        self.assertEqual(reconciled["status"], "missing")
        self.assertFalse(reconciled["mutation"])
        self.assertEqual(reconciled["config_text"], original)
        self.assertEqual(
            reconciled["reason_code"],
            "unsafe-verifier-boundary",
        )
        self.assertIn("candidates", reconciled["observed"])
        self.assertEqual(
            reconciled["required"]["mode_sandbox"],
            "read-only",
        )
        self.assertIn(
            "rerun preflight",
            " ".join(reconciled["remediation"]).lower(),
        )

    def test_multilingual_boundary_digest_matches_hardcoded_golden(self) -> None:
        golden = fixture("multilingual_golden.json")
        actual = self.contract.boundary_digest(golden["profile"])
        self.assertEqual(actual, golden["expected_boundary_digest"])

    def test_typed_schema_rejects_unknown_missing_wrong_duplicate_and_non_nfc(self) -> None:
        profile = fixture("multilingual_golden.json")["profile"]
        invalid_profiles = []
        unknown = deepcopy(profile)
        unknown["extra"] = "state"
        invalid_profiles.append(unknown)
        missing = deepcopy(profile)
        del missing["model"]
        invalid_profiles.append(missing)
        wrong_type = deepcopy(profile)
        wrong_type["fresh_context"] = "true"
        invalid_profiles.append(wrong_type)
        duplicate = deepcopy(profile)
        duplicate["effective_tools_capabilities"] = ["Read", "Read"]
        invalid_profiles.append(duplicate)
        non_nfc = deepcopy(profile)
        non_nfc["model"] = "mode\u0301l"
        invalid_profiles.append(non_nfc)
        unsorted = deepcopy(profile)
        unsorted["effective_tools_capabilities"] = ["Read", "Glob"]
        invalid_profiles.append(unsorted)

        for invalid in invalid_profiles:
            with self.subTest(invalid=invalid):
                with self.assertRaises(self.contract.ContractError):
                    self.contract.boundary_digest(invalid)

        unsafe_document = self.document("codex.json")
        unsafe_raw = fixture("codex.json")["candidates"][0]
        unsafe_raw["profile"]["effective_tools_capabilities"] = [
            "Bash",
            "Glob",
            "Grep",
            "Read",
        ]
        unsafe_document["candidates"] = [unsafe_raw]
        self.assertEqual(
            self.contract.resolve_document(unsafe_document)["status"], "missing"
        )

    def test_validate_agent_rejects_malformed_json_and_stateful_keys(self) -> None:
        valid = PLUGIN_AGENT.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            malformed = Path(directory) / "malformed.md"
            malformed.write_text("---\n{bad json}\n---\nbody\n", encoding="utf-8")
            extra = Path(directory) / "extra.md"
            extra.write_text(
                valid.replace(
                    '"tools":["Read","Grep","Glob"]',
                    '"tools":["Read","Grep","Glob"],"memory":"project"',
                ),
                encoding="utf-8",
            )
            duplicate = Path(directory) / "duplicate.md"
            duplicate.write_text(
                valid.replace(
                    '"model":"inherit"',
                    '"model":"inherit","model":"inherit"',
                ),
                encoding="utf-8",
            )
            for path in (malformed, extra, duplicate):
                completed = subprocess.run(
                    ["python3", str(HELPER), "validate-agent", str(path)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(completed.returncode, 0, completed.stdout)

    def test_helper_cli_paths_are_available(self) -> None:
        document = self.document("codex.json")
        candidate = self.candidate("codex.json")
        preflight = {
            "versions": self.versions(),
            "persisted": candidate["binding"],
            "live": deepcopy(candidate),
            "launch_plan": deepcopy(candidate),
        }
        post_launch = {
            "versions": self.versions(),
            "persisted": candidate["binding"],
            "live": deepcopy(candidate),
            "loaded": deepcopy(candidate),
        }
        reconcile = {
            "config_text": self.config_text("codex_not_configured.md"),
            "current_host": "codex",
            "candidates": fixture("codex.json")["candidates"],
        }
        with tempfile.TemporaryDirectory() as directory:
            repo = (Path(directory) / "repo").resolve()
            repo.mkdir(mode=0o700)
            (repo / "AGENTS.md").write_text(reconcile["config_text"])
            plan_input = {
                "repo_root": str(repo),
                "target_basename": "AGENTS.md",
                "current_host": "codex",
                "candidates": reconcile["candidates"],
            }
            inputs = {}
            for name, payload in (
                ("resolve", document),
                ("reconcile-config", reconcile),
                ("plan-config", plan_input),
                ("preflight", preflight),
                ("post-launch", post_launch),
            ):
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                inputs[name] = path
            commands = [
                ["python3", str(HELPER), "validate-agent", str(PLUGIN_AGENT)],
                ["python3", str(HELPER), "self-test"],
                [
                    "python3",
                    str(HELPER),
                    "resolve",
                    "--input",
                    str(inputs["resolve"]),
                ],
                [
                    "python3",
                    str(HELPER),
                    "preflight",
                    "--input",
                    str(inputs["preflight"]),
                ],
                [
                    "python3",
                    str(HELPER),
                    "post-launch",
                    "--input",
                    str(inputs["post-launch"]),
                ],
            ]
            for command in commands:
                completed = subprocess.run(
                    command, text=True, capture_output=True, check=False
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

            compatibility = subprocess.run(
                [
                    "python3", str(HELPER), "reconcile-config",
                    "--input", str(inputs["reconcile-config"]),
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(compatibility.returncode, 0)
            self.assertIn("plan-config", compatibility.stderr)

            planned = subprocess.run(
                [
                    "python3", str(HELPER), "plan-config",
                    "--input", str(inputs["plan-config"]),
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            plan_result = json.loads(planned.stdout)
            apply_input = {
                **plan_input,
                "plan": plan_result["plan"],
                "confirmed_plan_id": plan_result["plan_id"],
            }
            apply_path = Path(directory) / "apply-config.json"
            apply_path.write_text(json.dumps(apply_input), encoding="utf-8")
            applied = subprocess.run(
                [
                    "python3", str(HELPER), "apply-config",
                    "--input", str(apply_path),
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)


if __name__ == "__main__":
    unittest.main()
