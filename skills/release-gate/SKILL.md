---
name: release-gate
description: >-
  Evaluate an exact release candidate against its approved Project Test Baseline and Release Delta,
  then return GO, GO WITH CAVEATS, or NO-GO without promoting it. Use when someone asks whether a
  candidate is ready to release. Triggers: "/release-gate", "is this ready to release", "run the
  release gate", "go or no-go".
---

# release-gate

Return a release verdict from existing evidence. This skill is read-only: it never merges, deploys,
promotes, tags, publishes, seeds data, or changes release criteria.

## Required inputs

Given the candidate's full source SHA, read these before asking the user for anything. Read the
contract before asking for the SHA: a repository that does not own its release surface has no
candidate SHA to give, and asking produces this repository's `HEAD`, which is the substitution the
stop below exists to refuse.

- `.harness-ship/test-contract.md` — the user-approved contract containing Project Test Baseline
  plus Release Delta. Gate against this file only. A `.harness-ship/test-contract.draft.md` beside
  it is an unapproved revision in progress and is never evidence, but its presence is also never a
  reason to reject a candidate the approved file covers. When this file is a pointer, follow it and
  gate against every document it names plus its `Carried here` field — that field is contract text
  approved with the pointer, carrying criteria the named documents never held, except its
  declarations about where the release surface is, what identifies a candidate, and what this
  repository can see of that owner: those pass or fail nothing, and the stop below acts on them
  instead. Its `Not carried by that document` field states what nobody has decided, and its entries are read by their label, not
  by whether they name a file: `undecided` and `unreadable` are unevaluated gaps that block exactly
  as a missing result does and are never a pass, while `excluded` is a whole document outside the
  gated scope — report it as scope this verdict did not evaluate rather than letting the pointer
  imply it was covered;
- `.harness-ship/candidates/<short-sha>/report.md` and `ledger.md` — the `testing-workflow` report
  and its append-only ledger for this candidate. That directory is named for the contract's
  **Candidate identifier** where its **Release surface owner** is not this repository, which is how
  the stop below finds the records it hands over;
- `.harness-ship/candidates/<short-sha>/handoff.md` — the exact artifact/environment revision and
  the provenance receipt binding it to that SHA or identifier; and
- `.harness-ship/bugs/` — any Bug Case still open against a scenario this candidate must pass.

Then establish from outside the repository: the intended release target, exact-head CI/build/test
evidence, applicable operational-risk evidence and known gaps, and rollback or recovery evidence
when the release delta makes it required.

A record that is absent, `DRAFT`, or still carries a template placeholder is evidence of `NO-GO`,
not permission to infer PASS. An absent `.harness-ship/` is `NO-GO` with the reason that this
project has no contract to gate against — say that, rather than offering to evaluate the candidate
from whatever the user can paste into the session.

**Stop when the contract declares the release surface is elsewhere.** Read it from the contract's
**Release surface owner** field, or from a pointer's `Carried here`. A repository that ships
nothing — a QA-owned suite, a contract-test repository, a vendor-acceptance suite — holds criteria for a
candidate another team builds and releases. Return `NO-GO` whose reason is that the verdict belongs
to the repository that owns the candidate, and hand over what this repository does have: the
`testing-workflow` report and ledger, any open Bug Case, and the contract's **Visible from here** —
which tells the owning team what this repository could not see, and is the only place that fact
does any work. Report that short form rather than the full gate-by-gate layout below — there are no
gate results, and producing them is the failure this stop prevents. This is the skill working, not
a defect here and not a gap to fill.

Refuse rather than adapt, because adapting is easy and silent. The nearest SHA to hand is this
repository's own `HEAD`, and substituting it satisfies every gate mechanically — the contract's
seams are test files that resolve here, this repository's CI is green, and provenance binding this
repository to itself is trivially consistent. The result is a confident `GO` that proves the test
suite compiles and says nothing about the candidate. Do not reach across to the owning side's CI or
artifact provenance either; not having it is the condition, not the obstacle.

## Evaluate in order

1. **Contract** — the baseline and delta are approved, current, and cover the candidate scope, and
   the contract still describes the repository it names as the release surface. A contract that
   names another repository as that surface is not drift to report here; it is the stop above,
   already applied before this gate runs. Every gate below reads this document; nothing else
   checks whether it is still true. At the candidate SHA, resolve what each `required` and P0 row
   with an `automated` method names as its seam — the test file, test name, command, or CI job.
   A citation that no longer resolves makes that row **unevaluated**, which blocks exactly as a
   missing result does. It is never a pass, and a report claiming PASS for it is evidence the report
   was produced against a different tree.

   Resolve, do not execute: `release-gate` never runs the suite. Rows whose method is `manual`,
   `exploratory`, or `not-configured` name steps rather than code and are out of scope here — they
   are already governed by their own evidence rules.

   Where the contract is a pointer and a document it names is enforced by the project's own check,
   record that check and its result instead of repeating it, once per document — a pointer naming
   several documents that share one recorded check leaves the rest unaudited. A project that already
   fails CI when a cited test disappears has solved this better than an inspection at gate time.

   A contract nobody has audited grows more authoritative and less true at the same rate. This is
   the one failure mode that produces a confident `GO` with nothing behind it.
2. **Source** — required checks ran successfully on the full candidate SHA; skipped or stale jobs do
   not count.
3. **Artifact** — provenance binds the tested artifact to that SHA and intended environment.
4. **Behaviour** — every required P0 journey is PASS on this candidate. Required automation cannot
   be replaced by exploratory evidence.
5. **Operational risk** — only checks made applicable by the baseline or delta are required:
   migration, compatibility, security, performance, accessibility, recovery, or rollback.
6. **Gaps** — every non-blocking caveat names user impact, evidence, owner, and follow-up. Report
   the contract's **Seam runnability** rows here too, reading `What the used seam cannot see` as the
   user impact and the row itself as the evidence; each names a scenario proven at a seam blind to
   something its forbidden clause names, because the seam that would catch it cannot be run here.
   These are already accepted by the contract's approval and do not move the verdict — the evidence
   they produced is real — but reporting them is what keeps a standing environmental limitation from
   reading as a settled design choice, one candidate at a time. Where a pointer's `Carried here` does
   not say whether it has any, report that as a question this verdict did not evaluate rather than
   reading silence as none.

Do not add a universal coverage percentage, framework checklist, or test-count target.

## Verdict

Apply the first matching rule:

- **NO-GO** — unapproved or stale contract; a contract declaring the release surface is elsewhere,
  which no other rule below matches because every gate can be made to pass against this repository's
  own `HEAD`; source/artifact mismatch; any required or P0 result is
  FAIL, FLAKY, BLOCKED, NOT TESTED, skipped, stale, or missing; or an applicable operational gate
  lacks evidence.
- **GO WITH CAVEATS** — all required and P0 gates PASS, while only explicitly non-blocking gaps
  remain. This requires the user's recorded acceptance and linked follow-up; without it use NO-GO.
  A **Seam runnability** row is not a gap of this kind: approving the contract accepted it, it
  needs no further acceptance per candidate, and it does not move the verdict. Report it and read
  the next rule.
- **GO** — all required evidence and P0 gates PASS on the exact candidate and no release caveat
  remains. Standing **Seam runnability** rows are reported alongside a `GO`, not against it;
  otherwise a project would be permanently ungateable for admitting where its evidence is thin,
  which is the opposite of the incentive this record exists to create.

Report the verdict first, then candidate SHA/artifact, contract revision, gate-by-gate evidence,
gaps, rollback/recovery status, and the human decision still required to perform a release.
