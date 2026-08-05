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

Given the candidate's full source SHA, read these before asking the user for anything:

- `.harness-ship/test-contract.md` — the user-approved contract containing Project Test Baseline
  plus Release Delta. Gate against this file only. A `.harness-ship/test-contract.draft.md` beside
  it is an unapproved revision in progress and is never evidence, but its presence is also never a
  reason to reject a candidate the approved file covers. When this file is a pointer, follow it and
  gate against the document it names; its `Not carried by that document` field states what this
  project's criteria genuinely do not cover, and an item listed there is an unevaluated gap, never a
  pass;
- `.harness-ship/candidates/<short-sha>/report.md` and `ledger.md` — the `testing-workflow` report
  and its append-only ledger for this candidate;
- `.harness-ship/candidates/<short-sha>/handoff.md` — the exact artifact/environment revision and
  the provenance receipt binding it to that SHA; and
- `.harness-ship/bugs/` — any Bug Case still open against a scenario this candidate must pass.

Then establish from outside the repository: the intended release target, exact-head CI/build/test
evidence, applicable operational-risk evidence and known gaps, and rollback or recovery evidence
when the release delta makes it required.

A record that is absent, `DRAFT`, or still carries a template placeholder is evidence of `NO-GO`,
not permission to infer PASS. An absent `.harness-ship/` is `NO-GO` with the reason that this
project has no contract to gate against — say that, rather than offering to evaluate the candidate
from whatever the user can paste into the session.

## Evaluate in order

1. **Contract** — the baseline and delta are approved, current, and cover the candidate scope.
2. **Source** — required checks ran successfully on the full candidate SHA; skipped or stale jobs do
   not count.
3. **Artifact** — provenance binds the tested artifact to that SHA and intended environment.
4. **Behaviour** — every required P0 journey is PASS on this candidate. Required automation cannot
   be replaced by exploratory evidence.
5. **Operational risk** — only checks made applicable by the baseline or delta are required:
   migration, compatibility, security, performance, accessibility, recovery, or rollback.
6. **Gaps** — every non-blocking caveat names user impact, evidence, owner, and follow-up.

Do not add a universal coverage percentage, framework checklist, or test-count target.

## Verdict

Apply the first matching rule:

- **NO-GO** — unapproved or stale contract; source/artifact mismatch; any required or P0 result is
  FAIL, FLAKY, BLOCKED, NOT TESTED, skipped, stale, or missing; or an applicable operational gate
  lacks evidence.
- **GO WITH CAVEATS** — all required and P0 gates PASS, while only explicitly non-blocking gaps
  remain. This requires the user's recorded acceptance and linked follow-up; without it use NO-GO.
- **GO** — all required evidence and P0 gates PASS on the exact candidate and no release caveat
  remains.

Report the verdict first, then candidate SHA/artifact, contract revision, gate-by-gate evidence,
gaps, rollback/recovery status, and the human decision still required to perform a release.
