# Test Report — <feature / release>

Written to `.harness-ship/candidates/<short-sha>/report.md`, where that directory takes the **Candidate identifier** the contract defines when its **Release surface owner** is not this repository.

**<Ready for release gate | Not ready>** — <one-sentence reason>

- **Test Contract:** <project-test-id/revision>
- **Project Test Baseline / Release Delta:** <links>
- **TEST-RUN-ID / ledger:** <run ID> + `.harness-ship/candidates/<short-sha>/ledger.md`
- **Source SHA:** <full 40-character SHA — or, where the contract's Release surface owner is not this repository, its Candidate identifier plus what that was read from; never this repository's HEAD>
- **Artifact/environment:** <exact revision>
- **Artifact provenance:** <source + receipt>
- **Date:** <YYYY-MM-DD>

## User journeys

| Journey | Scenario | Baseline / delta | Method / seam | Result | Evidence | User-visible caveat |
|---|---|---|---|---|---|---|
| <what the user does> | <SC-001> | <baseline> | <command/manual steps> | <PASS/FAIL/FLAKY/BLOCKED/NOT TESTED> | <ledger/evidence> | <none or impact> |

## Coverage and gaps

- **Automated:** <journeys>
- **Manual / exploratory:** <journeys allowed by contract>
- **NOT TESTED:** <scope + reason>
- **Flaky / blocked:** <scope + linked Bug Cases>
- **Test data:** <safe fixtures/environment>

## Fixed-candidate comparison

- **Stable BUG-ID:** <ID>
- **Original failed candidate:** <artifact + evidence>
- **Fixed candidate:** <artifact + evidence>
- **Retest result:** <result>

Never replace the original failure with the fixed result. `release-gate` determines GO, GO WITH
CAVEATS, or NO-GO from this report plus source, artifact, CI, and operational evidence.
