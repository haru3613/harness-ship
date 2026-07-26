from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class AcceptanceDesignContractTests(unittest.TestCase):
    """HS-QA-BUG/acceptance-v1: SC-001 traces to AC-1 and AC-7."""

    def assert_compatibility_policy(
        self, version: str, testing_workflow: str, readme: str
    ) -> None:
        major, minor, _patch = (int(part) for part in version.split("."))
        normalized = " ".join(testing_workflow.split())

        if (major, minor) >= (0, 7):
            for marker in (
                "v0.6 compatibility",
                "implementation already exists",
                "no approved acceptance contract",
                "one minor release",
            ):
                self.assertNotIn(marker, normalized)
            self.assertNotIn("**v0.6.0 migration:**", readme)
            for command in (
                "$harness-ship:acceptance-design",
                "$harness-ship:testing-workflow",
                "/harness-ship:acceptance-design",
                "/harness-ship:testing-workflow",
            ):
                self.assertIn(command, readme)
            return

        self.assertEqual((major, minor), (0, 6))
        compatibility = normalized.split("v0.6 compatibility", maxsplit=1)[1].split(
            "## Stage 2", maxsplit=1
        )[0]
        self.assertIn("pre-implementation", compatibility)
        self.assertIn("`acceptance-design`", compatibility)
        self.assertNotIn("/testing-workflow", compatibility)
        self.assertRegex(compatibility.lower(), r"do not (begin|start|run) qa execution")
        self.assertIn("one minor release", compatibility.lower())
        self.assertIn("implementation already exists", compatibility)
        self.assertIn("no approved acceptance contract", compatibility)
        self.assertIn("original or current stable spec", compatibility)
        self.assertIn("never infer expected behaviour from code", compatibility.lower())
        self.assertIn("stop", compatibility.lower())
        self.assertIn("**v0.6.0 migration:**", readme)
        for command in (
            "$harness-ship:acceptance-design",
            "$harness-ship:testing-workflow",
            "/harness-ship:acceptance-design",
            "/harness-ship:testing-workflow",
        ):
            self.assertIn(command, readme)

    def test_acceptance_design_is_a_discoverable_skill(self) -> None:
        text = read("skills/acceptance-design/SKILL.md")

        self.assertRegex(text, r"(?m)^name:\s+acceptance-design$")
        self.assertIn("# acceptance-design", text)

    def test_acceptance_design_uses_project_tracker_and_tool_policy(self) -> None:
        skill = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        setup = " ".join(read("skills/setup/SKILL.md").lower().split())

        self.assertIn("## harness-ship", skill)
        self.assertIn("configured tracker", skill)
        self.assertIn("forbidden tools", skill)
        self.assertIn("run `setup` if", skill)
        self.assertIn("`acceptance-design`", setup)

    def test_scenario_contract_is_versioned_traceable_and_qa_executable(self) -> None:
        text = " ".join(read("skills/acceptance-design/SKILL.md").split())

        for marker in (
            "<spec-id>/acceptance-vN",
            "stable SC-ID",
            "stable AC-ID",
            "SC-ID → AC-ID",
            "P0",
            "P1",
            "surface",
            "Given",
            "When",
            "Then",
            "negative assertion",
            "QA-executable seam",
            "fixture/data needs",
            "QA assurance profile",
        ):
            self.assertIn(marker, text)

    def test_any_approved_contract_content_change_increments_revision(self) -> None:
        text = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        dev = " ".join(read("skills/dev-workflow/SKILL.md").lower().split())

        self.assertIn("any approved contract content changes", text)
        for field in (
            "priority",
            "surface",
            "qa-executable seam",
            "fixture/data needs",
            "qa assurance profile",
        ):
            self.assertIn(field, text)
        self.assertIn("preserve stable sc-id and ac-id", text)
        self.assertIn("contract revision still follows", text)
        self.assertIn("every approved contract-content change", dev)
        self.assertIn("returns to stage 3", dev)

    def test_p0_profiles_are_per_pr_or_explicit_human_exceptions(self) -> None:
        design = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        testing = " ".join(read("skills/testing-workflow/SKILL.md").lower().split())

        self.assertIn("p0 assurance profile", design)
        self.assertIn("automated on every pr", design)
        self.assertIn("qa automation owner", design)
        self.assertIn("approved exception owner", design)
        self.assertIn("equals the qa automation owner", design)
        self.assertIn("explicit user approval", design)
        self.assertIn("follow-up ticket", design)
        self.assertIn("expiry", design)
        self.assertIn("automated p0 profiles run on every pr", testing)
        self.assertIn("manual p0 exception", testing)
        self.assertIn("accept with caveats", testing)
        self.assertIn("exact candidate artifact", testing)

    def test_p0_automation_has_premerge_ownership_and_independent_qa_execution(self) -> None:
        dev = " ".join(read("skills/dev-workflow/SKILL.md").lower().split())
        implement_source = read("skills/implement/SKILL.md").lower()
        implement = " ".join(implement_source.split())
        premerge = " ".join(
            implement_source.split("### pre-merge p0 qa automation", maxsplit=1)[1]
            .split("## phase 3", maxsplit=1)[0]
            .split()
        )
        publish = " ".join(
            implement_source.split("## phase 4", maxsplit=1)[1]
            .split("## stop and recovery", maxsplit=1)[0]
            .split()
        )
        testing = " ".join(read("skills/testing-workflow/SKILL.md").lower().split())
        tdd = " ".join(read("skills/tdd/SKILL.md").lower().split())

        self.assertIn("qa automation owner", dev)
        self.assertIn("every approved p0", dev)
        self.assertIn("feature-branch head before publication", dev)
        self.assertIn("exact pr head", dev)
        self.assertIn("before merge", dev)
        self.assertIn("approved p0 integration/e2e automation", dev)
        self.assertIn("qa automation owner", implement)
        self.assertIn("approved p0 integration/e2e", implement)
        self.assertIn("bounded qa automation write slice", implement)
        self.assertIn("root inspects", implement)
        self.assertIn("checkpoint commit", implement)
        self.assertIn("ticket/receipt before pr creation", implement)
        self.assertIn("attach", implement)
        self.assertIn("exact head", implement)
        self.assertIn("before merge", implement)
        self.assertIn("clean committed feature-branch head before publication", premerge)
        self.assertNotIn("implementation pr's committed", premerge)
        self.assertLess(publish.index("open/update one pr"), publish.index("required ci includes"))
        self.assertIn("exact pr head", publish)
        self.assertIn("independently execute", testing)
        self.assertIn("exact handed-off artifact", testing)
        self.assertIn("unit and contract tests only", tdd)

    def test_p0_prepublication_evidence_tracks_every_local_head(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        integrate = " ".join(
            implement.split("## phase 3", maxsplit=1)[1]
            .split("## phase 4", maxsplit=1)[0]
            .split()
        )
        publish = " ".join(
            implement.split("## phase 4", maxsplit=1)[1]
            .split("## stop and recovery", maxsplit=1)[0]
            .split()
        )

        self.assertIn("without a manual exception", integrate)
        self.assertIn("when a manual exception is requested", integrate)
        self.assertIn("record the skip", integrate)
        self.assertNotIn("unless the validated manual exception applies", integrate)
        self.assertIn("every fix commit invalidates", integrate)
        self.assertIn("repeat step 3", integrate)
        self.assertIn("rebase or conflict-resolution commit invalidates", publish)
        self.assertIn("repeat phase 3 step 3", publish)
        self.assertIn("before push", publish)
        self.assertIn("receipt's head matches the current head", publish)

    def test_remote_feedback_refreshes_p0_before_each_push(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        remote = " ".join(
            implement.split("4. run the **remote feedback loop**", maxsplit=1)[1]
            .split("5. proceed only", maxsplit=1)[0]
            .split()
        )

        for marker in (
            "commit valid fixes",
            "repeat phase 3 step 3",
            "checkpoint the new exact head",
            "push a new head",
        ):
            self.assertIn(marker, remote)
        commit_index = remote.index("commit valid fixes")
        refresh_index = remote.index("repeat phase 3 step 3")
        checkpoint_index = remote.index("checkpoint the new exact head")
        push_index = remote.index("push a new head")
        self.assertLess(commit_index, refresh_index)
        self.assertLess(refresh_index, checkpoint_index)
        self.assertLess(checkpoint_index, push_index)

    def test_manual_p0_exception_is_revalidated_at_every_remote_skip(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        premerge = " ".join(
            implement.split("### pre-merge p0 qa automation", maxsplit=1)[1]
            .split("## phase 3", maxsplit=1)[0]
            .split()
        )
        integrate = " ".join(
            implement.split("## phase 3", maxsplit=1)[1]
            .split("## phase 4", maxsplit=1)[0]
            .split()
        )
        publish = " ".join(
            implement.split("## phase 4", maxsplit=1)[1]
            .split("## stop and recovery", maxsplit=1)[0]
            .split()
        )
        fields = (
            "current explicit user approval",
            "follow-up ticket exists and is open",
            "named owner",
            "unexpired deadline",
            "exact-candidate execution method",
            "required evidence",
            "live follow-up-ticket assignee equals the approved qa automation owner",
            "approved exception owner equals the approved qa automation owner",
        )

        for phase in (premerge, integrate, publish):
            for field in fields:
                self.assertIn(field, phase)
        self.assertIn("immediately before this exception-based skip", integrate)
        self.assertIn("before every exception-based skip", publish)
        self.assertIn("immediately before merge", publish)
        self.assertIn("stage 3", publish)

    def test_exception_owner_binding_is_preserved_through_qa(self) -> None:
        testing = read("skills/testing-workflow/SKILL.md").lower()
        stage2 = " ".join(
            testing.split("## stage 2", maxsplit=1)[1]
            .split("## stage 3", maxsplit=1)[0]
            .split()
        )
        stage3 = " ".join(
            testing.split("## stage 3", maxsplit=1)[1]
            .split("## stage 4", maxsplit=1)[0]
            .split()
        )
        report = " ".join(
            read("skills/testing-workflow/acceptance-report-template.md")
            .lower()
            .split("## manual p0 exceptions", maxsplit=1)[1]
            .split("## what failed", maxsplit=1)[0]
            .split()
        )

        for phase in (stage2, stage3):
            self.assertIn(
                "live follow-up-ticket assignee equals the approved qa automation owner",
                phase,
            )
            self.assertIn("owner mismatch", phase)
            self.assertIn("not ready", phase)
            self.assertIn("stage 3", phase)
        for field in (
            "approved qa automation owner",
            "live ticket assignee",
            "owner match",
            "exception validated at",
        ):
            self.assertIn(field, report)

    def test_owner_binding_uses_immutable_provider_principal_ids(self) -> None:
        design = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        dev = " ".join(read("skills/dev-workflow/SKILL.md").lower().split())
        implement = " ".join(read("skills/implement/SKILL.md").lower().split())
        testing = " ".join(read("skills/testing-workflow/SKILL.md").lower().split())
        report = " ".join(
            read("skills/testing-workflow/acceptance-report-template.md").lower().split()
        )

        for text in (design, implement, testing):
            self.assertIn("immutable provider principal id", text)
            self.assertIn("display label", text)
            self.assertIn("compare principal ids", text)
        self.assertIn("accountable owner", dev)
        self.assertIn("executing agent role", dev)
        self.assertIn("accountable owner", implement)
        self.assertIn("executing agent role", implement)
        self.assertIn("principal id", report)
        self.assertIn("display label", report)

    def test_qa_prerequisites_branch_for_automated_and_excepted_p0(self) -> None:
        testing = read("skills/testing-workflow/SKILL.md").lower()
        stage3 = " ".join(
            testing.split("## stage 3", maxsplit=1)[1]
            .split("## stage 4", maxsplit=1)[0]
            .split()
        )

        self.assertIn("without a manual exception", stage3)
        self.assertIn("exact-pr-head automation evidence", stage3)
        self.assertIn("with an approved manual exception", stage3)
        self.assertIn("fresh six-field-and-owner-match exception receipt", stage3)
        self.assertIn("exact handed-off artifact", stage3)
        self.assertIn("manual exact-candidate method", stage3)
        self.assertNotIn(
            "pre-merge automation evidence on the implementation pr is a prerequisite",
            stage3,
        )

    def test_qa_revalidates_exception_immediately_before_stage5_verdict(self) -> None:
        testing = read("skills/testing-workflow/SKILL.md").lower()
        stage5 = " ".join(
            testing.split("## stage 5", maxsplit=1)[1]
            .split("## stage 6", maxsplit=1)[0]
            .split()
        )
        fields = (
            "current explicit user approval",
            "follow-up ticket exists and is open",
            "named owner",
            "unexpired deadline",
            "exact-candidate execution method",
            "required evidence",
            "live follow-up-ticket assignee equals the approved qa automation owner",
            "approved exception owner equals the approved qa automation owner",
        )

        self.assertIn("immediately before generating the report and verdict", stage5)
        for field in fields:
            self.assertIn(field, stage5)
        self.assertIn("owner mismatch", stage5)
        self.assertIn("not ready", stage5)
        self.assertIn("validation timestamp", stage5)

    def test_qa_only_checks_rd_receipts_instead_of_running_rd_tests(self) -> None:
        testing = read("skills/testing-workflow/SKILL.md").lower()
        stage2 = " ".join(
            testing.split("## stage 2", maxsplit=1)[1]
            .split("## stage 3", maxsplit=1)[0]
            .split()
        )

        self.assertIn("verify the rd unit/contract receipt", stage2)
        self.assertIn("missing or red", stage2)
        self.assertIn("return to rd", stage2)
        self.assertIn("qa executes only", stage2)
        self.assertNotIn("test the contract against the api schema", stage2)

    def test_manual_p0_exception_is_validated_and_reported(self) -> None:
        testing = read("skills/testing-workflow/SKILL.md").lower()
        stage2 = " ".join(
            testing.split("## stage 2", maxsplit=1)[1]
            .split("## stage 3", maxsplit=1)[0]
            .split()
        )
        stage3 = " ".join(
            testing.split("## stage 3", maxsplit=1)[1]
            .split("## stage 4", maxsplit=1)[0]
            .split()
        )
        template_source = read(
            "skills/testing-workflow/acceptance-report-template.md"
        ).lower()
        exceptions = " ".join(
            template_source.split("## manual p0 exceptions", maxsplit=1)[1]
            .split("## what failed", maxsplit=1)[0]
            .split()
        )

        fields = (
            "current explicit user approval",
            "follow-up ticket exists and is open",
            "named owner",
            "unexpired deadline",
            "exact-candidate execution method",
            "required evidence",
        )
        for phase in (stage2, stage3):
            for field in fields:
                self.assertIn(field, phase)
            self.assertIn("not ready", phase)
        for field in (
            "exception approval",
            "exception ticket",
            "approved qa automation owner",
            "exception expiry",
            "exception execution method",
            "exception required evidence",
            "exception produced evidence",
            "exception evaluation",
        ):
            self.assertIn(field, exceptions)

    def test_p0_flakes_cannot_bypass_the_exception_gate(self) -> None:
        testing = read("skills/testing-workflow/SKILL.md").lower()
        implement = read("skills/implement/SKILL.md").lower()
        stage3 = " ".join(
            testing.split("## stage 3", maxsplit=1)[1]
            .split("## stage 4", maxsplit=1)[0]
            .split()
        )
        integrate = " ".join(
            implement.split("## phase 3", maxsplit=1)[1]
            .split("## phase 4", maxsplit=1)[0]
            .split()
        )
        remote = " ".join(
            implement.split("4. run the **remote feedback loop**", maxsplit=1)[1]
            .split("5. proceed only", maxsplit=1)[0]
            .split()
        )

        self.assertIn("non-p0 only", stage3)
        self.assertIn("p0 flaky", stage3)
        self.assertIn("not ready", stage3)
        self.assertIn("stage 3", stage3)
        for phase in (integrate, remote):
            self.assertIn("p0 flaky", phase)
            self.assertIn("not ready", phase)
            self.assertIn("must not be quarantined", phase)
            self.assertIn("infrastructure retry", phase)
            self.assertIn("stage 3", phase)

    def test_p0_state_is_durable_in_the_recovery_receipt(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        recovery = " ".join(
            implement.split("## stop and recovery", maxsplit=1)[1].split()
        )

        for field in (
            "p0 profile",
            "qa automation owner",
            "exact-head result",
            "produced evidence",
            "manual-exception six fields",
            "last validation time",
            "observed live ticket assignee",
            "owner-match result",
            "exact pr-head/expected-target-head pair",
            "merge-intent enforcement",
            "observed-derivation state",
        ):
            self.assertIn(field, recovery)

    def test_infrastructure_retry_requires_checkpointed_non_test_evidence(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        remote = " ".join(
            implement.split("4. run the **remote feedback loop**", maxsplit=1)[1]
            .split("5. proceed only", maxsplit=1)[0]
            .split()
        )
        fields = (
            "checkpointed proof",
            "profile/test never started",
            "provider incident",
            "test-started or ambiguous",
            "p0",
            "not ready",
            "infrastructure retry",
        )

        for field in fields:
            self.assertIn(field, remote)
        self.assertLess(remote.index("checkpointed proof"), remote.index("infrastructure retry"))

    def test_premerge_rechecks_target_and_binds_both_heads(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        publish = " ".join(
            implement.split("## phase 4", maxsplit=1)[1]
            .split("## stop and recovery", maxsplit=1)[0]
            .split()
        )
        premerge = " ".join(
            publish.split("6. ", maxsplit=1)[1].split("7. ", maxsplit=1)[0].split()
        )

        for marker in (
            "fetch the target branch",
            "exact pr head",
            "expected target head",
            "if either differs",
            "return to phase 4 step 1",
            "checkpoint the merge intent",
            "cas/ref-lease",
            "human merge receipt",
            "observed merge derives from that exact pair",
        ):
            self.assertIn(marker, premerge)
        self.assertLess(
            premerge.index("fetch the target branch"),
            premerge.index("checkpoint the merge intent"),
        )
        self.assertLess(
            premerge.index("checkpoint the merge intent"),
            premerge.index("merge only"),
        )

    def test_p0_review_and_ci_producers_checkpoint_the_target_pair(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        publish = " ".join(
            implement.split("## phase 4", maxsplit=1)[1]
            .split("## stop and recovery", maxsplit=1)[0]
            .split()
        )
        remote = " ".join(
            publish.split("4. run the **remote feedback loop**", maxsplit=1)[1]
            .split("5. proceed only", maxsplit=1)[0]
            .split()
        )

        self.assertIn("checkpoint the expected target head", publish)
        self.assertIn("alongside every pre-publication p0/review evidence set", publish)
        self.assertIn("exact pr head + expected target head", remote)
        self.assertIn("p0/review/ci evidence set", remote)

    def test_postmerge_recovery_replays_pair_bound_authorization(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        phase0 = " ".join(
            implement.split("## phase 0", maxsplit=1)[1]
            .split("## durable checkpoint protocol", maxsplit=1)[0]
            .split()
        )

        for marker in (
            "pair-bound merge intent",
            "authorization receipt",
            "actual merge derivation",
            "applicable exception state",
            "fail closed",
            "human reconciliation",
        ):
            self.assertIn(marker, phase0)

    def test_report_separates_pr_automation_from_artifact_qa_evidence(self) -> None:
        template = " ".join(
            read("skills/testing-workflow/acceptance-report-template.md")
            .lower()
            .split("## journeys", maxsplit=1)[1]
            .split("## manual p0 exceptions", maxsplit=1)[0]
            .split()
        )

        for field in (
            "exact pr head",
            "expected target head",
            "observed merge sha/derivation",
            "pair-bound rd receipt",
            "pr automation/ci evidence",
            "handed-off source/artifact revision",
            "independent qa evidence",
        ):
            self.assertIn(field, template)

    def test_qa_handoff_consumes_the_pair_bound_merge_chain(self) -> None:
        dev = read("skills/dev-workflow/SKILL.md").lower()
        stage6 = " ".join(dev.split("## stage 6", maxsplit=1)[1].split())
        testing = read("skills/testing-workflow/SKILL.md").lower()
        stage2 = " ".join(
            testing.split("## stage 2", maxsplit=1)[1]
            .split("## stage 3", maxsplit=1)[0]
            .split()
        )

        for field in (
            "expected target head",
            "observed merge sha",
            "merge derivation",
            "pair-bound rd receipt",
            "pair-bound p0 receipt",
        ):
            self.assertIn(field, stage6)
            self.assertIn(field, stage2)
        self.assertIn("mismatched or unrelated", stage2)
        self.assertIn("not ready", stage2)

    def test_initial_prepush_revalidates_live_exception_state(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        publish = " ".join(
            implement.split("## phase 4", maxsplit=1)[1]
            .split("## stop and recovery", maxsplit=1)[0]
            .split()
        )
        phase4_source = implement.split("## phase 4", maxsplit=1)[1].split(
            "## stop and recovery", maxsplit=1
        )[0]
        initial_push = " ".join(
            phase4_source.split("\n2. ", maxsplit=1)[1]
            .split("\n3. attach", maxsplit=1)[0]
            .split()
        )

        self.assertIn("freshly re-read live exception state", initial_push)
        self.assertIn("six fields", initial_push)
        self.assertIn("live assignee", initial_push)
        self.assertIn("owner match", initial_push)
        self.assertIn("before push", initial_push)

    def test_human_merge_receipt_is_observed_at_the_actual_action(self) -> None:
        implement = read("skills/implement/SKILL.md").lower()
        publish = " ".join(
            implement.split("## phase 4", maxsplit=1)[1]
            .split("## stop and recovery", maxsplit=1)[0]
            .split()
        )
        premerge = " ".join(
            publish.split("6. ", maxsplit=1)[1].split("7. ", maxsplit=1)[0].split()
        )
        phase0 = " ".join(
            implement.split("## phase 0", maxsplit=1)[1]
            .split("## durable checkpoint protocol", maxsplit=1)[0]
            .split()
        )

        for marker in (
            "pre-merge authorization is not a merge receipt",
            "at the actual human merge action",
            "merge timestamp",
            "observed human merge receipt",
            "provider principal ids",
        ):
            self.assertIn(marker, premerge)
        self.assertLess(
            premerge.index("pre-merge authorization"),
            premerge.index("at the actual human merge action"),
        )
        self.assertLess(
            premerge.index("at the actual human merge action"),
            premerge.index("observed human merge receipt"),
        )
        for marker in (
            "observed human merge receipt",
            "merge timestamp",
            "actual-action snapshot",
        ):
            self.assertIn(marker, phase0)

    def test_tdd_seam_corrections_cannot_mutate_the_acceptance_contract(self) -> None:
        text = " ".join(read("skills/tdd/SKILL.md").lower().split())

        self.assertIn("internal implementation test seam", text)
        self.assertIn("acceptance-contract qa-executable seam", text)
        for field in (
            "qa assurance profile",
            "fixture/data needs",
            "priority",
        ):
            self.assertIn(field, text)
        self.assertIn("always requires a new contract revision", text)
        self.assertIn("stage 3 re-approval", text)

    def test_acceptance_design_stops_before_implementation_or_qa_execution(self) -> None:
        text = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())

        self.assertIn("design only", text)
        self.assertIn("stop", text)
        self.assertRegex(text, r"do not (begin|start|run) qa execution")
        self.assertIn("do not implement", text)

    def test_acceptance_design_uses_the_joint_acceptance_gate(self) -> None:
        skill = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        dev = " ".join(read("skills/dev-workflow/SKILL.md").lower().split())
        readme = " ".join(read("README.md").lower().split())
        codex = json.loads(read(".codex-plugin/plugin.json"))

        self.assertIn("current stable spec", skill)
        self.assertIn("do not require a separate spec-approval gate", skill)
        self.assertIn("presents the spec criteria and scenario set together", skill)
        self.assertIn("for explicit user approval", skill)
        self.assertIn("spec criteria and scenarios describe the right behaviour", dev)
        self.assertIn("current stable spec", readme)
        self.assertTrue(
            any("current spec" in prompt.lower() for prompt in codex["interface"]["defaultPrompt"])
        )

    def test_only_the_user_can_approve_the_acceptance_contract(self) -> None:
        skill = " ".join(read("skills/acceptance-design/SKILL.md").lower().split())
        dev = " ".join(read("skills/dev-workflow/SKILL.md").lower().split())

        self.assertIn("only the user may approve", skill)
        self.assertIn("unapproved draft", skill)
        self.assertIn("never self-approve", skill)
        self.assertIn("user confirms", dev)

    def test_dev_workflow_invokes_acceptance_design_at_the_acceptance_gate(self) -> None:
        text = read("skills/dev-workflow/SKILL.md")
        stage = text.split("## Stage 3 — Acceptance contract", maxsplit=1)[1].split(
            "## Stage 4 — Tickets", maxsplit=1
        )[0]

        self.assertRegex(stage, r"Run \*\*`acceptance-design`\*\*")
        self.assertNotIn("Stage 1 of `testing-workflow`", stage)
        self.assertIn("<spec-id>/acceptance-vN", stage)

    def test_spec_routes_scenario_authoring_to_acceptance_design(self) -> None:
        text = read("skills/spec/SKILL.md")
        normalized = " ".join(text.lower().split())

        self.assertIn("`acceptance-design` turns these criteria into", normalized)
        self.assertIn("acceptance-scenario design is `acceptance-design`'s job", normalized)
        self.assertNotRegex(
            normalized,
            r"testing-workflow.{0,80}(acceptance contract|scenario design|scenario authoring)",
        )

    def test_testing_workflow_executes_approved_scenarios_but_does_not_author_them(self) -> None:
        text = read("skills/testing-workflow/SKILL.md")
        normalized = " ".join(text.lower().split())

        self.assertNotIn("## Stage 1 — Journeys → scenarios", text)
        self.assertNotRegex(normalized, r"testing-workflow.{0,80}(design|author).{0,80}scenario")
        self.assertIn("approved acceptance contract", normalized)
        self.assertIn("do not redesign", normalized)
        self.assertIn("integration + e2e", normalized)

    def test_testing_workflow_consumes_assurance_profiles_without_redesign(self) -> None:
        text = " ".join(read("skills/testing-workflow/SKILL.md").lower().split())

        self.assertIn("qa assurance profile", text)
        self.assertIn("execute each approved profile unchanged", text)
        self.assertIn("automation expectation", text)
        self.assertIn("required evidence", text)
        self.assertIn("risk-specific probes", text)
        self.assertIn("return to `acceptance-design`", text)
        self.assertIn("report the profile and evidence for every scenario", text)

    def test_testing_workflow_executes_integration_and_e2e_at_the_approved_layer(self) -> None:
        text = " ".join(read("skills/testing-workflow/SKILL.md").lower().split())

        self.assertIn("## stage 3 — execute approved qa layer", text)
        self.assertIn("integration profile", text)
        self.assertIn("at its named seam", text)
        self.assertIn("e2e / journey profile", text)
        self.assertIn("journey runner", text)
        self.assertIn("do not escalate an integration profile to e2e", text)

    def test_acceptance_report_template_records_assurance_evidence_for_every_scenario(self) -> None:
        template = " ".join(
            read("skills/testing-workflow/acceptance-report-template.md").lower().split()
        )

        for field in (
            "qa assurance profile",
            "execution method / automation",
            "required evidence",
            "produced evidence",
            "risk-probe result",
        ):
            self.assertIn(field, template)
        self.assertIn("every scenario", template)
        self.assertNotIn("evidence links open", template)
        self.assertIn("only the user", template)
        self.assertNotIn("authorized human", template)
        self.assertIn("automation cannot sign", template)

    def test_versioned_compatibility_redirect_and_expiry(self) -> None:
        text = read("skills/testing-workflow/SKILL.md")
        readme = read("README.md")
        version = json.loads(read(".codex-plugin/plugin.json"))["version"]

        self.assert_compatibility_policy(version, text, readme)

    def test_v07_policy_rejects_retained_alias_and_accepts_complete_removal(self) -> None:
        current_workflow = read("skills/testing-workflow/SKILL.md")
        current_readme = read("README.md")

        with self.assertRaises(AssertionError):
            self.assert_compatibility_policy("0.7.0", current_workflow, current_readme)

        future_workflow = re.sub(
            r"## v0\.6 compatibility redirect.*?(?=## Stage 2)",
            "",
            current_workflow,
            flags=re.DOTALL,
        )
        future_readme = re.sub(
            r"\n\*\*v0\.6\.0 migration:\*\*.*?(?=\n\n)",
            "",
            current_readme,
            flags=re.DOTALL,
        )
        with self.assertRaises(AssertionError):
            self.assert_compatibility_policy("0.7.0", future_workflow, future_readme)

        future_readme += (
            "\nCanonical commands remain valid: "
            "`$harness-ship:acceptance-design`, `$harness-ship:testing-workflow`, "
            "`/harness-ship:acceptance-design`, `/harness-ship:testing-workflow`.\n"
        )
        self.assert_compatibility_policy("0.7.0", future_workflow, future_readme)

    def test_existing_execution_stage_ids_and_references_remain_stable(self) -> None:
        text = read("skills/testing-workflow/SKILL.md")

        for heading in (
            "## Stage 2 — Route approved scenarios by ownership",
            "## Stage 3 — Execute approved QA layer",
            "## Stage 4 — Anti-fake-green gate",
            "## Stage 5 — Acceptance report",
            "## Stage 6 — Bug loopback",
        ):
            self.assertIn(heading, text)
        self.assertIn("acceptance-report-template.md", text)

    def test_readme_and_plugin_metadata_advertise_acceptance_design(self) -> None:
        readme = read("README.md")

        self.assertRegex(readme, r"(?m)^\| `acceptance-design` \|")
        self.assertIn("eight self-contained blocks", readme)

        versions = set()
        for manifest in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ):
            payload = json.loads(read(manifest))
            versions.add(payload["version"])
            self.assertIn("acceptance-design", payload["keywords"])
        self.assertEqual(len(versions), 1)
        version = versions.pop()
        self.assertGreaterEqual(tuple(int(part) for part in version.split(".")), (0, 6, 0))

        codex = json.loads(read(".codex-plugin/plugin.json"))
        self.assertTrue(
            any("acceptance" in prompt.lower() for prompt in codex["interface"]["defaultPrompt"])
        )

        marketplace = json.loads(read(".claude-plugin/marketplace.json"))["plugins"][0]
        self.assertIn("eight self-contained blocks", marketplace["description"])
        self.assertIn("acceptance-design", marketplace["keywords"])


if __name__ == "__main__":
    unittest.main()
