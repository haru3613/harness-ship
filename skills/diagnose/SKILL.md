---
name: diagnose
description: >-
  Root-cause an already-triaged product defect by building a red-capable, deterministic
  reproduction when safe, then ranking falsifiable hypotheses and emitting a Diagnosis Receipt.
  Use for a product defect needing substantial root-cause investigation. This skill diagnoses; it does not edit product code. Triggers: "/diagnose",
  "root-cause this product defect", "diagnose BUG-ID".
---

# diagnose

Find the real cause, not a plausible one, and publish a bounded **Diagnosis Receipt** for a repair
handoff. `diagnose` does not edit product code, create a replacement defect, choose a repair
workflow, or mark
the Bug Case `verified`.

Classify the observation first: product behaviour, test defect, environment problem, or ambiguous
expectation. A formal BUG-ID or Test Contract is not required. Resolve routine non-product problems
within authorized scope; use `bug-workflow` when durable tracking or handoff is useful.

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

Use [diagnosis-receipt-template.md](diagnosis-receipt-template.md) only when its detail helps.
Append findings to the existing issue or chosen record, preserving previous attempts. The legacy
`.harness-ship/bugs/<BUG-ID>.md` location remains supported without a mandatory local mirror.
Return one outcome:

- `diagnosed` — evidence identifies a falsifiable root cause and a safe repair seam;
- `inconclusive` — safe observations exist, but the evidence does not distinguish the remaining
  hypotheses; or
- `reproduction-blocked` — a safe observation cannot currently be obtained.

`inconclusive` and `reproduction-blocked` are resumable outcomes, not guesses or closure. Record the
missing evidence and exact resume condition. Do not force a diagnosis.

A `diagnosed` root cause is not established until its **reach** is: enumerate the callers and entry
points of the root cause and record, for each, the evidence that it is affected or the evidence that
rules it out. A seam narrowed to the caller the report happened to name leaves the identical defect
in every sibling caller, where it returns later as a separate Bug Case. An unenumerated caller is not
a caller ruled out; when reach cannot be established from safe observation, the outcome is
`inconclusive` with the missing evidence recorded, never `diagnosed` with a narrower seam.

## Handoff

A `diagnosed` receipt supplies the root cause, its reach, safe repair seam, expected fixed behaviour,
and retest conditions. Record it in the same summary. The host continues already-authorized repair and retesting using
the repository workflow; return a handoff only when another owner or session must take over.
