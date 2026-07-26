---
name: dev-workflow
description: >-
  Orchestrate a feature from a raw idea to shipped code, with humans on the ends and AI in the
  middle. Use when someone brings a feature request, a "can we even build this?" idea, or says
  /dev-workflow — anything that needs clarifying → feasibility → spec → acceptance contract →
  tickets → implement → hand to QA. Triggers: "/dev-workflow", "I want to build X", "new feature",
  "not sure if this is possible but…", "help me spec and ship".
---

# dev-workflow

Take a feature from a **rough idea** to **merged code**. The shape is deliberate:

> **Humans hold the ends, AI runs the middle.** The user pilots five judgment gates (feasibility,
> UI 定稿, acceptance contract, ticket granularity, acceptance). Everything between them is
> automated.

**Prerequisite:** read the project's `## harness-ship` config (tracker, integration vs protected
branch, test/lint commands, safety gate) in `AGENTS.md` / `CLAUDE.md`. If it is absent, run `setup`
first — otherwise the stages below fall back to generic guesses.

## Operating principle — bring out the 90%

Assume the user has stated ~10% of what the feature needs. Surface the other 90% **not by
interrogating them**, but by answering it yourself with stated assumptions and explaining *why*, then
asking only about the few forks where the answer changes the plan. Automate the labour, leave the
judgment. If a decision is a content/creative/taste call, it stays the user's — say so.

## The five human gates

1. **Feasibility** — go / spike-first / split / no (Stage 1).
2. **UI 定稿** — for UI features, the design is approved before backend (Stage 2).
3. **Acceptance contract** — do the pre-implementation scenarios describe the right behaviour
   (Stage 3).
4. **Ticket granularity** — are the slices and dependencies right (Stage 4).
5. **Acceptance** — after `testing-workflow` produces the acceptance report (Stage 6).

Never sail past a gate autonomously. Between gates, don't stall for permission.

---

## Stage 0 — Clarify

Run **`clarify`**: pull out the 90% the user didn't state by answering it with stated assumptions,
and ask only the ≤4 load-bearing forks. Output is an Assumptions list + the answered forks. This is
the cognitive-gap step — do not skip it into a spec built on guesses.

## Stage 1 — Feasibility gate

Emit an explicit verdict — nothing downstream starts without it:

| Verdict | Meaning | Next |
|---|---|---|
| `feasible` | known-good technical path | → Stage 2 |
| `needs-spike` | one real unknown blocks confidence | → run `spike`, then re-verdict |
| `split` | too big to reason about as one thing | → decompose, verdict each part |
| `infeasible` | can't be done / cost far exceeds value | → explain **why**, offer alternatives |

Always name the **top 2–3 risks** and why. For `needs-spike`, run **`spike`** (time-boxed, returns
its own feasible / not / needs-more verdict). The prototype is throwaway; only its answer folds
forward. **Gate:** user approves the direction.

## Stage 2 — Spec

Run **`spec`**: synthesize the conversation into a spec/PRD anchored at the highest test seam, and
publish to the project's configured tracker. The spec includes stable, externally observable
acceptance criteria. It does not re-interview — Stage 0 did that.

**For UI features**, lock the design first (front-end-first): approve a mock/prototype of the UI
*before* backend work, so the UI is a testable part of the spec. That approval is gate 2.

## Stage 3 — Acceptance contract

Run **Stage 1 of `testing-workflow`** against the current spec: turn its acceptance criteria into
platform-neutral Given/When/Then scenarios, negative assertions, and a P0/P1 matrix. Publish the
scenario set alongside the spec.

**Stop after scenario design. Do not implement or generate test-runner code yet. Gate:** the user
confirms the spec criteria and scenarios describe the right behaviour. Together they become the
approved acceptance contract, identified by contract revision and stable scenario IDs; any later
behaviour change returns here for re-approval and a new revision.

## Stage 4 — Tickets

Run **`tickets`**: break the approved spec and acceptance contract into vertical-slice tracer-bullet
tickets — each demoable on its own, sized to one context window, with blocking edges and per-ticket
acceptance criteria traced to the approved scenarios — and publish to the tracker, blockers first.
**Gate:** user confirms granularity + dependency edges.

## Stage 5 — Implement (automated middle)

Run **`implement`** once per frontier ticket. It is the only implementation orchestrator: the
main/root session owns planning, role routing, integration, Git/tracker/PR state, and the final
decision; bounded work is delegated only to the host's pre-defined role profiles recorded by
`setup`.

`implement` pins the exact base/fixed point, creates one repository-local worktree and PR, drives
approved behaviour slices through `tdd`, integrates clean GREEN checkpoint commits, runs
independent verification plus fixed-point `review`, and waits for required CI on the exact head SHA
before policy-allowed merge and cleanup. It also writes a durable implementation receipt so an
interrupted ticket resumes from evidence rather than conversation.

No extra human gate is added here. Observable behaviour changes return to Stage 3; missing or
drifted required role profiles, invalid baselines/REDs, unavailable independent verification, and
protected-branch decisions stop safely under `implement`'s rules.

## Stage 6 — Hand to QA

Write a **QA handoff** onto the PR/ticket (not a scratch file, not a "resume the work" note — QA
needs to know what to *verify*):

- **What changed** (user-facing behaviour, per ticket).
- **The acceptance-contract revision**, approved scenario IDs, and each criterion to verify.
- **The exact source commit and deployed artifact/environment revision** under test.
- **How to reach it**: test URL / environment + fixtures/accounts + seed data.
- **Known risks / edge cases** worth probing.
- **The TDD receipt and what unit + contract tests cover** — so QA focuses on integration +
  journeys, no duplication.

Then resume **`testing-workflow` at Stage 2**; do not redesign the approved scenarios from the
implementation. Its acceptance report is gate 5 — the user signs off. Bugs loop back as new tickets
(Stage 4).
