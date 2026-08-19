---
name: bug-workflow
description: >-
  Turn a test non-pass into one traceable Bug Case, classify it before diagnosis, and route it to the
  correct owner without losing evidence. Use after testing-workflow records FAIL, FLAKY, BLOCKED,
  or NOT TESTED, or when someone asks to triage a test finding.
---

# bug-workflow

Create one durable Bug Case from test evidence, then classify before choosing an owner. This is a
triage workflow: it does not diagnose every failure, change product code, or run the repaired
artifact. Write it from `bug-case-template.md` to `.harness-ship/bugs/<BUG-ID>.md`.

## 1 — Intake one Bug Case

Start from the failing attempt in `.harness-ship/candidates/<short-sha>/ledger.md` — that directory
takes the contract's **Candidate identifier** where its **Release surface owner** is not this
repository — and the validated
handoff beside it at `handoff.md`. Preserve:

- Test Contract revision, scenario ID, and originating work;
- full source SHA — or the candidate identifier where the contract's **Release surface owner** is not
  this repository — exact tested artifact/environment revision, and provenance receipt;
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

- `product-defect` → diagnosis through `diagnose` when root cause is not already established; append
  its Diagnosis Receipt to the same BUG-ID.
- `test-defect` → test maintenance through `exploratory-testing`; preserve the product observation.
- `environment-defect` → configured environment owner; include the failing environment receipt.
- `spec-ambiguity` → `test-plan`; approve a new Test Contract revision before any behaviour
  change.
- `duplicate` → canonical BUG-ID; link the canonical case and stop parallel defect handling.
- `known-limitation` → record explicit scope and user impact; require human disposition.

Only `product-defect` may enter diagnosis. Never use a generic failure label as permission to run
`diagnose`.

## 3 — Route or pause honestly

Append the owner, next action, timestamp, and evidence link to the history. `blocked` and
`needs-evidence` are resumable phases, not closure dispositions: record the blocker or missing
evidence plus the exact resume condition, then stop without pretending triage completed.

Write the Bug Case to `.harness-ship/bugs/<BUG-ID>.md` regardless of tracker availability. Use the
configured tracker adapter to publish or update the same case and mirror its ID into the file. If
the tracker adapter is unavailable, state exactly **publication did not occur** and preserve the
next safe action. Do not invent a tracker ID, publication receipt, or successful handoff.

For every non-product classification, this workflow ends after classification and routing.

## 4 — Repair handoff and return

For a diagnosed `product-defect`, append a **repair handoff** containing:

- stable BUG-ID, Test Contract trace, and original failed-candidate evidence;
- Diagnosis Receipt when one exists;
- falsifiable root cause or unresolved uncertainty;
- the root cause's **reach** as the Diagnosis Receipt established it — every affected caller, not
  only the one this Bug Case reported;
- expected fixed behaviour and affected scenarios; and
- the exact evidence a future candidate must provide for retest.

Carrying a narrower reach than the receipt established leaves the identical defect in every sibling
caller, where it returns later as a separate Bug Case.

Then stop. The user or host agent chooses the repair process; Harness Ship never requires
a development workflow, a branch strategy, or a deployment method.

When a fixed candidate returns, append its repair summary, whichever of the two this Bug Case
already records, exact artifact and
provenance receipt, then resume `testing-workflow`. Every repair and retest remains under the same
BUG-ID. Never overwrite the failed artifact or infer verification from implementation evidence.
