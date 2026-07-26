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
the **current host's** `Agent role bindings`. Before the first dispatch, verify the live profile's
name, mode/sandbox, model, effort, definition source, write authority, `may_spawn=false`, and
capability boundary against both that binding and the portable `Agent role requirements`. A field
the host cannot expose is `unsupported`, not assumed safe.

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

1. Look first for a receipt-backed existing claim. Apply the configured **resume policy**: resume
   only the same valid owner/session, or use **takeover** only after the recorded lease/heartbeat has
   expired and the takeover rule succeeds. An active claim owned elsewhere stops this root. Read the
   receipt's **workflow phase**, merge SHA, PR, and worktree-disposed state. An
   `awaiting-deployment` **deployment-only resume** validates the merged SHA and jumps directly to
   Phase 4 deployment handling; do not create or resume a feature worktree.
2. For new work, resolve one frontier ticket that matches the configured **ready criteria**.
3. Load the approved spec, acceptance-contract revision, stable scenario/criterion IDs, test seams,
   and explicit out-of-scope list. A stale, missing, or behaviourally contradictory contract stops
   implementation and returns to `dev-workflow` Stage 3.
4. For new work only, atomically apply the configured **claim transition** with the root/session
   identity, immediately persist the initial receipt, then re-read the ticket to verify ownership
   and unchanged contract revision. **Release** a new claim if a terminal validation failure occurs
   before the worktree exists. A receipt-backed resume revalidates its existing claim instead of
   applying a second transition.
5. Inspect `git worktree list`; resume the receipt's exact branch/worktree/HEAD or create one
   repository-local worktree and feature branch from the configured integration branch.
   Never reuse a merged branch or an active/dirty worktree.
6. Record the exact integration-branch SHA and `git merge-base HEAD <integration-ref>` as the
   **fixed point**, plus the branch, worktree path, and starting `git status`.
7. Run a narrow **baseline** at each approved seam and the cheapest configured static check.
   Pre-existing failures stop the ticket; record them without rewriting the contract.

Refresh the claim **heartbeat** during long phases. Every implementation receipt records claim
owner, lease/heartbeat, and the permitted resume/release/takeover action.

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

For each behaviour slice, root dispatches the mapped mechanical or judgment-bearing executor with
the dispatch contract above. The executor runs `tdd` at the approved public seam:

1. demonstrate a valid **RED** caused by the missing behaviour;
2. add the smallest **GREEN** implementation;
3. rerun the focused test and relevant surrounding regression;
4. return the changed files, commands/results, risks, and TDD receipt to root.

Root inspects the diff and evidence before accepting the slice. Reject out-of-scope files,
implementation-coupled tests, invalid REDs, speculative behaviour, or unexplained command failures.
After each accepted slice, run the focused test and a proportionate **typecheck** / lint check, then
make a clean checkpoint commit. Committing GREEN checkpoints ensures review sees the actual
`fixed-point...HEAD` change; children never commit on root's behalf.

If implementation discovers a required observable behaviour change, stop and return to the
acceptance-contract gate. Standards-only refactoring keeps tests green; it does not invent a RED.

## Phase 3 — Integrate, verify, and review

When all slices are integrated:

1. require a clean working tree and inspect every commit plus `git diff <fixed-point>...HEAD`;
2. run the **full configured suite** once, plus configured typecheck/lint/build steps (`none` skips);
3. dispatch the mandatory independent-verification profile against the ticket, contract, exact
   diff, and commands; it may create test artifacts but must not edit source code;
4. run `review` with two fresh child runs from the mapped verification profile, the fixed point,
   originating ticket/spec/contract, repository standards, and data-mutation/security gates that
   apply.

Blocking verification/review findings return to a bounded executor or root. Behaviour fixes restart
a RED → GREEN slice; standards-only fixes keep tests green. Commit fixes, rerun affected checks,
the full configured gate when impact warrants it, and independent review until no blockers remain.

## Phase 4 — Publish exact evidence

Root alone:

1. fetch the integration branch. If it advanced, rebase safely, **recompute the fixed point** from
   the new integration head, and treat the prior review/verification evidence as superseded. After
   any rebase or conflict resolution, require a clean tree and rerun the full configured gate,
   independent verification, and `review` against the new `fixed-point...HEAD` before publishing;
2. push the feature branch and open/update one PR targeting the integration branch;
3. attach the contract revision, SC-ID → AC-ID trace, TDD receipts, fixed point, commit list, and
   verification results;
4. run the **remote feedback loop** on the exact head SHA. Classify review change requests and CI
   failures before editing: approved-behaviour defects use a bounded RED → GREEN slice;
   **standards-only** fixes keep tests green; requested contract changes return to the acceptance
   gate. Commit valid fixes and rerun affected plus full configured checks. Rerun the
   **independent outcome verifier** and two fresh review runs, push a new HEAD, and wait again. Retry unrelated
   infrastructure failures only within the configured bound, then stop with evidence;
5. proceed only when required review and CI are green on the new **exact head SHA**—stale green
   checks do not count;
6. merge only under the configured branch policy. Never autonomously merge a protected release
   branch or auto-merge a single-branch repository;
7. update the tracker to development-complete/awaiting-deployment, verify no process/session uses
   the clean merged feature worktree, then perform worktree **cleanup** immediately. If a later
   local build is required, use a detached build-only worktree at the exact merged SHA and remove it
   after artifact production;
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

On interruption, leave the branch/worktree recoverable and write an **implementation receipt** to
the configured ticket/PR—not a transient scratch note:

- ticket + acceptance-contract revision and SC-ID → AC-ID scope;
- claim owner, lease/heartbeat, and allowed resume/release/takeover action;
- workflow phase, PR, merge SHA, deployment state, and whether the feature worktree was disposed;
- fixed point, branch, worktree, current HEAD, and clean/dirty state;
- completed/current/remaining slices and assigned role profiles;
- RED/GREEN/regression/static/full-suite commands and results;
- review/CI state at the exact head SHA and any deployment/artifact receipt;
- blocker, next safe action, and any required human judgment.
