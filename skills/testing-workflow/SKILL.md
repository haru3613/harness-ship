---
name: testing-workflow
description: >-
  Execute an approved Test Contract against an exact non-production candidate, preserve every
  attempt, and produce the evidence consumed by release-gate. Use after a candidate handoff or when
  someone asks to test a release candidate. Triggers: "/testing-workflow", "test this candidate",
  "verify this artifact".
---

# testing-workflow

Execute the approved Project Test Baseline plus Release Delta. This workflow does not prescribe how
the feature was developed, redesign expected behaviour from implementation, repair product code, or
release the candidate.

Read repository instructions and its `## harness-ship` Config v3 block. Run `setup` only when the
block is absent or unsupported. Resolve test capabilities at the point of use; never install a
framework without approval or infer PASS from `not-configured`.

## 1 — Validate the candidate handoff

Use [candidate-handoff-template.md](candidate-handoff-template.md). Require:

- approved Test Contract revision and scenario scope;
- full source SHA;
- exact non-production artifact/environment revision;
- provenance source and receipt binding the artifact to the SHA;
- writable durable evidence location; and
- access path, safe fixtures/accounts, known risks, and established test evidence.

Any missing, placeholder, stale, or mismatched required value makes the handoff `Not ready`. Do not
execute against production.

## 2 — Select the candidate scope

Execute every required baseline item plus the release delta. Choose the method recorded in the Test
Contract:

- automated command at its approved seam;
- exact manual steps;
- bounded exploratory method; or
- `not-configured`, recorded as NOT RUN / NOT TESTED.

Test layers follow risk and seam stability, not author role. Avoid rerunning equivalent coverage at
multiple layers merely to fill a pyramid.

Exploratory evidence may satisfy only a criterion explicitly marked `manual` or `exploratory`.
Required automation must run on this exact candidate. Evidence from a local, preview, or older
artifact cannot prove a later candidate.

## 3 — Execute append-only

Use [execution-ledger-template.md](execution-ledger-template.md). Immediately before each action,
revalidate the Test Contract revision, source SHA, artifact revision, provenance receipt, evidence
destination, and command/manual method. On drift, append NOT RUN / NOT TESTED and stop that item.

Record every attempt, including PASS, with scenario ID, method, raw outcome, normalized result, and
durable evidence. Never erase retries.

Raw outcomes are PASS, FAIL, BLOCKED, or NOT RUN. Normalize in this order:

1. latest NOT RUN → NOT TESTED;
2. latest BLOCKED → BLOCKED;
3. mixed FAIL and PASS in one run → FLAKY;
4. latest PASS → PASS;
5. latest FAIL → FAIL.

For P0, anything except PASS makes the candidate Not ready. Quarantine never manufactures PASS.

## 4 — Check test quality

Before trusting green evidence, confirm the check observes the approved behaviour through a stable
public seam, uses an independent expected value, and does not ignore runtime/console errors. A weak
or tautological check becomes BLOCKED until corrected and rerun.

## 5 — Report and route

Produce [test-report-template.md](test-report-template.md) from the ledger. State each user journey,
exact candidate, method, evidence, gaps, and one verdict: `Ready for release gate` or `Not ready`.

For every non-pass, run `bug-workflow` under one stable BUG-ID. Harness Ship classifies the finding,
preserves evidence, and emits repair/retest conditions; it does not dictate the repair workflow.

When a fixed candidate returns, require the same BUG-ID, original failed evidence, diagnosis when
available, repair summary, new full source SHA, new artifact/environment revision, new provenance
receipt, affected scenarios, and neighbouring regression scope. Rerun the original observation,
affected scenarios, and proportionate neighbours through this same ledger. Never overwrite the
failed artifact or call implementation evidence a verification result.

`release-gate` consumes this report. Release promotion remains a separate human-authorized action.
