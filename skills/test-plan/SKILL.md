---
name: test-plan
description: >-
  Create or revise the user-approved Test Contract that defines what must be proven before release.
  Use for a new project, an existing project's test audit, a feature's release delta, or when someone
  asks what should be tested. Triggers: "/test-plan", "plan the tests", "define the release
  criteria", "audit this project's tests".
---

# test-plan

Define **what must be proven**, not how development must proceed. The Test Contract may be written
before implementation or added to an existing project later, but its release criteria must be fixed
before `release-gate` executes.

Read the repository instructions and its `## harness-ship` Config v3 block first. Run `setup` only
when the block is absent or unsupported. Keep Config v3 policy-only; store test capabilities and
release criteria in the Test Contract instead of expanding project configuration.

## Where the records live

Every Harness Ship record is a file under `.harness-ship/` at the repository root, committed with
the code it describes. `test-plan` creates this tree; the other workflows read and extend it.

| Record | Path | Written by |
|---|---|---|
| Approved Test Contract | `.harness-ship/test-contract.md` | `test-plan` |
| Test Contract revision in progress | `.harness-ship/test-contract.draft.md` | `test-plan` |
| Bug Case, then its Diagnosis Receipts appended | `.harness-ship/bugs/<BUG-ID>.md` | `bug-workflow`, `diagnose` |
| Candidate handoff, execution ledger, test report | `.harness-ship/candidates/<short-sha>/` | `testing-workflow` |

`<short-sha>` is the first 12 characters of the candidate's full source SHA; the full SHA stays
inside each record and is what binds evidence, so on any mismatch the record wins and the directory
name is wrong. Twelve rather than git's displayed seven: a colliding directory would let two
candidates share one ledger, which is the older-artifact-proves-a-later-candidate failure this
workflow exists to prevent.

One directory per candidate, not per attempt — within one candidate's ledger, append attempts rather
than starting a second ledger. A fixed candidate is a new SHA and gets its own directory; continuity
across the repair cycle runs through the stable BUG-ID, not through reusing the failed candidate's
ledger file.

These paths are fixed, not configured. A project that keeps records in a tracker still writes the
files: the tracker holds the discussion, the repository holds the evidence a later session can find
without being told where to look. Where a record is mirrored into a tracker, its file carries the
durable link.

**One release surface per repository.** The layout carries no product or surface qualifier, so a
monorepo whose services release on independent cadences does not fit: two of them cutting candidates
from the same commit would write into one `.harness-ship/candidates/<short-sha>/` and overwrite each
other, and one shared contract would force a revision bump on surface A to be reconciled by surface
B's untested candidates. Say so and stop rather than inventing a per-surface path; a repository that
needs this needs a contract change, not a directory convention.

## Two-layer Test Contract

Give the contract a stable ID and revision. It has two independently reviewable layers. Draft it
from `test-contract-template.md`.

`.harness-ship/test-contract.md` holds only the currently approved revision. Draft every revision —
including the first — to `.harness-ship/test-contract.draft.md`, and replace the approved file from
it at approval, deleting the draft. Never write a `DRAFT` header into the approved path.

The split exists because planning the next revision must not disturb a candidate already being
tested or gated against the current one. Overwriting the approved file mid-flight would make
`testing-workflow` record drift and `release-gate` return `NO-GO` for a candidate whose contract
never actually changed.

Revisions are git history. Increment the `rev` when drafting so records that cite a revision stay
interpretable, and do not keep superseded copies alongside the approved file.

### Project Test Baseline

Record the reusable release expectations:

- product type, supported surfaces, and release target;
- P0/P1 user journeys with stable scenario IDs and externally observable expected and forbidden
  behaviour;
- the cheapest stable seam that can prove each journey or risk;
- method: `automated`, `manual`, `exploratory`, or `not-configured`;
- established command or exact manual steps, required evidence, environment, fixtures, permissions,
  and safe test-data rules;
- source-to-artifact provenance method and durable evidence location; and
- required, observe-only, and deferred checks, with reasons.

P0 covers core value, auth, money, destructive state changes, or a flow that must not regress.
Unknown capability is `not-configured`, never PASS.

### Release Delta

For one candidate, record:

- source range, release scope, and affected baseline scenarios;
- new or changed behaviour and risks;
- added scenarios or evidence requirements; and
- applicable migration, compatibility, security, performance, accessibility, recovery, or rollback
  checks. Mark an item not applicable only with a concrete reason.

Unchanged baseline content is referenced, not copied or re-approved.

## Greenfield project

Start with the product surface and first real risks. Do not install a framework, invent commands, or
create E2E infrastructure for an empty repository. A draft may honestly leave capabilities
`not-configured` until a testable slice exists. Add automation only when a real behaviour and seam
justify it.

## Existing project

Inspect before proposing change:

1. inventory the complete test tree, runners, CI jobs, deployment path, and artifact provenance;
2. identify current green, red, flaky, skipped, and missing capabilities;
3. map existing tests to user journeys and risks;
4. mine the project's own defect history — every Bug Case and Diagnosis Receipt already under
   `.harness-ship/bugs/`, plus closed defect issues, revert and fix commits, and incident records,
   and the predecessor's when the project is a rewrite, clustering by failure mechanism rather than
   by file; and
5. preserve repository-native tools while classifying gates as required, observe-only, or deferred.

What has already broken is the most reliable evidence of what must be proven. A recurring mechanism
that no journey describes is a **baseline gap**: add the scenario before adding coverage. A mechanism
that recurred despite an existing defence has disproved that defence — the defence is not evidence,
and the scenario keeps whatever classification its own priority earns. When the history is sampled
rather than read in full, say so; a sampled count is a floor, never a reason to lower a
classification. A defect caught before release is evidence about seam adequacy, not a production
incident; record which one it is.

Do not replace a framework or duplicate coverage merely to make the project resemble a template.

## Approval and revision

Present the complete baseline plus release delta. Only the user may approve the Test Contract.
Until then it stays at `.harness-ship/test-contract.draft.md` with a `DRAFT` header, and
`release-gate` gates against the approved file — or returns `NO-GO` when no approved file exists
yet. Writing the draft is not approval.

On approval, record the approving user and date, replace `.harness-ship/test-contract.md` with the
draft's content, and delete the draft. A candidate already tested against the previous revision now
drifts against the new one, which is correct: its evidence proves the contract it was tested
against, not this one.

After approval, any semantic change to expected behaviour, priority, required evidence, test method,
or blocking status creates a new revision. Implementation details and equivalent seam corrections
do not. Preserve retired scenarios and IDs so old evidence remains interpretable.
