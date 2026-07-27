"""Behavioural tests for the RED evidence check."""

from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "tdd_receipt.py"

spec = importlib.util.spec_from_file_location("tdd_receipt", HELPER)
receipts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receipts)

FAILING_OUTPUT = "```\nE  AssertionError: expected 3, got None\n```"
TEST_FILE = {"tests/test_discount.py": "assert discount(10) == 3\n"}
IMPL_FILE = {"discount.py": "def discount(n): return 3\n"}


def receipt(red: str, green: str, output: str = FAILING_OUTPUT) -> str:
    return (
        "## TDD receipt\n"
        f"- RED commit: `{red}`\n"
        f"- RED: `pytest -k discount` — first 20 lines:\n{output}\n"
        f"- GREEN commit: `{green}`\n"
    )


class Repo:
    """A throwaway git repo built one commit at a time."""

    def __init__(self, directory: str) -> None:
        self.path = Path(directory)
        self.run("init", "-q")
        self.run("config", "user.email", "t@example.invalid")
        self.run("config", "user.name", "T")
        self.commit("baseline", {"README.md": "start\n"})

    def run(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.path), *args], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def commit(self, message: str, files: dict) -> str:
        for name, body in files.items():
            path = self.path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        self.run("add", "-A")
        self.run("commit", "-q", "-m", message)
        return self.run("rev-parse", "HEAD")


class RedEvidenceTests(unittest.TestCase):
    def test_test_only_red_then_implementation_green_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            red = repo.commit("red", TEST_FILE)
            green = repo.commit("green", IMPL_FILE)

            result = receipts.check(receipt(red, green), repo.path)

        self.assertEqual(result["status"], "pass")

    def test_red_containing_the_implementation_is_rejected(self) -> None:
        """The exact lie the old prose receipt could not detect."""
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            red = repo.commit("red but not really", {**TEST_FILE, **IMPL_FILE})
            green = repo.commit("green", {"discount.py": "def discount(n): return 3  # tweak\n"})

            result = receipts.check(receipt(red, green), repo.path)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("already contains implementation" in p for p in result["problems"]))
        self.assertTrue(any("discount.py" in p for p in result["problems"]))

    def test_red_with_no_test_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            red = repo.commit("red", {"notes.md": "I ran the test, honest\n"})
            green = repo.commit("green", IMPL_FILE)

            result = receipts.check(receipt(red, green), repo.path)

        self.assertTrue(any("adds no test file" in p for p in result["problems"]))

    def test_green_with_no_implementation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            red = repo.commit("red", TEST_FILE)
            green = repo.commit("green", {"tests/test_more.py": "assert True\n"})

            result = receipts.check(receipt(red, green), repo.path)

        self.assertTrue(any("changes no implementation file" in p for p in result["problems"]))

    def test_same_commit_for_red_and_green_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            both = repo.commit("both", {**TEST_FILE, **IMPL_FILE})

            result = receipts.check(receipt(both, both), repo.path)

        self.assertTrue(any("same commit" in p for p in result["problems"]))

    def test_red_after_green_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            green = repo.commit("green", IMPL_FILE)
            red = repo.commit("red", TEST_FILE)

            result = receipts.check(receipt(red, green), repo.path)

        self.assertTrue(any("does not precede" in p for p in result["problems"]))


class ReceiptParsingTests(unittest.TestCase):
    def rejection(self, text: str) -> str:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            with self.assertRaises(receipts.ReceiptError) as caught:
                receipts.check(text, repo.path)
        return str(caught.exception)

    def test_receipt_without_a_red_commit_is_rejected(self) -> None:
        text = "## TDD receipt\n- RED: `pytest` — failed because the behaviour is missing\n"

        self.assertIn("no RED commit", self.rejection(text))

    def test_receipt_without_a_green_commit_is_rejected(self) -> None:
        self.assertIn("no GREEN commit", self.rejection("- RED commit: `abc1234`\n"))

    def test_receipt_without_quoted_output_is_rejected(self) -> None:
        text = "- RED commit: `abc1234`\n- GREEN commit: `def5678`\n"

        self.assertIn("quotes no failing output", self.rejection(text))

    def test_unknown_commit_is_rejected(self) -> None:
        self.assertIn("git rev-parse", self.rejection(receipt("0" * 40, "1" * 40)))


class TestPathHeuristicTests(unittest.TestCase):
    def test_recognises_common_conventions(self) -> None:
        for path in (
            "tests/test_thing.py",
            "test/foo.js",
            "src/__tests__/button.tsx",
            "pkg/handler_test.go",
            "src/Button.test.tsx",
            "src/Button.spec.ts",
            "spec/models/user_spec.rb",
        ):
            with self.subTest(path=path):
                self.assertTrue(receipts.is_test_path(path))

    def test_does_not_mistake_implementation_for_tests(self) -> None:
        for path in ("src/latest.py", "lib/contest.js", "app/protest/view.py", "discount.py"):
            with self.subTest(path=path):
                self.assertFalse(receipts.is_test_path(path))


class CliTests(unittest.TestCase):
    def run_cli(self, repo: Repo, red: str, green: str) -> subprocess.CompletedProcess:
        path = repo.path / "receipt.md"
        path.write_text(receipt(red, green), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(HELPER), "check", "--receipt", str(path), "--repo", str(repo.path)],
            capture_output=True,
            text=True,
        )

    def test_exit_two_on_a_fabricated_red(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            red = repo.commit("red", {**TEST_FILE, **IMPL_FILE})
            green = repo.commit("green", {"discount.py": "def discount(n): return 3  # tweak\n"})
            result = self.run_cli(repo, red, green)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "fail")

    def test_exit_zero_on_a_real_red(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            red = repo.commit("red", TEST_FILE)
            green = repo.commit("green", IMPL_FILE)
            result = self.run_cli(repo, red, green)

        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
