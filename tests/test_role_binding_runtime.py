from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "role_binding_contract.py"
FIXTURES = ROOT / "tests" / "fixtures" / "role_binding"
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


class RoleBindingRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contract()

    def candidate(self, name: str, index: int = 0) -> dict:
        raw = fixture(name)["candidates"][index]
        return self.contract.build_candidate(**raw)

    def document(self, name: str) -> dict:
        return fixture(name)

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
            "host-registry://codex/alternate-verifier"
        )
        second_raw["source"] = canonical_record(second_raw["profile"])
        document["candidates"].append(second_raw)
        original = deepcopy(document)

        ambiguous = self.contract.resolve_document(document)
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assertFalse(ambiguous["mutation"])
        self.assertEqual(ambiguous["bindings"], original["bindings"])
        self.assertEqual(ambiguous["global_settings"], original["global_settings"])

        document["candidates"] = []
        missing = self.contract.resolve_document(document)
        self.assertEqual(missing["status"], "missing")
        self.assertFalse(missing["mutation"])
        self.assertIn("actionable", missing)
        self.assertEqual(missing["bindings"], original["bindings"])

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
                candidate["profile"]["definition_source"] = str(path.resolve())
                candidate["source"] = str(path.resolve())
                with self.subTest(index=index):
                    with self.assertRaises(self.contract.ContractError):
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

    def test_preflight_and_post_launch_require_persisted_live_loaded_match(self) -> None:
        candidate = self.candidate("codex.json")
        packet = {
            "persisted": candidate["binding"],
            "live": deepcopy(candidate),
            "launch_plan": deepcopy(candidate),
        }
        self.assertEqual(self.contract.preflight_document(packet)["status"], "pass")
        self.assertEqual(
            self.contract.reconcile_post_launch(
                candidate["binding"], deepcopy(candidate), deepcopy(candidate)
            )["status"],
            "pass",
        )

        drift = deepcopy(packet)
        drift["live"]["binding"]["model"] = "drifted-model"
        self.assertEqual(self.contract.preflight_document(drift)["status"], "fail")

        missing = deepcopy(packet)
        missing["launch_plan"] = None
        self.assertEqual(self.contract.preflight_document(missing)["status"], "fail")

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
            "persisted": candidate["binding"],
            "live": deepcopy(candidate),
            "launch_plan": deepcopy(candidate),
        }
        post_launch = {
            "persisted": candidate["binding"],
            "live": deepcopy(candidate),
            "loaded": deepcopy(candidate),
        }
        with tempfile.TemporaryDirectory() as directory:
            inputs = {}
            for name, payload in (
                ("resolve", document),
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


if __name__ == "__main__":
    unittest.main()
