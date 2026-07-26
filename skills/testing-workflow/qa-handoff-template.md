# QA Handoff — <feature / ticket>

> Publish this handoff on the configured ticket or PR. QA starts only when every required field is
> concrete and the handoff status is `Ready`.

- **Handoff status:** <Ready | Not ready>
- **Acceptance contract revision:** <spec-id/acceptance-vN>
- **Scenario scope:** <SC-ID → AC-ID, ticket>
- **Full 40-character source SHA:** <SHA>
- **Deployed artifact/environment revision:** <immutable artifact or deployment revision + QA environment>
- **Artifact-provenance source:** <provider/API/build manifest that binds the artifact to the source SHA>
- **Artifact provenance receipt:** <receipt ID or durable link>
- **QA evidence location:** <configured writable durable location>
- **Access path:** <URL/app build/API endpoint>
- **Fixtures/accounts:** <fixture IDs, account roles, permissions, seed state; no secrets>
- **Known risks:** <approved risk probes and important edge cases>

## RD coverage summary — informational only

- **RD source SHA:** <same full source SHA>
- **Unit coverage summary:** <behaviour covered | not-configured>
- **API-contract coverage summary:** <behaviour covered | not-configured>
- **RD evidence links:** <CI/test receipts>
- **Not covered by RD:** <integration boundaries and journeys QA should exercise>

The RD coverage summary helps QA avoid duplicate testing. QA does not audit the TDD cycle and does
not execute RD unit or API-contract tests.

## Validation

Mark the handoff `Not ready` when a required value is missing, a placeholder, or mismatched; when
the provenance receipt does not bind the full source SHA to the deployed artifact; or when the
configured QA environment cannot be reached safely.
