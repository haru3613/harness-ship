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

- a user-approved Test Contract revision containing Project Test Baseline plus Release Delta;
- full candidate source SHA and intended release target;
- exact artifact/environment revision and provenance receipt binding it to that SHA;
- exact-head CI/build/test evidence;
- the `testing-workflow` report and append-only ledger for this candidate;
- applicable operational-risk evidence and known gaps; and
- rollback or recovery evidence when the release delta makes it required.

Missing or placeholder required input is evidence of `NO-GO`, not permission to infer PASS.

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
