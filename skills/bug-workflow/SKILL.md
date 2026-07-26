---
name: bug-workflow
description: >-
  Turn a QA non-pass into one traceable Bug Case, classify it before diagnosis, and route it to the
  correct owner without losing evidence. Use after testing-workflow records FAIL, FLAKY, BLOCKED,
  or NOT TESTED, or when someone asks to triage a QA finding.
---

# bug-workflow

Create one durable Bug Case from QA evidence, then classify before choosing an owner. This is a QA
triage workflow: it does not diagnose every failure, change product code, or run the repaired
artifact. Use `bug-case-template.md` as the portable record.

## 1 — Intake one Bug Case

Start from the execution-ledger attempt and validated QA handoff. Preserve:

- acceptance contract revision and `SC-ID → AC-ID → originating ticket`;
- full source SHA, exact tested artifact/environment revision, and provenance receipt;
- expected and actual behaviour, reproducibility, and durable evidence.

Assign one **stable BUG-ID** once. If the tracker publishes the case, use its ID; otherwise assign a
portable local BUG-ID. Every later classification, handoff, diagnosis, and retest is an append-only
event under that same ID. Never replace the Bug Case with a new defect and never rewrite history.

Keep these independent fields:

- **phase** — where triage currently is;
- **classification** — what kind of finding the evidence supports; and
- **disposition** — the current routing decision.

## 2 — Classify before diagnosis

Choose exactly one classification and append the evidence for that choice:

- `product-defect` → RD diagnosis through `diagnose`; append its Diagnosis Receipt to the same
  BUG-ID.
- `test-defect` → QA maintenance; preserve the product observation and repair the QA asset.
- `environment-defect` → configured environment owner; include the failing environment receipt.
- `spec-ambiguity` → `acceptance-design`; approve a new contract revision before any behaviour
  change.
- `duplicate` → canonical BUG-ID; link the canonical case and stop parallel defect handling.
- `known-limitation` → record explicit scope and user impact; require human disposition.

Only `product-defect` may enter RD diagnosis. Never use a generic failure label as permission to run
`diagnose`.

## 3 — Route or pause honestly

Append the owner, next action, timestamp, and evidence link to the history. `blocked` and
`needs-evidence` are resumable phases, not closure dispositions: record the blocker or missing
evidence plus the exact resume condition, then stop without pretending triage completed.

Use the configured tracker adapter to publish or update the same case. If the tracker adapter is
unavailable, emit the filled **portable Bug Case** from `bug-case-template.md`, state exactly
**publication did not occur**, and preserve the next safe action. Do not invent a tracker ID,
publication receipt, or successful handoff.

For every non-product classification, this workflow ends after classification and routing.

## 4 — Product-defect repair and verification

For a `product-defect`, preserve role ownership while the root/controller advances these four
receipts in order:

1. `diagnose` appends a **Diagnosis Receipt**. Continue only when its status is `diagnosed`;
   `inconclusive` and `reproduction-blocked` remain resumable.
2. `implement` consumes `HS-DEFECT-PACKET/v1`, performs the RD-owned repair, and appends an
   **implement defect receipt**.
3. The configured controller publishes the exact fixed artifact and appends a **new deployment
   receipt**.
4. `testing-workflow` validates that handoff and appends a QA-owned **QA verification attempt**.

Every fix and retest attempt stays append-only under the same stable BUG-ID. Do not overwrite the
original failed artifact, its evidence, or any earlier receipt. Only the final QA step may set
`verified`; release promotion and production rollout remain outside this workflow.
