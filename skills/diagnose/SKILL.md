---
name: diagnose
description: >-
  Root-cause an already-triaged product defect by building a red-capable, deterministic
  reproduction FIRST, then ranking falsifiable hypotheses. For a QA finding, use only after
  bug-workflow supplies a stable BUG-ID classified product-defect. Triggers: "/diagnose",
  "root-cause this product defect", "diagnose BUG-ID".
---

# diagnose

Find the real cause, not a plausible one. The discipline that separates this from guess-and-patch is
**a reproduction before a theory**.

**QA boundary:** if the input came from QA or `testing-workflow`, require an existing stable BUG-ID
whose classification is `product-defect`. Otherwise run `bug-workflow` and stop; do not bypass
classification.

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

## Repair authorization boundary

When invoked from a QA Bug Case, Phases 1–2 are diagnosis-only. Append the red repro, tested
hypotheses, and root-cause receipt to the same BUG-ID, then stop without changing product code or
adding a regression test. Enter Phase 3 only when the downstream repair workflow explicitly
authorizes implementation for that Bug Case.

## Phase 3 — fix at the root, once

Fix where all callers route through, not the one path the report named — a report names a symptom;
grep the callers of the function you're about to touch. Add a **regression test at the seam** that
fails before the fix and passes after, so the bug can't return silently.

## Loopback

When `bug-workflow` routes a classified `product-defect` here, append the red repro, tested
hypotheses, and root cause to the existing stable BUG-ID. Do not create a replacement defect. If
implementation work needs a delivery ticket, create a linked ticket via `tickets` so the fix flows
through the normal dev path with its RD-owned regression test.
