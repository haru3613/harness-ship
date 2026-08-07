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

Use [candidate-handoff-template.md](candidate-handoff-template.md), written to
`.harness-ship/candidates/<short-sha>/handoff.md`. Require:

- approved Test Contract revision and scenario scope;
- full source SHA — or, where the contract's **Release surface owner** is not this repository, its
  **Candidate identifier** plus what that was read from;
- exact non-production artifact/environment revision;
- provenance source and receipt binding the artifact to that SHA or identifier;
- a writable `.harness-ship/candidates/<short-sha>/`, whose name is that SHA's first twelve
  characters, or that identifier; and
- access path, safe fixtures/accounts, known risks, and established test evidence.

Any missing, placeholder, stale, or mismatched required value makes the handoff `Not ready`. Do not
execute against production.

**Where the contract-derived values come from depends on the contract's form.** A two-layer contract
holds them in its Project Test Baseline and Release Delta. A pointer holds its scenario scope in the
documents it names, and in `Carried here` both the operational values — safe fixtures and accounts,
environment, evidence location — and the declarations that pass or fail nothing but decide how this
workflow behaves: who owns the release surface, what identifies a candidate, what this repository
can see of that owner. A pointer has no separable delta; its delta scope is the handoff's scenario
scope read against the documents it names. A value neither form supplies is `Not ready` naming which
one was missing; it is never a reason to infer a safe environment, and an environment inferred
rather than approved is how a test suite meets production.

**Where the contract's Release surface owner is not this repository**, the source SHA is whatever
that owner exposes, recorded as the **Candidate identifier** the contract defines together with what
it was read from, and every record below — handoff, ledger, report, Bug Case — carries that same
value wherever it asks for a source SHA. Where the owner exposes nothing that identifies the build,
the handoff is `Not ready` for that reason, and the missing identifier is a blocker to raise with the
owner. **Never substitute this repository's own `HEAD`**: it is the only 40-character SHA in reach,
it is not the candidate's, and once written here it propagates into the ledger, the report, and every
Bug Case citing them as a source binding that was never true. This is the one loosening — a contract
whose release surface *is* this repository still requires the full source SHA.

## 2 — Select the candidate scope

Execute every required baseline item plus the release delta. Choose the method recorded in the Test
Contract:

- automated command at its approved seam;
- exact manual steps;
- bounded exploratory method; or
- `not-configured`, recorded as NOT RUN / NOT TESTED, carrying the contract row's reason into the
  ledger entry — a row can be `not-configured` because a test exists but nothing has shown it able
  to fail, and a bare NOT RUN reads as no test at all.

Test layers follow risk and seam stability, not author role. Avoid rerunning equivalent coverage at
multiple layers merely to fill a pyramid.

Exploratory evidence may satisfy only a criterion explicitly marked `manual` or `exploratory`.
Required automation must run on this exact candidate. Evidence from a local, preview, or older
artifact cannot prove a later candidate.

## 3 — Execute append-only

Use [execution-ledger-template.md](execution-ledger-template.md), written to
`.harness-ship/candidates/<short-sha>/ledger.md`. Immediately before each action,
revalidate the Test Contract revision, source SHA or candidate identifier, artifact revision,
provenance receipt, evidence destination, and command/manual method. On drift, append NOT RUN / NOT TESTED and stop that item.

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

Produce [test-report-template.md](test-report-template.md) at
`.harness-ship/candidates/<short-sha>/report.md` from the ledger. State each user journey, exact
candidate, method, evidence, gaps, and one verdict: `Ready for release gate` or `Not ready`.

For every non-pass, run `bug-workflow` under one stable BUG-ID, recorded at
`.harness-ship/bugs/<BUG-ID>.md`. Harness Ship classifies the finding, preserves evidence, and
emits repair/retest conditions; it does not dictate the repair workflow.

When a fixed candidate returns, it is a new candidate at a new source SHA — or a new identifier,
whichever kind this candidate's handoff recorded above: it gets its own directory and its own ledger
at `.harness-ship/candidates/<short-sha>/ledger.md`, keyed by that same value and seeded with
a link back to the failed candidate's directory. Require the same BUG-ID, original failed evidence,
diagnosis when available, repair summary, the new one of whichever the handoff recorded, new
artifact/environment revision, new provenance receipt, affected scenarios, and neighbouring regression scope — continuity runs
through the BUG-ID, not through reusing a prior candidate's ledger file. Rerun the original
observation, affected scenarios, and proportionate neighbours. Never overwrite the failed artifact
or call implementation evidence a verification result.

`release-gate` consumes this report. Release promotion remains a separate human-authorized action.
