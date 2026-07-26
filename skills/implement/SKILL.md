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

**Prerequisite:** read the project's `## harness-ship` **Config version 1** block in `AGENTS.md` /
`CLAUDE.md`. It must identify the tracker and PR access paths, branch topology, classified RD/QA
commands, configured checks, and **Agent role profiles**. If it is absent, legacy or unversioned,
or lacks role profiles, run `setup` and stop before delegating or running a baseline. Do not
reinterpret a legacy generic test command.

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
8. for **every pre-handoff child**, a hard constraint: do not run or consume any QA integration,
   P0, or full-suite command or job; use only its authorized RD command/check scope.

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
   evidence proves the PR merged, enter the dedicated **post-merge reconciliation** path: finish the
   development-complete tracker transition, safely dispose the recorded feature worktree until
   `worktree-disposed=true`, and only then handle deployment. Do not reuse the merged branch.
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
7. Run a narrow **baseline** using only the applicable configured **RD unit** and
   **RD API-contract** commands at approved RD seams, plus the cheapest configured static check.
   Do not run or consume any QA integration, P0, or full-suite command before the dev→QA handoff.
   An applicable `not-configured` RD command is reported as missing; it is never replaced with a QA
   command or inferred PASS. Pre-existing failures stop the ticket; record them without rewriting
   the contract.

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

## Phase 3 — Integrate, verify, and review

When all slices are integrated:

1. require a clean working tree and inspect every commit plus `git diff <fixed-point>...HEAD`;
2. run the full configured **RD verification gate** once: the RD unit command, RD API-contract
   command, and configured typecheck/lint/build steps (`none` skips). Do not run or consume any QA
   integration, P0, or full-suite command before the dev→QA handoff. An applicable
   `not-configured` RD command is reported as missing, never replaced with a QA command or inferred
   PASS;
3. dispatch the mandatory **RD-owned independent verification** profile against the ticket,
   contract, exact diff, and the configured RD verification-gate commands. It may create RD
   verification artifacts but must not edit source code. It must not run or consume any QA
   integration, P0, or full-suite command or job before the dev→QA handoff;
4. run `review` with two fresh child runs from the mapped verification profile, the fixed point,
   originating ticket/spec/contract, repository standards, and data-mutation/security gates that
   apply. Each is an **RD-owned pre-handoff review**: it may inspect the diff, RD verification
   evidence, and non-QA checks, but must not run or consume any QA command or job.

Blocking verification/review findings return to a bounded executor or root. Behaviour fixes restart
a RED → GREEN slice; standards-only fixes keep tests green. Commit fixes, rerun affected checks,
the full RD verification gate when impact warrants it, and independent review until no blockers
remain.

## Phase 4 — Publish exact evidence

Root alone:

Until the QA handoff is valid, rerun the **CI ownership preflight** immediately before every
trigger-capable mutation: initial push, retry push, PR open/update, merge/integration push,
deployment mutation, workflow dispatch, job rerun, and infrastructure retry. Immediately before
each, re-read the current Config v1 and the current remote workflow and job wiring. If a QA-owned or
**unclassified test job** would launch, stop before the mutation; only positively classified RD
verification jobs and automatic non-QA branch-required checks may proceed.

1. fetch the integration branch. If it advanced, rebase safely, **recompute the fixed point** from
   the new integration head, and treat the prior review/verification evidence as superseded. After
   any rebase or conflict resolution, require a clean tree and rerun the full RD verification gate,
   independent verification, and `review` against the new `fixed-point...HEAD` before publishing.
   Apply the same **RD-only pre-handoff review boundary**: these runs must not run or consume any QA
   command or job;
2. before any push or PR mutation, run a **CI ownership preflight**: inspect the exact workflow
   triggers and job-command wiring plus the Config v1 QA command mappings. If pushing the branch or
   opening/updating the PR would automatically launch a QA integration, P0, or full-suite job, stop
   before the mutation. Automatically triggered non-QA branch-required checks remain allowed. Once
   the preflight passes, apply the fencing check and receipt write-ahead protocol, then push the
   feature branch and open/update one PR targeting the integration branch;
3. attach the contract revision, SC-ID → AC-ID trace, TDD receipts, fixed point, commit list, and
   verification results;
4. run the **remote feedback loop** on the exact head SHA. Before handoff, only **RD-owned CI**
   verification jobs may be actively triggered or counted as RD test evidence. Rerun the CI
   ownership preflight immediately before every workflow dispatch or job rerun. Triggering a QA
   integration, P0, or full-suite job here is an **ownership violation**: stop, and do not trigger
   or consume any QA command or job as merge evidence. Automatically triggered **non-QA
   branch-required checks**—such as security, license, provenance, or policy—may run and must pass,
   but are not RD test evidence. Classify review change requests and RD-owned CI failures before
   editing: approved-behaviour defects use a bounded RED → GREEN slice;
   **standards-only** fixes keep tests green; requested contract changes return to the acceptance
   gate. Commit valid fixes and rerun affected plus the full RD verification gate. Rerun the
   **independent outcome verifier** and two fresh review runs under the same **RD-only pre-handoff
   review boundary**; they must not run or consume any QA command or job. Rerun the CI ownership
   preflight immediately, then push a new HEAD and wait again. Rerun the CI ownership preflight
   immediately before each infrastructure retry. Retry unrelated infrastructure failures only
   within the configured bound, then stop with evidence;
5. proceed only when required review, RD-owned CI, and all other non-QA branch-required checks are
   green on the new **exact head SHA**—stale green checks and QA-owned jobs do not count;
6. rerun the CI ownership preflight immediately before merge. After a fresh fencing check and
   pre-mutation checkpoint, merge only under the configured branch policy. Never autonomously merge
   a protected release branch or auto-merge a single-branch repository. Checkpoint the observed
   merge SHA immediately;
7. run the idempotent **post-merge reconciliation** path: revalidate fencing, update the tracker to
   development-complete/awaiting-deployment, verify no process/session uses the clean merged feature
   worktree, then perform worktree **cleanup** immediately and checkpoint
   `worktree-disposed=true`. If cleanup is temporarily unsafe, retain the post-merge phase and retry
   disposal on resume; do not skip it or recreate/reuse the merged branch. If a later local build is
   required, use a detached build-only worktree under `<repo-root>/.worktrees/` at the exact merged
   SHA and remove it after artifact production;
8. obtain a **deployment receipt** for the configured non-production test environment. Before any
   deployment-triggering mutation, rerun the CI ownership preflight and stop on a QA-owned or
   unclassified test job. Record deployed source SHA, artifact/environment revision, status,
   URL/access path, and fixtures. Verify the artifact was built from the merged source. If
   deployment is manual or unavailable, mark the ticket `awaiting deployment` and stop before QA
   until an external receipt supplies this evidence;
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
- RD unit/API-contract RED/GREEN/regression commands plus static-check commands and results;
- review/CI state at the exact head SHA and any deployment/artifact receipt;
- blocker, next safe action, and any required human judgment.
