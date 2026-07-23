---
name: tickets
description: >-
  Break a spec or plan into vertical-slice tracer-bullet tickets — each a narrow but complete path
  through every layer, demoable on its own, with blocking edges and per-ticket acceptance criteria.
  Use after a spec, before implementing. Triggers: "/tickets", "break this into tickets", "split the
  work", "make issues".
---

# tickets

Break the work into **tracer-bullet** tickets. The goal is a set of small, independently shippable
units an agent (or a person) can pick up one at a time in a fresh context.

## Vertical-slice rules

- Each slice cuts a **narrow but COMPLETE path through every layer** (schema → API → UI → tests).
  Vertical, never a horizontal slice of one layer ("do all the backend first" is the anti-pattern).
- A completed slice is **demoable or verifiable on its own**.
- Each slice fits in **one fresh context window**.
- Any prefactor ("make the change easy, then make the easy change") is its own first ticket.

## Each ticket carries

- **Title** — short, in the project's domain vocabulary.
- **What to build** — the end-to-end behaviour this makes work, from the user's view. Not a
  layer-by-layer task list. No file paths (they go stale).
- **Blocked by** — the tickets that must finish first, or "None — can start immediately."
- **Acceptance criteria** — a checklist. Each item is independently checkable.

## Wide refactors are the exception

A mechanical change whose blast radius breaks thousands of call sites at once (rename a column,
retype a shared symbol) can't land green as one tracer bullet. Sequence it **expand → migrate →
contract**: add the new form beside the old (nothing breaks) → migrate call sites in blast-radius
batches, each its own ticket blocked by the expand, CI green batch to batch → delete the old form,
blocked by every migrate batch. If batches can't stay green alone, share an integration branch that
all block a final integrate-and-verify ticket.

## Publish + work

Publish to the tracker named in the project's `## harness-ship` config (run `setup` if absent),
blockers first, so each ticket's edges can reference real IDs; apply that config's agent-ready
signal (a label, a Jira status, or a sprint — whatever the tracker uses; skip if `none`). Then
**work the frontier** — any ticket whose blockers are all done — one at a time,
clearing context between them.

## Quiz the user (the granularity gate)

Present the breakdown as a numbered list (title · blocked-by · what it delivers) and ask: is the
granularity right? are the blocking edges correct? should any merge or split? Iterate until approved
— this is a human gate, don't publish before it.
