# Test Execution Ledger — <feature / release>

Written to `.harness-ship/candidates/<short-sha>/ledger.md`, where that directory takes the **Candidate identifier** the contract defines when its **Release surface owner** is not this repository.
Append attempts; never overwrite them.

- **TEST-RUN-ID:** <stable run ID>
- **Test Contract:** <project-test-id/revision>
- **Candidate handoff:** `.harness-ship/candidates/<short-sha>/handoff.md`
- **Full source SHA:** <40-character SHA — or, where the contract's Release surface owner is not this repository, its Candidate identifier plus what that was read from; never this repository's HEAD>
- **Exact artifact/environment revision:** <immutable artifact + non-production environment>
- **Artifact-provenance source / receipt:** <source + durable receipt>
- **Evidence location:** `.harness-ship/candidates/<short-sha>/`

| Attempt | Previous | Started / completed | Scenario | Baseline / delta | Method / seam | Raw outcome | Normalized result | Evidence | Notes |
|---|---|---|---|---|---|---|---|---|---|
| <1> | <none> | <timestamps> | <SC-001> | <baseline/delta> | <command or manual steps> | <PASS/FAIL/BLOCKED/NOT RUN> | <PASS/FAIL/FLAKY/BLOCKED/NOT TESTED> | <durable link> | <risk result; for a `not-configured` row, the contract's reason — a test may exist that nothing has shown able to fail> |

Normalize each scenario in this order:

1. latest NOT RUN → NOT TESTED;
2. latest BLOCKED → BLOCKED;
3. any FAIL plus PASS in the same TEST-RUN-ID → FLAKY;
4. latest PASS → PASS;
5. latest FAIL → FAIL.

If source, artifact, environment, or provenance changes, start a new TEST-RUN-ID and retain the old
ledger.

## Fixed-candidate verification

Record the stable BUG-ID, repair attempt, original failed attempt, new candidate, affected scenario,
raw outcome, normalized result, and evidence. Preserve every failed and fixed candidate observation.

## Resume

- **Last durable attempt:** <attempt>
- **Resume from:** <next scenario>
- **Blocker:** <none or exact blocker>
- **Next safe action:** <append; never overwrite>
