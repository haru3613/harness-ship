# QA Execution Ledger — <feature / ticket>

> This is an append-only execution record. Never overwrite an earlier attempt, failed-artifact
> observation, or evidence link. To resume after interruption, append a new attempt that names the
> previous attempt and revalidates the exact artifact before execution.

- **QA-RUN-ID:** <stable run ID>
- **Acceptance contract revision:** <spec-id/acceptance-vN>
- **Handoff:** <durable QA handoff link>
- **Full source SHA:** <40-character SHA>
- **Exact artifact/environment revision:** <immutable artifact/deployment revision + QA environment>
- **Artifact-provenance source:** <provider/API/build manifest>
- **Artifact provenance receipt:** <receipt ID or durable link>
- **Evidence location:** <configured durable path>

## Attempts

Append one row per scenario attempt. A retry gets a new attempt number; it never replaces the
original result.

| Attempt | Previous attempt | Started at | Completed at | SC-ID | AC-ID | Ticket | Full source SHA | Exact artifact/environment revision | Artifact-provenance source / receipt | QA layer / risk probe | Method/command or manual steps | Result | Evidence | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <1> | <none> | <timestamp> | <timestamp / in-progress> | <SC-002> | <AC-2> | <ID> | <SHA> | <artifact/env> | <source + receipt> | <integration / E2E / exploratory / non-functional> | <configured QA command or exact manual steps> | <PASS / FAIL / FLAKY / BLOCKED / NOT TESTED> | <durable screenshot/video/trace/log/assertion link> | <risk result> |

Every attempt inherits and records the ledger's full source SHA, exact artifact/environment
revision, artifact-provenance source, and provenance receipt. If any value changes, start a new
QA-RUN-ID and retain the old ledger.

## Resume state

- **Last durable attempt:** <attempt>
- **Resume from:** <next scenario / interrupted attempt>
- **Blocker:** <none / missing capability / environment / artifact mismatch>
- **Next safe action:** <append attempt; never overwrite>
