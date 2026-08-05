# Test Candidate Handoff — <feature / release>

Written to `.harness-ship/candidates/<short-sha>/handoff.md`.

- **Status:** <Ready | Not ready>
- **Test Contract:** <project-test-id/revision>
- **Project Test Baseline:** <revision/link>
- **Release Delta:** <revision/link>
- **Scenario scope:** <scenario IDs + originating work>
- **Full source SHA:** <40-character SHA>
- **Exact artifact/environment revision:** <immutable artifact + non-production environment>
- **Artifact-provenance source / receipt:** <provider/build manifest + durable receipt>
- **Evidence location:** `.harness-ship/candidates/<short-sha>/`
- **Access path:** <URL/app build/API endpoint/local command>
- **Fixtures/accounts:** <safe fixtures, roles, permissions; no secrets>
- **Known risks:** <release-delta risks>
- **Established test evidence:** <commands/results/CI links; not a substitute for candidate execution>

## Fixed-candidate addendum

- **Stable BUG-ID:** <existing BUG-ID>
- **Repair attempt:** <append-only number>
- **Original failed artifact/evidence:** <source + artifact + ledger/evidence>
- **Diagnosis Receipt:** <link | not produced>
- **Repair summary:** <what changed; no prescribed implementation workflow>
- **New full source SHA:** <40-character SHA>
- **New artifact/environment revision:** <immutable fixed artifact + environment>
- **New provenance receipt:** <binds new artifact to new SHA>
- **Affected scenarios:** <original observation + journeys>
- **Neighbouring regression scope:** <risk-based scope>

Mark the handoff Not ready when a required value is missing, placeholder, stale, or mismatched; the
artifact cannot be bound to the source SHA; the evidence destination is unavailable; or the
environment is production. A fixed candidate must differ from the failed artifact.
