---
name: dev-workflow
description: >-
  Orchestrate a feature from a raw idea to shipped code, with humans on the ends and AI in the
  middle. Use when someone brings a feature request, a "can we even build this?" idea, or says
  /dev-workflow — anything that needs clarifying → feasibility → spec → tickets → implement → hand to
  QA. Triggers: "/dev-workflow", "I want to build X", "new feature", "not sure if this is possible
  but…", "help me spec and ship".
---

# dev-workflow

Take a feature from a **rough idea** to **merged code**. The shape is deliberate:

> **Humans hold the ends, AI runs the middle.** The user pilots four judgment gates (feasibility,
> ticket granularity, UI 定稿, acceptance). Everything between them is automated.

**Prerequisite:** read the project's `## harness-ship` config (tracker, integration vs protected
branch, test/lint commands, safety gate) in `AGENTS.md` / `CLAUDE.md`. If it is absent, run `setup`
first — otherwise the stages below fall back to generic guesses.

## Operating principle — bring out the 90%

Assume the user has stated ~10% of what the feature needs. Surface the other 90% **not by
interrogating them**, but by answering it yourself with stated assumptions and explaining *why*, then
asking only about the few forks where the answer changes the plan. Automate the labour, leave the
judgment. If a decision is a content/creative/taste call, it stays the user's — say so.

## The four human gates

1. **Feasibility** — go / spike-first / split / no (Stage 1).
2. **Ticket granularity** — are the slices and dependencies right (Stage 3).
3. **UI 定稿** — for UI features, the design is approved before backend (Stage 2).
4. **Acceptance** — after `testing-workflow` produces the acceptance report.

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
publish to the project's configured tracker. It does not re-interview — Stage 0 did that.

**For UI features**, lock the design first (front-end-first): approve a mock/prototype of the UI
*before* backend work, so the UI is a testable part of the spec. That approval is gate 3.

## Stage 3 — Tickets

Run **`tickets`**: break the spec into vertical-slice tracer-bullet tickets — each demoable on its
own, sized to one context window, with blocking edges and per-ticket acceptance criteria — and
publish to the tracker, blockers first. **Gate:** user confirms granularity + dependency edges.

## Stage 4 — Implement (automated middle)

**First, sweep worktrees** so cleanup doesn't rely on the happy path completing (dead sessions leak
worktrees):

```bash
git worktree prune
# remove worktrees whose branch is already merged into the integration branch
```

Then drive the frontier ticket (all blockers done). Per ticket, non-negotiable:

- **one feature = one worktree = one PR**, based on the integration branch.
- **TDD** at the spec's seams — cover the behaviour and the edge cases that matter, not a blanket
  coverage %.
- **Code review = `review`** (dual-axis Standards × Spec; enable its data-mutation safety gate if the
  project has batch/cron DB writers).
- **A pre-push gate** — typecheck / lint / test / review all green before push.
- Merge to the **integration branch**. **NEVER** merge to a protected release branch — that's a human
  + release gate.
- **Clean up the worktree right after merge**, verifying no other session uses it.

*(If you have an autonomous implement loop available — e.g. a `ship-loop` skill — this stage can
delegate to it; otherwise drive tickets one at a time with the discipline above.)*

## Stage 5 — Hand to QA

Write a **QA handoff** onto the PR/ticket (not a scratch file, not a "resume the work" note — QA
needs to know what to *verify*):

- **What changed** (user-facing behaviour, per ticket).
- **Each acceptance criterion to verify** (from the ticket).
- **How to reach it**: test URL / environment + fixtures/accounts + seed data.
- **Known risks / edge cases** worth probing.
- **What unit + contract tests already cover** — so QA focuses on integration + journeys, no
  duplication.

Then trigger **`testing-workflow`**. Its acceptance report is gate 4 — the user signs off. Bugs loop
back as new tickets (Stage 3).
