---
name: spec
description: >-
  Synthesize the current conversation into a spec/PRD — no re-interview, just write down what's
  already been decided, anchored at the highest test seam with explicit acceptance criteria. Use
  after clarifying + feasibility, before acceptance-scenario design and tickets. Triggers: "/spec",
  "write the spec", "turn this into a PRD", "document what we decided".
---

# spec

Turn the conversation and codebase understanding into a spec. Do **not** re-interview the user —
`clarify` already did that. Synthesize what you already know.

## Process

1. **Explore the codebase** enough to use the project's real vocabulary and respect existing ADRs in
   the area you touch.
2. **Choose the test seams.** Sketch where this feature will be tested. Prefer existing seams; use
   the *highest* seam that still isolates the behaviour; the fewer seams, the better (ideal: one).
   Confirm the seams match the user's mental model before writing.
3. **Write the spec** with the template below and publish it to the tracker named in the project's
   `## harness-ship` config (GitHub / Linear / local files); run `setup` if that config is absent.

## Template

```
## Problem
The problem, from the user's perspective.

## Solution
The solution, from the user's perspective.

## User stories
A long, numbered list — "As an <actor>, I want <feature>, so that <benefit>." Cover every aspect.

## Acceptance criteria
Stable AC-IDs with externally observable outcomes. Cover success, rejection/failure, and important
negative behaviour. **Approved AC-IDs are immutable** and never reused: when an approved criterion's
meaning changes, the changed criterion receives a new AC-ID and the spec must retain the superseded
criterion so historical references remain unambiguous. Do not write Given/When/Then here —
`acceptance-design` turns these criteria into the acceptance contract.

## Implementation decisions
Modules to build/modify, interfaces, architectural calls, schema changes, API contracts.
No file paths or code snippets — they go stale. Exception: a decision-encoding snippet from a
spike (state machine, reducer, schema shape), trimmed to the decision-rich parts.

## Test decisions
What makes a good test here (assert external behaviour, not implementation); which modules get
tested; prior art in the codebase; the seams from step 2.

## Out of scope
What this spec deliberately does not cover.
```

Keep it about behaviour and decisions, not a task list — acceptance-scenario design is
`acceptance-design`'s job and task breakdown is `tickets`' job.
