from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class ImplementSkillContractTests(unittest.TestCase):
    def test_implement_is_a_discoverable_skill(self) -> None:
        text = read("skills/implement/SKILL.md")

        self.assertRegex(text, r"(?m)^name:\s+implement$")
        self.assertIn("# implement", text)

    def test_root_owns_orchestration_and_only_predefined_profiles_are_dispatched(self) -> None:
        text = read("skills/implement/SKILL.md").lower()

        for responsibility in ("planning", "delegation", "integration", "final decision"):
            self.assertIn(responsibility, text)
        self.assertRegex(text, r"pre[- ]defined role profile")
        for property_name in ("mode", "model", "effort"):
            self.assertIn(property_name, text)
        self.assertIn("must not spawn", text)
        self.assertIn("mcp", text)
        self.assertNotRegex(text, r"gpt-\d")

    def test_dispatch_contract_is_bounded_and_writer_safe(self) -> None:
        text = read("skills/implement/SKILL.md").lower()

        for field in (
            "bounded deliverable",
            "allowed files",
            "exact worktree path",
            "working directory",
            "constraints",
            "verification",
        ):
            self.assertIn(field, text)
        self.assertIn("one writer", text)
        self.assertIn("overlapping", text)
        self.assertIn("serialize all write-capable", text)

    def test_implementation_closes_the_delivery_loop(self) -> None:
        text = " ".join(read("skills/implement/SKILL.md").lower().split())

        for marker in (
            "fixed point",
            "baseline",
            "red",
            "green",
            "typecheck",
            "full configured **rd verification gate**",
            "review",
            "exact head sha",
            "recompute the fixed point",
            "tracker",
            "cleanup",
            "implementation receipt",
            "deployment receipt",
            "remote feedback loop",
            "resume policy",
            "heartbeat",
            "takeover",
            "release",
            "workflow phase",
            "deployment-only resume",
            "independent outcome verifier",
            "claim generation / fencing token",
            "durable checkpoint protocol",
            "post-merge reconciliation",
            "worktree-disposed=true",
            "<repo-root>/.worktrees/<task-slug>",
        ):
            self.assertIn(marker, text)

        cleanup_position = text.index("worktree **cleanup**")
        deployment_position = text.index("obtain a **deployment receipt**")
        self.assertLess(cleanup_position, deployment_position)

        remote_loop = text.split("remote feedback loop", maxsplit=1)[1].split(
            "proceed only", maxsplit=1
        )[0]
        self.assertIn("standards-only", remote_loop)
        self.assertIn("keep tests green", remote_loop)
        self.assertIn("independent outcome verifier", remote_loop)

    def test_recovery_checkpoints_and_fences_external_mutations(self) -> None:
        text = " ".join(read("skills/implement/SKILL.md").lower().split())

        self.assertIn("there must be no claimed-without-receipt window", text)
        self.assertIn("immediately before every external mutation", text)
        self.assertIn("owner, lease, contract revision, and fencing token", text)
        self.assertIn("before each external mutation", text)
        self.assertIn("after each external mutation", text)
        self.assertIn("does not repeat the operation blindly", text)
        self.assertIn("conditional on the expected claim generation at its target", text)
        self.assertIn("cas/etag/ref-lease enforcement", text)
        self.assertIn("automatic mutation and takeover fail closed", text)
        self.assertLess(
            text.index("post-merge reconciliation", text.index("root alone:")),
            text.index("obtain a **deployment receipt**"),
        )

    def test_write_capable_dispatch_is_checkpointed_before_it_starts(self) -> None:
        text = " ".join(read("skills/implement/SKILL.md").lower().split())
        phase = text.split("## phase 2 — execute tdd slices", maxsplit=1)[1].split(
            "## phase 3 — integrate, verify, and review", maxsplit=1
        )[0]

        for field in (
            "slice id",
            "dispatch/idempotency id",
            "verified role-definition digest",
            "expected head",
            "working-tree status",
            "allowed files",
            "`in-flight` state",
            "host run identity",
            "terminal result",
        ):
            self.assertIn(field, text)
        self.assertLess(phase.index("pre-dispatch `in-flight` reservation"), phase.index("dispatches"))
        self.assertIn("do not redispatch", text)

    def test_profiles_are_revalidated_for_every_dispatch(self) -> None:
        text = " ".join(read("skills/implement/SKILL.md").lower().split())

        self.assertIn("immediately before every dispatch", text)
        self.assertIn("immutable digest keyed by its dispatch id and selected role", text)
        self.assertIn("dispatch-scoped digest", text)
        self.assertIn("sequential dispatches may legitimately select different mapped profiles", text)
        self.assertIn("only when they select the same approved binding", text)

    def test_worktrees_use_the_repository_local_nested_location(self) -> None:
        text = " ".join(read("skills/implement/SKILL.md").lower().split())

        self.assertIn("<repo-root>/.worktrees/<task-slug>", text)
        self.assertIn("git worktree list", text)
        self.assertIn(".git/info/exclude", text)
        self.assertIn("detached head at the exact source sha", text)
        self.assertIn("never create sibling worktrees", text)

    def test_setup_records_runtime_role_profiles_without_owning_them(self) -> None:
        text = read("skills/setup/SKILL.md").lower()

        self.assertIn("agent role profiles", text)
        self.assertIn("host", text)
        self.assertIn("mode", text)
        self.assertIn("effort", text)
        self.assertRegex(text, r"do not (create|override)")
        self.assertIn("definition source", text)
        self.assertIn("may spawn", text)
        self.assertIn("unsupported", text)
        self.assertIn("ready criteria", text)
        self.assertIn("claim transition", text)
        self.assertIn("claim recovery", text)
        self.assertIn("deployment / test environment", text)
        self.assertIn("agent role requirements", text)
        self.assertIn("agent role bindings — codex", text)
        self.assertIn("agent role bindings — claude code", text)
        self.assertIn("delegation limits — codex", text)
        self.assertIn("delegation limits — claude code", text)
        self.assertIn("security review", text)
        self.assertIn("security implementation", text)
        self.assertIn("build", text)
        self.assertNotIn("<profile | missing>", text)

    def test_dev_workflow_delegates_stage_five_to_implement(self) -> None:
        text = read("skills/dev-workflow/SKILL.md")
        stage = text.split("## Stage 5 — Implement", maxsplit=1)[1].split(
            "## Stage 6 — Hand to QA", maxsplit=1
        )[0]

        self.assertRegex(stage, r"Run \*\*`implement`\*\*")
        self.assertNotIn("ship-loop", stage)
        self.assertLess(stage.index("cleanup"), stage.index("deployment evidence"))

    def test_review_pins_a_fixed_point_and_reviews_committed_work(self) -> None:
        text = " ".join(read("skills/review/SKILL.md").lower().split())

        self.assertIn("fixed point", text)
        self.assertIn("merge-base", text)
        self.assertRegex(text, r"fixed[- ]point\.\.\.head")
        self.assertIn("originating", text)
        self.assertIn("commit list", text)
        self.assertIn("two fresh child runs", text)
        self.assertIn("blocked", text)
        self.assertIn("self-contained block", text)
        self.assertIn("independence: not established", text)

    def test_readme_and_manifests_advertise_the_current_minor_version(self) -> None:
        readme = read("README.md")
        self.assertRegex(readme, r"(?m)^\| \*\*`implement`\*\* \|")
        self.assertIn("Versioned RD/QA commands", readme)
        self.assertIn("Lint / typecheck / build", read("skills/setup/SKILL.md"))

        versions = set()
        for manifest in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ):
            payload = json.loads(read(manifest))
            versions.add(payload["version"])
        self.assertEqual(len(versions), 1)
        version = versions.pop()
        self.assertGreaterEqual(tuple(int(part) for part in version.split(".")), (0, 6, 0))

        marketplace = json.loads(read(".claude-plugin/marketplace.json"))
        listing = marketplace["plugins"][0]
        self.assertIn("QA-led", listing["description"])
        self.assertIn("implement", listing["keywords"])

    def test_public_docs_position_qa_led_software_delivery(self) -> None:
        readme = read("README.md")
        upgrade = read("docs/upgrade-guide.md")

        self.assertIn("QA-led software delivery", readme)
        self.assertIn("not a test framework", readme.lower())
        self.assertIn("exact-artifact", readme)
        self.assertIn("Bug Case", readme)
        for classification in (
            "product-defect",
            "test-defect",
            "environment-defect",
            "spec-ambiguity",
            "duplicate",
            "known-limitation",
        ):
            self.assertIn(classification, readme)
        self.assertNotIn("**v0.6.3 migration:**", readme)
        self.assertIn("**v0.6.3 migration:**", upgrade)
        self.assertEqual(upgrade.count("**v0.5.0 migration:**"), 2)

        metadata_descriptions = (
            json.loads(read(".codex-plugin/plugin.json"))["description"],
            json.loads(read(".claude-plugin/plugin.json"))["description"],
            json.loads(read(".claude-plugin/marketplace.json"))["description"],
            json.loads(read(".claude-plugin/marketplace.json"))["plugins"][0][
                "description"
            ],
        )
        for description in metadata_descriptions:
            self.assertIn("QA-led", description)

    def test_every_skill_has_matching_frontmatter_name(self) -> None:
        skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
        required_skills = {
            "clarify",
            "dev-workflow",
            "diagnose",
            "implement",
            "review",
            "setup",
            "spec",
            "spike",
            "tdd",
            "testing-workflow",
            "tickets",
        }
        self.assertTrue(required_skills.issubset({path.parent.name for path in skill_files}))

        for skill_file in skill_files:
            match = re.search(r"(?m)^name:\s+([a-z0-9-]+)$", skill_file.read_text())
            self.assertIsNotNone(match, skill_file)
            self.assertEqual(match.group(1), skill_file.parent.name)

    def test_contract_suite_is_wired_into_ci(self) -> None:
        workflow = read(".github/workflows/ci.yml")

        self.assertIn("python3 -m unittest discover -s tests -v", workflow)
        self.assertIn("jq empty", workflow)
        self.assertIn("${{ github.event.before }}", workflow)
        self.assertIn("git cat-file -e", workflow)
        self.assertIn("git log --check --format= head", workflow.lower())


if __name__ == "__main__":
    unittest.main()
