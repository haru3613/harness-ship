from pathlib import Path
import json
import shutil
import subprocess
import tempfile
from typing import Optional
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_release_contract.py"
PUBLISHER = ROOT / "scripts" / "publish_release.py"


def run(command, cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
    )


class ReleaseContractTests(unittest.TestCase):
    def make_repo(self, directory: str) -> tuple[Path, str]:
        repo = Path(directory)
        run(["git", "init", "-q"], repo)
        run(["git", "config", "user.name", "Harness Ship Test"], repo)
        run(["git", "config", "user.email", "test@example.invalid"], repo)

        for relative in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            ".github/workflows/ci.yml",
            "agents/harness-ship-independent-verifier.md",
            "scripts/role_binding_contract.py",
            "scripts/validate_plugin_lifecycle.sh",
            "skills/setup/SKILL.md",
            "skills/implement/SKILL.md",
        ):
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                if relative.endswith("plugin.json"):
                    payload = {"name": "harness-ship", "version": "0.6.3"}
                else:
                    payload = {
                        "name": "harness-ship",
                        "plugins": [
                            {
                                "name": "harness-ship",
                                "source": {
                                    "source": "url",
                                    "url": "https://github.com/haru3613/harness-ship.git",
                                    "ref": "v0.6.3",
                                },
                            },
                            {
                                "name": "harness-ship-next",
                                "source": {
                                    "source": "url",
                                    "url": "https://github.com/haru3613/harness-ship.git",
                                    "ref": "main",
                                },
                            },
                        ],
                    }
                path.write_text(json.dumps(payload), encoding="utf-8")
            else:
                path.write_text(f"baseline {relative}\n", encoding="utf-8")
        (repo / "CHANGELOG.md").write_text(
            "# Changelog\n\n## 0.6.3\n\n- Baseline.\n", encoding="utf-8"
        )
        (repo / "README.md").write_text("baseline docs\n", encoding="utf-8")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-qm", "base"], repo)
        return repo, run(["git", "rev-parse", "HEAD"], repo).stdout.strip()

    def commit(self, repo: Path, message: str) -> str:
        run(["git", "add", "."], repo)
        run(["git", "commit", "-qm", message], repo)
        return run(["git", "rev-parse", "HEAD"], repo).stdout.strip()

    def declare(
        self,
        repo: Path,
        *,
        paths: list[str],
        classification: str = "patch",
        migration: str = "none",
        identifier: str = "test-change",
    ) -> None:
        declaration = repo / ".changes" / f"{identifier}.json"
        declaration.parent.mkdir(parents=True, exist_ok=True)
        declaration.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "id": identifier,
                    "classification": classification,
                    "migration": migration,
                    "summary": "Test release contract change.",
                    "paths": paths,
                }
            ),
            encoding="utf-8",
        )

    def check(self, repo: Path, base: str, current: str) -> subprocess.CompletedProcess:
        return run(
            [
                "python3",
                str(CHECKER),
                "pr",
                "--repo",
                str(repo),
                base,
                current,
            ],
            ROOT,
            check=False,
        )

    def pr_check(
        self, repo: Path, base: str, current: str
    ) -> subprocess.CompletedProcess:
        return run(
            [
                "python3",
                str(CHECKER),
                "pr",
                "--repo",
                str(repo),
                base,
                current,
            ],
            ROOT,
            check=False,
        )

    def add_policy(
        self,
        repo: Path,
        *,
        version: str = "0.6.3",
        consumed: Optional[list[str]] = None,
    ) -> None:
        path = repo / "release" / "policy.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "releases": [
                        {
                            "version": version,
                            "declarations": consumed or [],
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def normal_base(self, repo: Path) -> str:
        self.add_policy(repo)
        return self.commit(repo, "add release policy")

    def generate_candidate(
        self, repo: Path, *, classification: str = "minor"
    ) -> tuple[str, str]:
        self.normal_base(repo)
        helper = repo / "scripts" / "role_binding_contract.py"
        helper.write_text("pending release change\n", encoding="utf-8")
        self.declare(
            repo,
            paths=["scripts/role_binding_contract.py"],
            classification=classification,
            migration="recommended" if classification != "patch" else "none",
        )
        pending = self.commit(repo, "pending normal change")
        result = run(
            [
                "python3",
                str(CHECKER),
                "version-state",
                "generate",
                "--repo",
                str(repo),
                "--base-ref",
                pending,
            ],
            ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return pending, self.commit(repo, "generated version state")

    def test_protected_contract_change_requires_strict_version_increase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            base = self.normal_base(repo)
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("changed verifier contract\n", encoding="utf-8")
            current = self.commit(repo, "change protected contract")

            result = self.check(repo, base, current)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "release-sensitive path has no change declaration",
                result.stderr.lower(),
            )
            self.assertIn("scripts/role_binding_contract.py", result.stderr)

    def test_normal_change_pr_keeps_released_version_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            self.add_policy(repo)
            base = self.commit(repo, "add release policy")
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("changed verifier contract\n", encoding="utf-8")
            self.declare(repo, paths=["scripts/role_binding_contract.py"])
            current = self.commit(repo, "normal source change")

            result = self.pr_check(repo, base, current)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("mode=change", result.stdout)
            self.assertIn("version=0.6.3", result.stdout)

    def test_direct_version_bump_on_normal_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            base = self.normal_base(repo)
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("changed verifier contract\n", encoding="utf-8")
            for relative in (
                ".codex-plugin/plugin.json",
                ".claude-plugin/plugin.json",
            ):
                path = repo / relative
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["version"] = "0.6.4"
                path.write_text(json.dumps(payload), encoding="utf-8")
            self.declare(
                repo,
                paths=[
                    ".codex-plugin/plugin.json",
                    ".claude-plugin/plugin.json",
                    "scripts/role_binding_contract.py",
                ],
            )
            current = self.commit(repo, "bump and change protected contract")

            result = self.check(repo, base, current)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("version PR may change only generated release files", result.stderr)

    def test_docs_only_change_may_keep_the_same_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            base = self.normal_base(repo)
            (repo / "README.md").write_text("updated docs\n", encoding="utf-8")
            current = self.commit(repo, "docs only")

            result = self.check(repo, base, current)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("mode=change", result.stdout)

    def test_required_migration_cannot_be_underclassified_as_patch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            base = self.normal_base(repo)
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("changed verifier contract\n", encoding="utf-8")
            self.declare(
                repo,
                paths=["scripts/role_binding_contract.py"],
                migration="required",
            )
            current = self.commit(repo, "underclassified change")

            result = self.check(repo, base, current)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("underclassified", result.stderr)

    def test_malformed_change_declaration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            base = self.normal_base(repo)
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("changed verifier contract\n", encoding="utf-8")
            declaration = repo / ".changes" / "broken.json"
            declaration.parent.mkdir(parents=True, exist_ok=True)
            declaration.write_text("{not-json}\n", encoding="utf-8")
            current = self.commit(repo, "malformed declaration")

            result = self.check(repo, base, current)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not valid json", result.stderr.lower())

    def test_duplicate_declaration_coverage_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            base = self.normal_base(repo)
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("changed verifier contract\n", encoding="utf-8")
            self.declare(repo, paths=["scripts/role_binding_contract.py"])
            self.declare(
                repo,
                paths=["scripts/role_binding_contract.py"],
                identifier="other-change",
            )
            current = self.commit(repo, "duplicate coverage")

            result = self.check(repo, base, current)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate declarations", result.stderr)

    def test_version_state_generate_is_idempotent_and_checks_channels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            self.normal_base(repo)
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("pending release change\n", encoding="utf-8")
            self.declare(
                repo,
                paths=["scripts/role_binding_contract.py"],
                classification="minor",
                migration="recommended",
            )
            pending = self.commit(repo, "pending normal change")
            command = [
                "python3",
                str(CHECKER),
                "version-state",
                "generate",
                "--repo",
                str(repo),
                "--base-ref",
                pending,
            ]

            first = run(command, ROOT, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            first_diff = run(["git", "diff"], repo).stdout
            second = run(command, ROOT, check=False)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first_diff, run(["git", "diff"], repo).stdout)

            check_result = run(
                [
                    "python3",
                    str(CHECKER),
                    "version-state",
                    "check",
                    "--repo",
                    str(repo),
                    "--ref",
                    "WORKTREE",
                ],
                ROOT,
                check=False,
            )
            self.assertEqual(check_result.returncode, 0, check_result.stderr)
            self.assertIn("stable=v0.7.0", check_result.stdout)
            self.assertIn("next=main", check_result.stdout)

    def test_version_generation_consumes_all_pending_with_exact_max_bump(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            self.normal_base(repo)
            (repo / "scripts/role_binding_contract.py").write_text(
                "patch source\n", encoding="utf-8"
            )
            (repo / ".github/workflows/ci.yml").write_text(
                "minor source\n", encoding="utf-8"
            )
            self.declare(
                repo,
                paths=["scripts/role_binding_contract.py"],
                identifier="patch-change",
            )
            self.declare(
                repo,
                paths=[".github/workflows/ci.yml"],
                classification="minor",
                migration="required",
                identifier="minor-change",
            )
            pending = self.commit(repo, "two pending declarations")

            result = run(
                [
                    "python3",
                    str(CHECKER),
                    "version-state",
                    "generate",
                    "--repo",
                    str(repo),
                    "--base-ref",
                    pending,
                ],
                ROOT,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("version=0.7.0", result.stdout)
            policy = json.loads(
                (repo / "release/policy.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                policy["releases"][-1],
                {
                    "version": "0.7.0",
                    "declarations": ["minor-change", "patch-change"],
                },
            )
            changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("[minor-change] Test release contract change.", changelog)
            self.assertIn("migration: required", changelog)

    def test_version_pr_accepts_only_exact_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            pending, candidate = self.generate_candidate(repo)

            accepted = run(
                [
                    "python3",
                    str(CHECKER),
                    "version-pr",
                    "--repo",
                    str(repo),
                    pending,
                    candidate,
                ],
                ROOT,
                check=False,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

            (repo / "README.md").write_text("source drift\n", encoding="utf-8")
            drifted = self.commit(repo, "mix source into version PR")
            rejected = run(
                [
                    "python3",
                    str(CHECKER),
                    "version-pr",
                    "--repo",
                    str(repo),
                    pending,
                    drifted,
                ],
                ROOT,
                check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("only generated release files", rejected.stderr)

    def test_already_consumed_declaration_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            self.declare(
                repo,
                paths=["scripts/role_binding_contract.py"],
                identifier="used-change",
            )
            self.add_policy(repo, consumed=["used-change"])
            base = self.commit(repo, "release policy with consumed id")
            (repo / "scripts/role_binding_contract.py").write_text(
                "changed source\n", encoding="utf-8"
            )
            declaration = repo / ".changes" / "used-change.json"
            payload = json.loads(declaration.read_text(encoding="utf-8"))
            payload["summary"] = "Attempted consumed declaration reuse."
            declaration.write_text(json.dumps(payload), encoding="utf-8")
            current = self.commit(repo, "reuse consumed declaration")

            result = self.pr_check(repo, base, current)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already consumed", result.stderr)

    def test_bootstrap_is_one_time_and_requires_policy_consumption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            for manifest in (
                ".codex-plugin/plugin.json",
                ".claude-plugin/plugin.json",
            ):
                payload = json.loads((repo / manifest).read_text(encoding="utf-8"))
                payload["version"] = "0.6.4"
                (repo / manifest).write_text(json.dumps(payload), encoding="utf-8")
            for catalog in (
                ".agents/plugins/marketplace.json",
                ".claude-plugin/marketplace.json",
            ):
                payload = json.loads((repo / catalog).read_text(encoding="utf-8"))
                payload["plugins"][0]["source"]["ref"] = "v0.6.4"
                (repo / catalog).write_text(json.dumps(payload), encoding="utf-8")
            (repo / "CHANGELOG.md").write_text(
                "# Changelog\n\n## 0.6.4\n\n- Baseline.\n", encoding="utf-8"
            )
            base = self.commit(repo, "0.6.4 pre-policy base")

            changed_sensitive = [
                ".codex-plugin/plugin.json",
                ".claude-plugin/plugin.json",
                ".agents/plugins/marketplace.json",
                ".claude-plugin/marketplace.json",
                "CHANGELOG.md",
                "release/policy.json",
                "scripts/role_binding_contract.py",
            ]
            for manifest in (
                ".codex-plugin/plugin.json",
                ".claude-plugin/plugin.json",
            ):
                payload = json.loads((repo / manifest).read_text(encoding="utf-8"))
                payload["version"] = "0.7.0"
                (repo / manifest).write_text(json.dumps(payload), encoding="utf-8")
            for catalog in (
                ".agents/plugins/marketplace.json",
                ".claude-plugin/marketplace.json",
            ):
                payload = json.loads((repo / catalog).read_text(encoding="utf-8"))
                payload["plugins"][0]["source"]["ref"] = "v0.7.0"
                (repo / catalog).write_text(json.dumps(payload), encoding="utf-8")
            (repo / "CHANGELOG.md").write_text(
                "# Changelog\n\n## 0.7.0\n\n- Bootstrap.\n\n"
                "## 0.6.4\n\n- Baseline.\n",
                encoding="utf-8",
            )
            self.add_policy(repo, version="0.7.0", consumed=["issue-27"])
            (repo / "scripts/role_binding_contract.py").write_text(
                "bootstrap source\n", encoding="utf-8"
            )
            self.declare(
                repo,
                paths=changed_sensitive,
                classification="minor",
                migration="required",
                identifier="issue-27",
            )
            bootstrap = self.commit(repo, "one-time bootstrap")

            accepted = self.pr_check(repo, base, bootstrap)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertIn("mode=bootstrap", accepted.stdout)

            (repo / "release/policy.json").unlink()
            after_policy = self.commit(repo, "attempt bootstrap after policy")
            rejected = self.pr_check(repo, bootstrap, after_policy)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertNotIn("mode=bootstrap", rejected.stdout)

    def test_post_merge_dry_run_rejects_mismatched_existing_tag_without_mutation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, old = self.make_repo(directory)
            run(["git", "branch", "-M", "main"], repo)
            run(["git", "tag", "v0.7.0", old], repo)
            _, candidate = self.generate_candidate(repo)

            result = run(
                [
                    "python3",
                    str(CHECKER),
                    "post-merge",
                    "--repo",
                    str(repo),
                    "--candidate",
                    candidate,
                    "--main-ref",
                    "refs/heads/main",
                    "--tag",
                    "v0.7.0",
                    "--dry-run",
                ],
                ROOT,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mismatched tag", result.stderr)
            self.assertEqual(
                run(["git", "rev-parse", "v0.7.0^{}"], repo).stdout.strip(), old
            )

    def test_post_merge_dry_run_emits_exact_provenance_without_creating_tag(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, _ = self.make_repo(directory)
            run(["git", "branch", "-M", "main"], repo)
            _, candidate = self.generate_candidate(repo)

            result = run(
                [
                    "python3",
                    str(CHECKER),
                    "post-merge",
                    "--repo",
                    str(repo),
                    "--candidate",
                    candidate,
                    "--main-ref",
                    "refs/heads/main",
                    "--tag",
                    "v0.7.0",
                    "--dry-run",
                ],
                ROOT,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"channel=stable tag=v0.7.0 sha={candidate}", result.stdout)
            self.assertIn("versions=codex:0.7.0,claude:0.7.0", result.stdout)
            self.assertNotEqual(
                run(
                    ["git", "rev-parse", "--verify", "refs/tags/v0.7.0"],
                    repo,
                    check=False,
                ).returncode,
                0,
            )

    def test_repository_channels_are_pinned_and_mutually_exclusive(self) -> None:
        versions = {
            json.loads((ROOT / path).read_text(encoding="utf-8"))["version"]
            for path in (
                ".codex-plugin/plugin.json",
                ".claude-plugin/plugin.json",
            )
        }
        self.assertEqual(versions, {"0.7.0"})
        for relative in (
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
        ):
            payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            channels = {entry["name"]: entry["source"] for entry in payload["plugins"]}
            self.assertEqual(
                set(channels), {"harness-ship", "harness-ship-next"}
            )
            self.assertEqual(channels["harness-ship"]["ref"], "v0.7.0")
            self.assertEqual(channels["harness-ship-next"]["ref"], "main")
            self.assertIsInstance(channels["harness-ship"], dict)
            self.assertNotEqual(channels["harness-ship"], "./")
        docs = (
            (ROOT / "README.md").read_text(encoding="utf-8")
            + (ROOT / "docs/upgrade-guide.md").read_text(encoding="utf-8")
        ).lower()
        for marker in (
            "mutually exclusive",
            "editable local",
            "exact confirmation",
            "restart",
            "harness-ship-next",
        ):
            self.assertIn(marker, docs)
        self.assertIn(
            "codex plugin marketplace add haru3613/harness-ship --ref main",
            docs,
        )
        self.assertIn(
            "claude plugin marketplace add haru3613/harness-ship@main",
            docs,
        )
        self.assertNotIn(
            "plugin marketplace add haru3613/harness-ship --ref v0.7.0",
            docs,
        )

    def test_release_workflow_is_attended_and_has_narrow_write_permission(
        self,
    ) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("    permissions:\n      contents: write", workflow)
        self.assertIn("--candidate \"$CANDIDATE_SHA\"", workflow)
        publisher = PUBLISHER.read_text(encoding="utf-8")
        self.assertNotIn("--force", publisher)
        self.assertNotIn("tag\", \"-d", publisher)
        self.assertIn("validate_plugin_lifecycle.sh", publisher)

    def test_publication_dry_run_uses_full_lifecycle_without_creating_tag(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            shutil.copytree(
                ROOT,
                repo,
                ignore=shutil.ignore_patterns(
                    ".git", ".worktrees", "__pycache__", "*.pyc"
                ),
            )
            run(["git", "init", "-q"], repo)
            run(["git", "config", "user.name", "Harness Ship Test"], repo)
            run(["git", "config", "user.email", "test@example.invalid"], repo)
            run(["git", "add", "."], repo)
            run(["git", "commit", "-qm", "release state"], repo)
            (repo / "README.md").write_text(
                (repo / "README.md").read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            candidate = self.commit(repo, "merged main candidate")
            run(["git", "branch", "-M", "main"], repo)

            result = run(
                [
                    "python3",
                    str(repo / "scripts" / "publish_release.py"),
                    "--repo",
                    str(repo),
                    "--candidate",
                    candidate,
                    "--main-ref",
                    "refs/heads/main",
                    "--tag",
                    "v0.7.0",
                    "--dry-run",
                ],
                repo,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("publication dry-run: zero mutation", result.stdout)
            self.assertIn("fresh-install receipt:", result.stdout)
            self.assertNotEqual(
                run(
                    ["git", "rev-parse", "--verify", "refs/tags/v0.7.0"],
                    repo,
                    check=False,
                ).returncode,
                0,
            )


if __name__ == "__main__":
    unittest.main()
