# Test Candidate Handoff — <feature / release>

Written to `.harness-ship/candidates/<short-sha>/handoff.md`, where that directory takes the **Candidate identifier** the contract defines when its **Release surface owner** is not this repository.

- **Status:** <Ready | Not ready>
- **Test Contract:** <project-test-id/revision>
- **Project Test Baseline:** <revision/link — or, for a pointer contract, the documents it names>
- **Release Delta:** <revision/link — or, for a pointer contract, the scenario scope below read against the documents it names; a pointer has no separable delta>
- **Scenario scope:** <scenario IDs + originating work>
- **Full source SHA:** <40-character SHA — or, where the contract's Release surface owner is not this repository, its Candidate identifier plus what that was read from; never this repository's HEAD>
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
- **New full source SHA:** <40-character SHA — or, where the contract's Release surface owner is not this repository, its Candidate identifier plus what that was read from; never this repository's HEAD>
- **New artifact/environment revision:** <immutable fixed artifact + environment>
- **New provenance receipt:** <binds new artifact to the new SHA or candidate identifier>
- **Affected scenarios:** <original observation + journeys>
- **Neighbouring regression scope:** <risk-based scope>

Mark the handoff Not ready when a required value is missing, placeholder, stale, or mismatched; the
artifact cannot be bound to the source SHA or candidate identifier; the owner of an external release
surface exposes nothing that identifies the build; the evidence destination is unavailable; or the
environment is production. A fixed candidate must differ from the failed artifact.
