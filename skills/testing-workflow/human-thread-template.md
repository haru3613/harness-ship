<!-- harness-ship:testing:<candidate-key> -->
# Harness Ship candidate — <feature / release>

**<Ready for testing | Ready for release gate | Not ready>** — <one plain-language reason>

> Human-readable projection for the review thread. The candidate handoff, append-only ledger, and
> test report under `.harness-ship/candidates/<short-sha>/` remain the only source of truth.

## QA handoff

**Handoff: <Ready | Not ready>** — <one plain-language reason>

- **Candidate:** <full source SHA or external candidate identifier>
- **Test Contract:** <project-test-id/revision>
- **Artifact/environment:** <exact immutable revision + non-production environment>
- **Provenance:** <source + durable receipt>
- **Canonical evidence:** <links to handoff, ledger, and report as available>

### What changed

<What a user or release owner will experience. Do not lead with filenames or implementation detail.>

### Acceptance criteria to verify

| User journey | Scenario / originating work | Expected | Must not happen |
|---|---|---|---|
| <what the user does> | <SC-001 + ticket> | <observable result> | <specific forbidden outcome> |

### How to reach it

- **Access:** <URL, app build, API endpoint, or local command>
- **Safe fixtures:** <roles, permissions, and seed state safe to disclose; never production>

### Known risks

- <release-delta risk or edge case worth probing>

### Already covered

- <established unit, contract, CI, or earlier evidence; informational, not candidate PASS>

### Not tested yet

- <candidate journeys or operational checks awaiting execution>

## Test result

**<Pending | Ready for release gate | Not ready>** — <one plain-language reason>

### User journeys

| User journey | Method | Result | Evidence | What the user would experience |
|---|---|---|---|---|
| <what the user does> | <automated/manual/exploratory> | <PASS/FAIL/FLAKY/BLOCKED/NOT TESTED> | <durable link> | <none, caveat, or failure impact> |

### Coverage and gaps

- **Automated PASS:** <journeys proven on this exact candidate>
- **Manual / exploratory:** <contract-approved evidence and result>
- **NOT TESTED:** <scope + reason>
- **FAIL / FLAKY / BLOCKED:** <scope + Bug Case or follow-up>
- **Test data:** <safe fixture/environment summary>

### Next action

<Run or rerun testing, repair under a Bug Case, proceed to release-gate, or make the named human decision.>

Do not publish secrets, credentials, raw tokens, fixture PII, or full logs in this projection. Link
to access-controlled durable evidence when the detail is needed.
