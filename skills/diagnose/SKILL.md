---
name: diagnose
description: >-
  Root-cause an already-triaged product defect by building a red-capable, deterministic
  reproduction when safe, then ranking falsifiable hypotheses and emitting a Diagnosis Receipt.
  For a test finding, use only after bug-workflow supplies a stable BUG-ID classified
  product-defect. This skill diagnoses; it does not edit product code. Triggers: "/diagnose",
  "root-cause this product defect", "diagnose BUG-ID".
---

# diagnose

Find the real cause, not a plausible one, and publish a bounded **Diagnosis Receipt** for a repair
handoff. `diagnose` does not edit product code, create a replacement defect, choose a repair
workflow, or mark
the Bug Case `verified`.

**Test boundary:** if the input came from `testing-workflow`, require an existing stable BUG-ID
whose classification is `product-defect`. Otherwise run `bug-workflow` and stop; do not bypass
classification.

## 1 — Establish a safe observation

Prefer one deterministic, red-capable command at the smallest safe seam. Never force an unsafe,
destructive, production-only, or inherently intermittent observation through a dangerous
reproduction. Use bounded non-destructive evidence instead and record why the reproduction cannot
be made safe.

## 2 — Rank falsifiable hypotheses

List candidate causes, each stated so a single observation could **disprove** it. Test the cheapest
distinguishing observation first. Follow the evidence at each layer; don't pattern-match to a past
fix.

**On a recurrence** of a symptom "we fixed last time": do not adopt the previous diagnosis. Find the
prior incident, then run one distinguishing query (DB / log / API) that **disproves** the old root
cause before you accept it. "Plausible because it matches last time" is exactly the trap.

## 3 — Append the Diagnosis Receipt

Use `diagnosis-receipt-template.md` and append one outcome to the same stable BUG-ID:

- `diagnosed` — evidence identifies a falsifiable root cause and a safe repair seam;
- `inconclusive` — safe observations exist, but the evidence does not distinguish the remaining
  hypotheses; or
- `reproduction-blocked` — a safe observation cannot currently be obtained.

`inconclusive` and `reproduction-blocked` are resumable outcomes, not guesses or closure. Record the
missing evidence and exact resume condition. Do not force a diagnosis.

## Handoff

A `diagnosed` receipt supplies the root cause, safe repair seam, expected fixed behaviour, and retest
conditions. Append it to the Bug Case and stop. The user or host agent chooses how to repair and
produce a new candidate; `testing-workflow` verifies that exact candidate later.
