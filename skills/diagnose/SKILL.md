---
name: diagnose
description: >-
  Root-cause a bug by building a red-capable, deterministic reproduction FIRST, then ranking
  falsifiable hypotheses — no theorizing before you can make it fail on demand. Use when something is
  broken, flaky, or slow, or on a QA→dev loopback. Triggers: "/diagnose", "debug this", "why is this
  failing", "it's broken", "flaky test", "regression".
---

# diagnose

Find the real cause, not a plausible one. The discipline that separates this from guess-and-patch is
**a reproduction before a theory**.

## Phase 1 — build a red-capable loop (no skipping to Phase 2)

Before any hypothesis, get a **single command that fails deterministically** on the bug — a failing
test, a script, a curl that reliably errors. If you cannot make it fail on demand, you cannot know
when you've fixed it. **No red-capable command → no Phase 2.** For flakiness, make the flake
reproducible (seed, loop, forced timing) before theorizing.

## Phase 2 — rank falsifiable hypotheses

List candidate causes, each stated so a single observation could **disprove** it. Test the cheapest
distinguishing observation first. Follow the evidence at each layer; don't pattern-match to a past
fix.

**On a recurrence** of a symptom "we fixed last time": do not adopt the previous diagnosis. Find the
prior incident, then run one distinguishing query (DB / log / API) that **disproves** the old root
cause before you accept it. "Plausible because it matches last time" is exactly the trap.

## Phase 3 — fix at the root, once

Fix where all callers route through, not the one path the report named — a report names a symptom;
grep the callers of the function you're about to touch. Add a **regression test at the seam** that
fails before the fix and passes after, so the bug can't return silently.

## Loopback

When this runs from a QA failure, file the root cause back as a new ticket (via `tickets`) with the
red repro attached, so the fix flows through the normal dev path with its regression test.
