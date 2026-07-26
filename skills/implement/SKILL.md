---
name: implement
description: >-
  Implement one approved ticket through a root-owned, role-routed delivery loop: establish an exact
  baseline, delegate bounded TDD slices only to pre-defined host agent profiles, integrate and
  review committed work, then push, verify CI, merge, update the tracker, and clean up. Use after a
  spec, acceptance contract, and ticket are approved. Triggers: "/implement", "implement this
  ticket", "build this ticket", "start the next ready ticket".
---

# implement

Implement **one approved ticket** from ready state to merged evidence. The main/root session is the
orchestrator; subagents are bounded specialists, not competing controllers.

**Prerequisite:** read the project's `## harness-ship` config in `AGENTS.md` / `CLAUDE.md`. It must
identify the tracker and PR access paths, branch topology, configured checks, and **Agent role
profiles**. If the block is absent or lacks role profiles, run `setup` before delegating.

## Root ownership — never delegate the control plane

The main/root session owns **planning, delegation, integration, and the final decision**. It also
owns:

- tracker, PR, CI, deployment, secret-bearing, or other MCP/external-state operations;
- the worktree and branch lifecycle, fixed point, commits, pushes, merges, and cleanup;
- acceptance-contract interpretation and all scope/behaviour decisions;
- inspection of every child result, conflict resolution, final checks, and the implementation
  receipt.

Children **must not spawn** more agents. They start without MCP/plugins unless a host administrator
has deliberately created a task-specific profile; never pass credentials or direct personal data
through a child prompt.

## Role-profile gate

Dispatch only to a **pre-defined role profile** that exists in the host runtime and is mapped under
the **current host's** `Agent role bindings`. **Immediately before every dispatch**, verify the live
profile's name, mode/sandbox, model, effort, definition source, write authority, `may_spawn=false`,
and capability boundary against both that binding and the portable `Agent role requirements`.
For each dispatch reservation, record an immutable digest keyed by its dispatch ID and selected
role requirement/binding. Launch and recovery must match the live profile to that dispatch-scoped
digest or stop for re-approval. Sequential dispatches may legitimately select different mapped
profiles; require digest equality across dispatches only when they select the same approved
binding. A field the host cannot expose is `unsupported`, not assumed safe.

- Do not create, override, or silently downgrade a role's model / effort / mode while implementing.
- Do not use an undefined `generic`, `default`, or `worker` profile as a substitute.
- If a mapped profile is missing or has drifted, keep safe work in root and report the mismatch.
  Stop when independent verification or a required security boundary cannot be preserved. A
  pre-defined independent-verification profile is mandatory for `implement`.
- Profile names are host-specific; route by **work nature**, not by memorized names:

| Work nature | Required boundary | Typical effort |
|---|---|---|
| one narrow lookup | read-only, no MCP | low |
| cross-module exploration | read-only, no MCP | medium |
| specification-complete mechanical edit | bounded workspace write | medium |
| implementation needing local judgment | bounded workspace write | medium or higher |
| high-risk plan challenge | read-only, independent | high |
| post-implementation verification | verification-only; no source edits | high |
| security/trust-boundary review | dedicated read-only security profile | highest configured |
| already-scoped security fix | dedicated bounded-write security profile | highest configured |

Model families are not hard-coded here. `setup` records the host's deliberate assignment; this skill
enforces it.

## Dispatch contract

Every child receives exactly one task with:

1. a **bounded deliverable**;
2. **allowed files** or an explicit read-only scope;
3. the **exact worktree path** and command **working directory**; all returned paths must resolve
   beneath that worktree;
4. the ticket, acceptance-contract revision, SC-ID → AC-ID mapping, and approved seam it needs;
5. behavioural and operational **constraints**, including forbidden tools;
6. a concrete **verification** command or evidence request;
7. an instruction not to spawn agents, commit, push, mutate tracker/PR state, or expand scope.

Use **one writer** for any file set or worktree region. **Serialize all write-capable** children in
the ticket worktree—even when their planned files are disjoint—so root can inspect and checkpoint a
clean slice without another child's uncommitted changes. Parallelize read-only investigation only.
One executor owns both RED and GREEN for its vertical behaviour slice so TDD does not split into
imagined tests versus disconnected implementation.

## Phase 0 — Resolve the work and pin the fixed point

Root:

1. Look first for a receipt-backed existing claim. Reconcile the receipt with live tracker, branch,
   PR, merge, worktree, CI, deployment, and artifact evidence before choosing a phase; live
   external evidence may advance recovery but must never be silently overwritten by stale receipt
   state. Persist the reconciled checkpoint before continuing. Apply the configured **resume
   policy**: resume
   only the same valid owner/session, or use **takeover** only after the recorded lease/heartbeat has
   expired and the takeover rule succeeds. Every successful claim/takeover issues a monotonically
   changing **claim generation / fencing token**. An active claim owned elsewhere stops this root.
   Read the receipt's **workflow phase**, merge SHA, PR, and worktree-disposed state. If live
   evidence proves the PR merged, enter the dedicated **post-merge reconciliation** path. First
   load the **pair-bound merge intent** and **authorization receipt**, verify the **actual merge
   derivation** matches their exact PR-HEAD/target-HEAD pair, and reconcile the **applicable
   exception state** at the merge action. For a human merge, require the **observed human merge
   receipt**, provider **merge timestamp**, and **actual-action snapshot** of the pair, all exception
   fields, and owner principal IDs. Missing or mismatched evidence must **fail closed** for **human
   reconciliation** before tracker transition, cleanup, or deployment. Only then finish the
   development-complete tracker transition, safely dispose the recorded feature worktree until
   `worktree-disposed=true`, and handle deployment. Do not reuse the merged branch.
   An `awaiting-deployment` **deployment-only resume** is allowed only after that disposal is
   confirmed; validate the merged SHA and jump directly to Phase 4 deployment handling without
   creating or resuming a feature worktree.
2. For new work, resolve one frontier ticket that matches the configured **ready criteria**.
3. Load the approved spec, acceptance-contract revision, stable scenario/criterion IDs, test seams,
   and explicit out-of-scope list. A stale, missing, or behaviourally contradictory contract stops
   implementation and returns to `dev-workflow` Stage 3.
4. For new work only, atomically apply the configured **claim transition** with the root/session
   identity, claim-generation fencing token, and the minimal initial recovery receipt (or an atomic
   pointer to it) in the same operation—there must be no claimed-without-receipt window. Then re-read
   the ticket to verify ownership, generation, and unchanged contract revision. **Release** a new
   claim if a terminal validation failure occurs before the worktree exists. A receipt-backed resume
   revalidates its existing claim instead of applying a second transition.
5. Inspect `git worktree list`; resume the receipt's exact branch/worktree/HEAD or create one
   at **`<repo-root>/.worktrees/<task-slug>`** with a new feature branch from the configured
   integration branch. Before the first nested worktree, ensure `.worktrees/` is ignored, preferably
   in repository-local `.git/info/exclude` when it should not be committed. Build-only worktrees
   also live under `.worktrees/` and use detached HEAD at the exact source SHA. Never create sibling
   worktrees, reuse a merged branch, duplicate an unfinished task/branch, or reuse an active/dirty
   worktree.
6. Record the exact integration-branch SHA and `git merge-base HEAD <integration-ref>` as the
   **fixed point**, plus the branch, worktree path, and starting `git status`.
7. Run a narrow **baseline** at each approved seam and the cheapest configured static check.
   Pre-existing failures stop the ticket; record them without rewriting the contract.

Refresh the claim **heartbeat** during long phases. Every implementation receipt records claim
owner, lease/heartbeat, claim-generation fencing token, and the permitted
resume/release/takeover action. Immediately before every external mutation—including tracker
changes, push, PR writes, merge, worktree cleanup, deployment, and artifact publication—re-read the
claim and abort unless owner, lease, contract revision, and fencing token still match. A heartbeat
does not replace this ownership check. The check alone is not a fence: each mutation must also be
**conditional on the expected claim generation at its target**, or use an equivalent
generation-scoped ref/resource plus CAS/ETag/ref-lease enforcement. When a provider cannot enforce
that condition, atomically reserve the action in the claim store and prevent takeover through its
completion; if neither mechanism is available, automatic mutation and takeover fail closed for a
human-owned reconciliation. A stale root must be unable to mutate after a newer generation exists.

## Durable checkpoint protocol

The configured implementation receipt is a write-ahead recovery ledger, not an end-of-run report.
Root durably checkpoints it:

- after every accepted slice, clean commit, and workflow-phase transition;
- before each external mutation with the intended idempotent action and fencing token;
- after each external mutation with its observed tracker/PR/SHA/deployment result; and
- after merge, tracker transition, worktree disposal, and entry into `awaiting-deployment`.

Use host idempotency keys when available. If a crash leaves an intent without a result, recovery
first reconciles live external state and records the observation; it does not repeat the operation
blindly. A checkpoint failure stops before the next mutation.

Dispatches use the same write-ahead discipline. Before any child dispatch, checkpoint the slice ID,
a root-generated dispatch/idempotency ID, verified role-definition digest, expected HEAD and
working-tree status, allowed files, and `in-flight` state. Immediately after dispatch, checkpoint
the host run identity; after completion, checkpoint its terminal result before accepting work. On
resume, reconcile an `in-flight` dispatch with the host and worktree before starting another child.
If the host cannot prove the prior writer terminal or absent, do not redispatch or permit takeover
to write in that worktree.

## Phase 1 — Plan and route by risk

Root decomposes the ticket into vertical behaviour slices sized for one bounded child task.

- Use narrow lookup or exploration profiles only when the answer materially changes the plan.
- For high-risk migrations, concurrency, destructive operations, or cross-system changes, send the
  proposed plan to the mapped plan-verification profile before any writer starts.
- Route explicit auth, secrets, payments, permissions, or destructive trust boundaries through the
  mapped security reviewer; use a security executor only after the security fix is scoped.
- Keep trivial or tightly coupled work in root when delegation overhead would exceed its value.

No child chooses its own role, risk tier, acceptance meaning, or next ticket.

## Phase 2 — Execute TDD slices

For each behaviour slice, root first checkpoints the slice's pre-dispatch `in-flight` reservation
under the durable checkpoint protocol, then dispatches the mapped mechanical or judgment-bearing
executor with the dispatch contract above. The executor runs `tdd` at the approved public seam:

1. demonstrate a valid **RED** caused by the missing behaviour;
2. add the smallest **GREEN** implementation;
3. rerun the focused test and relevant surrounding regression;
4. return the changed files, commands/results, risks, and TDD receipt to root.

Root inspects the diff and evidence before accepting the slice. Reject out-of-scope files,
implementation-coupled tests, invalid REDs, speculative behaviour, or unexplained command failures.
After each accepted slice, run the focused test and a proportionate **typecheck** / lint check, then
make a clean checkpoint commit. Committing GREEN checkpoints ensures review sees the actual
`fixed-point...HEAD` change; children never commit on root's behalf.
Durably checkpoint the receipt after the accepted slice and its commit before dispatching or
mutating anything else.

If implementation discovers a required observable behaviour change, stop and return to the
acceptance-contract gate. Standards-only refactoring keeps tests green; it does not invent a RED.

### Pre-merge P0 QA automation

After the RD TDD slices, root copies the approved **QA automation owner** unchanged for every
approved P0 integration/E2E profile into the ticket/receipt before PR creation, preserving its
**immutable provider principal ID** and **display label**. Compare principal IDs; labels are
informational. This owner is the **accountable owner**; the configured **executing agent role**
performs the bounded write. Any reassignment is an approved-contract content change and returns to
`dev-workflow` Stage 3 for a new revision. Unless the approved contract
carries a still-valid manual exception, treat each profile as a **bounded QA automation write
slice** under the existing dispatch and durable-checkpoint protocol: reserve it before dispatch
with allowed harness files and exact expected HEAD; dispatch the compatible configured write role;
then root inspects the diff and execution evidence, rejects scope or contract drift, runs the
focused harness check, makes a clean checkpoint commit, and records the result in the receipt.
Children never commit.

After that checkpoint commit, root runs the approved automation in its named integration or journey
harness against the clean committed feature-branch HEAD before publication. This automation is
not owned by `tdd`; preserve the approved QA seam, layer, fixtures, required evidence, and risk
probes unchanged. When the PR opens, attach the recorded QA automation owner, profile, and
pre-publication evidence to it.

A manual exception may skip this pre-publication automation only after root re-reads and verifies
all approved exception fields: **current explicit user approval**, that the **follow-up ticket
exists and is open**, its **named owner**, its **unexpired deadline**, the **exact-candidate
execution method**, and the **required evidence**; also verify the **live follow-up-ticket assignee
equals the approved QA automation owner** and the **approved exception owner equals the approved QA
automation owner**. An incomplete, closed, expired, or owner-mismatched exception stops
implementation and returns to `acceptance-design` through `dev-workflow` Stage 3 for a revised
approved contract.

## Phase 3 — Integrate, verify, and review

When all slices are integrated:

1. require a clean working tree and inspect every commit plus `git diff <fixed-point>...HEAD`;
2. run the **full configured suite** once, plus configured typecheck/lint/build steps (`none` skips);
3. resolve each approved P0 integration/E2E profile through exactly one branch:
   - **Without a manual exception:** run it at the committed exact HEAD, checkpoint that HEAD plus
     its result and produced evidence, and require PASS.
   - **When a manual exception is requested:** immediately before this exception-based skip,
     re-read and verify all approved exception fields: **current explicit user approval**, that the
     **follow-up ticket exists and is open**, its **named owner**, its **unexpired deadline**, the
     **exact-candidate execution method**, and the **required evidence**; also verify the **live
     follow-up-ticket assignee equals the approved QA automation owner** and the **approved exception
     owner equals the approved QA automation owner**. If all fields and the owner binding are valid,
     record the skip, exact HEAD, and validation evidence; any invalid field or owner mismatch
     returns to `acceptance-design` through `dev-workflow` Stage 3.
   A **P0 flaky** result is **Not ready**. It must not be quarantined or accepted through an
   infrastructure retry; a green retry alone is not PASS. Diagnose and fix the flake, then rerun at
   the new exact HEAD, or return through `dev-workflow` Stage 3 for the user to approve a complete
   manual exception.
4. dispatch the mandatory independent-verification profile against the ticket, contract, exact
   diff, and commands; it may create test artifacts but must not edit source code;
5. run `review` with two fresh child runs from the mapped verification profile, the fixed point,
   originating ticket/spec/contract, repository standards, and data-mutation/security gates that
   apply.

Blocking verification/review findings return to a bounded executor or root. Behaviour fixes restart
a RED → GREEN slice; standards-only fixes keep tests green. Commit fixes, rerun affected checks,
the full configured gate when impact warrants it, and independent review until no blockers remain.
Every fix commit invalidates the prior P0 exact-HEAD receipt; repeat step 3 at the new clean
committed HEAD and checkpoint its replacement evidence before continuing to publication.

## Phase 4 — Publish exact evidence

Root alone:

1. fetch the integration branch. If it advanced, rebase safely, **recompute the fixed point** from
   the new integration head, and treat the prior review/verification evidence as superseded. After
   any rebase or conflict resolution, require a clean tree and rerun the full configured gate,
   independent verification, and `review` against the new `fixed-point...HEAD` before publishing.
   Every rebase or conflict-resolution commit invalidates the prior P0 receipt: repeat Phase 3
   step 3 at the new exact HEAD and checkpoint its replacement evidence. In every case, checkpoint
   the expected target HEAD alongside every pre-publication P0/review evidence set;
2. before push, confirm the P0 receipt's HEAD matches the current HEAD. For an exception, **freshly
   re-read live exception state**—all **six fields**, the **approved exception owner**, the **live
   assignee**, and both **owner match** comparisons—and checkpoint the observed values and time; a
   mismatch returns to Stage 3. Otherwise repeat Phase 3 step 3. Then apply the fencing check and
   receipt write-ahead protocol, push the feature branch, and open/update one PR targeting the
   integration branch;
3. attach the contract revision, SC-ID → AC-ID trace, TDD receipts, fixed point, commit list, and
   verification results;
4. run the **remote feedback loop** on the exact head SHA. Classify review change requests and CI
   failures before editing: approved-behaviour defects use a bounded RED → GREEN slice;
   **standards-only** fixes keep tests green; requested contract changes return to the acceptance
   gate. Commit valid fixes and rerun affected plus full configured checks. Every such commit
   invalidates the P0 receipt: before the next push, repeat Phase 3 step 3 and checkpoint the new
   exact HEAD, result, and evidence (or the freshly validated six-field exception). Then rerun the
   **independent outcome verifier** and two fresh review runs, push a new HEAD, and wait again.
   Before any retry, require **checkpointed proof** that the approved **profile/test never started**
   or that a named **provider incident** caused the failure. Only then is an infrastructure retry
   permitted within the configured bound. Any **test-started or ambiguous** P0 failure is **Not
   ready**. A **P0 flaky** result is **Not ready** and must not be quarantined or treated as
   infrastructure; diagnose and fix it, or return through `dev-workflow` Stage 3 for a complete
   manual exception. After remote review and CI settle, checkpoint the exact PR HEAD + expected
   target HEAD with the resulting P0/review/CI evidence set;
5. proceed only when required review and CI are green on the new **exact PR head SHA**—stale green
   checks do not count. Required CI includes every approved P0 integration/E2E automation profile;
   rerun it after every new commit or rebase unless the validated manual exception applies. Before
   every exception-based skip in this remote loop, re-read and verify all approved exception fields:
   **current explicit user approval**, that the **follow-up ticket exists and is open**, its
   **named owner**, its **unexpired deadline**, the **exact-candidate execution method**, and the
   **required evidence**; also verify the **live follow-up-ticket assignee equals the approved QA
   automation owner** and the **approved exception owner equals the approved QA automation owner**.
   Any owner mismatch returns to `acceptance-design` through `dev-workflow` Stage 3; prior validation
   is not reusable;
6. immediately before merge authorization, **fetch the target branch** and require both the
   **exact PR HEAD** and **expected target HEAD** to equal the pair bound to the latest P0,
   review, and CI evidence. If either differs, return to Phase 4 step 1 to rebase, recompute the
   fixed point, and rerun P0, review, and CI. Then perform the fresh fencing check and re-read all
   approved exception fields when an exception is being used: **current explicit user approval**,
   that the **follow-up ticket exists and is open**, its **named owner**, its **unexpired deadline**,
   the **exact-candidate execution method**, and the **required evidence**; also verify the **live
   follow-up-ticket assignee equals the approved QA automation owner** and the **approved exception
   owner equals the approved QA automation owner**. Any invalid state or owner mismatch stops and
   returns to `acceptance-design` through `dev-workflow` Stage 3.

   Checkpoint the merge intent bound to that exact PR-HEAD/target-HEAD pair. Enforce it with
   **CAS/ref-lease** where policy permits automation. For a protected or single-branch repository,
   issue a short-lived human merge authorization bound to the pair; **pre-merge authorization is
   not a merge receipt**. **At the actual human merge action**, re-fetch both refs and revalidate all
   exception fields by immutable **provider principal IDs**, then capture the provider
   **merge timestamp** and actual-action snapshot. The provider result becomes the **observed human
   merge receipt**, bound to the pair, actor principal ID, exception snapshot, and observed merge
   SHA. If that action-time check/receipt cannot be obtained, fail closed for human reconciliation.

   Only after the applicable atomic or action-time check, merge only under the configured branch
   policy; never autonomously merge a protected release branch or auto-merge a single-branch
   repository. Checkpoint the observed merge SHA and verify the **observed merge derives from that
   exact pair**;
7. run the idempotent **post-merge reconciliation** path: revalidate fencing, update the tracker to
   development-complete/awaiting-deployment, verify no process/session uses the clean merged feature
   worktree, then perform worktree **cleanup** immediately and checkpoint
   `worktree-disposed=true`. If cleanup is temporarily unsafe, retain the post-merge phase and retry
   disposal on resume; do not skip it or recreate/reuse the merged branch. If a later local build is
   required, use a detached build-only worktree under `<repo-root>/.worktrees/` at the exact merged
   SHA and remove it after artifact production;
8. obtain a **deployment receipt** for the configured non-production test environment: deployed
   source SHA, artifact/environment revision, status, URL/access path, and fixtures. Verify the
   artifact was built from the merged source. If deployment is manual or unavailable, mark the
   ticket `awaiting deployment` and stop before QA until an external receipt supplies this evidence;
9. update the tracker with PR/merge/deployment evidence and the awaiting-QA state—do not close
   acceptance early.

## Stop and recovery

Stop without guessing on: missing/drifted required profiles, dirty or active worktrees, invalid
fixed point, stale acceptance contract, unrelated red baseline, invalid RED, scope/behaviour drift,
overlapping writers, failed atomic claim, unavailable independent/security verification, merge
conflicts that change behaviour, failed required CI, missing deployment receipt, or protected-branch
authorization.

On a handled interruption, leave the branch/worktree recoverable and update the already-durable
**implementation receipt** in the configured ticket/PR—not a transient scratch note. Hard
termination recovery relies on the checkpoint protocol above rather than an interruption handler:

- ticket + acceptance-contract revision and SC-ID → AC-ID scope;
- claim owner, lease/heartbeat, claim-generation fencing token, role-definition digests, and allowed
  resume/release/takeover action;
- workflow phase, PR, merge SHA, deployment state, and whether the feature worktree was disposed;
- fixed point, branch, worktree, current HEAD, and clean/dirty state;
- completed/current/remaining slices and assigned role profiles;
- RED/GREEN/regression/static/full-suite commands and results;
- review/CI state at the exact head SHA and any deployment/artifact receipt;
- each P0 profile, its QA automation owner, exact-HEAD result and produced evidence, plus the
  manual-exception six fields, observed live ticket assignee, owner-match result, and last
  validation time when an exception applies;
- the exact PR-HEAD/expected-target-HEAD pair for every P0/review/CI evidence set, plus the
  merge-intent enforcement and observed-derivation state;
- blocker, next safe action, and any required human judgment.
