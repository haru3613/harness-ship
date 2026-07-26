from pathlib import Path
import json
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_release_contract.py"


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
                path.write_text(
                    json.dumps({"name": "harness-ship", "version": "0.6.3"}),
                    encoding="utf-8",
                )
            else:
                path.write_text(f"baseline {relative}\n", encoding="utf-8")
        (repo / "README.md").write_text("baseline docs\n", encoding="utf-8")
        run(["git", "add", "."], repo)
        run(["git", "commit", "-qm", "base"], repo)
        return repo, run(["git", "rev-parse", "HEAD"], repo).stdout.strip()

    def commit(self, repo: Path, message: str) -> str:
        run(["git", "add", "."], repo)
        run(["git", "commit", "-qm", message], repo)
        return run(["git", "rev-parse", "HEAD"], repo).stdout.strip()

    def check(self, repo: Path, base: str, current: str) -> subprocess.CompletedProcess:
        return run(
            [
                "python3",
                str(CHECKER),
                "--repo",
                str(repo),
                base,
                current,
            ],
            ROOT,
            check=False,
        )

    def test_protected_contract_change_requires_strict_version_increase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, base = self.make_repo(directory)
            helper = repo / "scripts" / "role_binding_contract.py"
            helper.write_text("changed verifier contract\n", encoding="utf-8")
            current = self.commit(repo, "change protected contract")

            result = self.check(repo, base, current)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "protected contract changed without version increase",
                result.stderr.lower(),
            )
            self.assertIn("scripts/role_binding_contract.py", result.stderr)

    def test_version_bump_allows_protected_contract_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, base = self.make_repo(directory)
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
            current = self.commit(repo, "bump and change protected contract")

            result = self.check(repo, base, current)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("0.6.3 -> 0.6.4", result.stdout)

    def test_docs_only_change_may_keep_the_same_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo, base = self.make_repo(directory)
            (repo / "README.md").write_text("updated docs\n", encoding="utf-8")
            current = self.commit(repo, "docs only")

            result = self.check(repo, base, current)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no protected contract drift", result.stdout)


if __name__ == "__main__":
    unittest.main()
