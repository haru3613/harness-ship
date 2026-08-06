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

## An existing document may already be the contract

Before drafting anything, check whether this project already states what must be proven, under
another name — a journey coverage map, a release gate checklist, an accepted acceptance-criteria
document. A mature project usually does.

It qualifies when it carries all four:

- stable per-item IDs that survive the item being retired;
- both expected behaviour **and** the negative — what must never happen, and both readable from
  this repository: resolve every path the document cites for a scenario's authoritative detail, and
  require it to be tracked at the revision being approved;
- a priority or blocking classification the project actually honours; and
- a record that the user accepted it, not just that someone wrote it.

Resolve those citations rather than reading past them. A document that delegates each scenario's
detail elsewhere can assert it covers the negative half and still leave that half unreadable from a
fresh clone — the cited path is two characters short of correct, or correct and pointing into a
directory nobody committed. Neither is visible to a reviewer; only resolving is. `release-gate`
already re-resolves what a row cites as its seam because a citation that no longer exists makes the
row unevaluated instead of passing; the contract's own citations are the same problem one level up,
and nothing else checks them.

A delegation that does not resolve fails this condition for the scenarios it covers, not for the
whole document: record those as `unreadable` under **Not carried by that document** rather than
inheriting the coverage they claim. Disqualifying an otherwise good document over one broken path
would force the restatement this section exists to avoid. When the delegation covers every
scenario, though, nothing readable is left to point at — that is the threshold below, and the
document does not qualify. Citations of discussion — tracker items, published standards — are not
criteria and are not what this checks.

When it qualifies, **do not restate it**. `.harness-ship/test-contract.md` becomes a pointer:

```markdown
# Test Contract — pointer

- **Contract:** `<path>` — the document this project already treats as its release criteria
- **Qualifies because:** `<where its stable IDs, expected, forbidden, priority, and acceptance
  record live>`
- **Kept honest by:** `<the check that fails when it drifts | nothing>`
- **Approved by / date:** `<user + date>`
- **Carried here:** `<criteria this project supplies that the document does not>`
- **Not carried by that document:**
  - `<undecided: what nobody has ruled on yet>`
  - `<unreadable: a scenario whose authoritative detail this document delegates to something that
    does not resolve>`
  - `<excluded: a sibling document nobody has accepted, named with the condition it failed>`
```

Repeat the first three fields for each qualifying document. Conditions three and four are judged per
document, so one shared line cannot say which document carries an acceptance record and which
carries a check — and a pointer that cannot say that is back to implying coverage it has not
established.

The last two fields are what stop a pointer from being a way to skip the work, and they are not the
same field. **Carried here** holds what this project can answer now and the document simply never
covered — safe test-data rules, environment, evidence location. Its content comes from the
interview in `## Ask before drafting`, never from inspection alone: it is the one part of a pointer
that `release-gate` reads as criteria to pass, so criteria the model wrote and nobody chose would
pass against themselves. A pointer may extend the document it names, never contradict it, and the
extension is approved with the pointer. Without this the mature-project path cannot satisfy the
Project Test Baseline's operational half, and mature projects are exactly the ones whose document
was written for another purpose and omits it.

**Not carried by that document** holds what this project's criteria do not establish — never merely
what is absent from that file. `release-gate` treats an `undecided` or `unreadable` entry there as
an unevaluated gap that blocks, so an answered question filed there blocks on its own answer. A
document written for one release usually has no reusable baseline separable from its delta, so
re-reviewing one candidate means re-reviewing everything; that belongs there. If the gap is large
enough that release criteria cannot be read out of the document at all, it does not qualify — draft
a contract instead.

Qualification is per document, not per project. Sibling documents covering related capabilities
mature at different rates: the shipped one has a closed acceptance record, the one still in flight
has nobody's acceptance at all. Both available moves are then wrong — pointing at both launders
unapproved criteria into an approved contract, and restating the good one instead discards a real
acceptance record to create the second source of truth this section exists to avoid. Point at each
document that qualifies, and name any that do not as `excluded` under **Not carried by that
document**, with the condition each failed.

Only a whole document is excluded this way, and only exclusion leaves the gated scope:
`release-gate` gates the qualifying documents and reports an excluded one as scope it did not
evaluate, while an `unreadable` scenario belongs to a document that did qualify, stays in scope, and
blocks like any other unevaluated row. Blocking on an excluded document instead would hold every
release hostage to a capability nobody has finished accepting, which is the pressure that turns
acceptance into a rubber stamp. What the exclusion buys is that its scenarios are never counted as
proven — unevaluated, not passed and not deferred, since nobody has decided they may ship unproven.
A user may still decide to defer them, but a deferral is a decision with a reason and is recorded as
one; silence is not deferral.

A project whose existing document is enforced by its own check is ahead of this template, not behind
it. Replacing it with a restatement loses that enforcement and creates a second source of truth that
begins drifting immediately.

## Two-layer Test Contract

Only when no qualifying document exists. Give the contract a stable ID and revision. It has two
independently reviewable layers. Draft it from `test-contract-template.md`.

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

Read [scenario-craft.md](scenario-craft.md) before writing the scenario table. It covers how to cut
journeys so their IDs outlive the UI, and how to write the forbidden half — the column that decides
whether the contract can catch anything, and the one most often left as a restatement of "fails".

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

Here there is nothing to inspect, so every answer comes from the interview below. Never synthesize a
baseline from the sentence that started the session.

## Existing project

Inspect before proposing change:

1. inventory the complete test tree, runners, CI jobs, deployment path, and artifact provenance;
2. identify current green, red, flaky, skipped, and missing capabilities;
3. map existing tests to user journeys and risks;
4. mine the project's own defect history — any Bug Case and Diagnosis Receipt already under
   `.harness-ship/bugs/`, of which a first run has none because this skill creates that tree, plus
   closed defect issues, revert and fix commits, and incident records, and the predecessor's when
   the project is a rewrite, clustering by failure mechanism rather than by file; and
5. preserve repository-native tools while classifying gates as required, observe-only, or deferred.

What has already broken is the most reliable evidence of what must be proven. A recurring mechanism
that no journey describes is a **baseline gap**: add the scenario before adding coverage. A mechanism
that recurred despite an existing defence has disproved that defence — the defence is not evidence,
and the scenario keeps whatever classification its own priority earns. When the history is sampled
rather than read in full, say so; a sampled count is a floor, never a reason to lower a
classification. A defect caught before release is evidence about seam adequacy, not a production
incident; record which one it is.

Do not replace a framework or duplicate coverage merely to make the project resemble a template.

## Ask before drafting

Inspection establishes what the project *has*. It cannot establish what *matters*, and the contract
is a statement about what matters. Complete at least one round of real answers before drafting any
scenario table, and before filling a pointer's **Carried here** — a pointer inherits what it points
at, but whatever it supplies itself is subject to this section exactly as a drafted contract is.

Use the harness's structured question tool where one exists. One topic per question, never several
folded into one choice — but where the tool accepts several questions in a call, one call may carry
several, and a topic whose framing depends on an earlier answer waits for its own round. Add rounds
rather than widening a question. Where inspection suggests an answer, lead with it as a hypothesis
to confirm or correct — never as a finished fact. Skip anything the repository already answers with
explicit evidence; a purpose transcribed from a README is a hypothesis, not evidence. A topic the
user has already answered unprompted is answered — do not re-ask it to satisfy the round.

Ask about what inspection cannot reach:

- **Priority.** Which journeys are P0. Code shows what exists, not what the business cannot afford
  to break. Never derive P0 from test coverage — the best-covered path is often the easiest one.
- **Money and destruction.** What counts as money, irreversible state, or data loss *in this
  product*. A refund, a scheduled send, a bulk delete, and a published post are not recognizable
  from a call graph.
- **Forbidden behaviour.** What must never happen, per journey. The scenario table's `Forbidden`
  column is almost never inferable; an expected-behaviour-only contract passes every test while the
  thing the user actually fears still ships.
- **Existing red, flaky, and skipped tests.** For each, whether it is a known-accepted state or an
  unreported gap. Both look identical in the tree, and guessing wrong either manufactures a blocker
  or launders a real failure into the baseline.
- **Acceptable deferral.** Which gaps may be deferred and why. A deferral the user did not make is
  the model deciding what may ship broken.
- **Release target.** What this baseline is being written against.

Then propose. Inferred answers may be presented for confirmation only after that first round, and
each still names what it was inferred from.

Do not generate the complete baseline and delta from inspection alone and ask for one blanket
approval. An approved contract nobody chose is the failure mode this whole workflow exists to
prevent: `release-gate` will enforce it exactly, and every later Bug Case, Diagnosis Receipt, and
verdict traces back to a scenario the user never actually agreed to.

## Approval and revision

Present the complete draft — baseline plus release delta, or the pointer. Only the user may approve
the Test Contract. Until then it stays at `.harness-ship/test-contract.draft.md` with a `DRAFT`
header, and `release-gate` gates against the approved file — or returns `NO-GO` when no approved
file exists yet. Writing the draft is not approval.

This holds for both forms. A pointer is short and mostly citation, which makes writing it straight
to the approved path tempting, but what a pointer commits this project to is exactly what the user
has to approve, and `release-gate` gates the approved file either way.

On approval, record the approving user and date, replace `.harness-ship/test-contract.md` with the
draft's content, and delete the draft. A candidate already tested against the previous revision now
drifts against the new one, which is correct: its evidence proves the contract it was tested
against, not this one.

After approval, any semantic change to expected behaviour, priority, required evidence, test method,
or blocking status creates a new revision. Implementation details and equivalent seam corrections
do not. Preserve retired scenarios and IDs so old evidence remains interpretable.
