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

## Bug Case fixed-artifact verification

- **Stable BUG-ID:** <existing product-defect BUG-ID>
- **Fix attempt:** <append-only repair attempt>
- **Original failed-artifact evidence:** <prior ledger attempt + artifact/environment>
- **Fixed artifact:** <new source SHA + exact artifact/environment + new deployment receipt>

Append one **QA verification attempt** for every fixed-artifact check. A retest attempt is numbered
within its fix attempt and never overwrites the original failure or another fix/retest attempt.
Each row indexes the canonical Stage 3 attempt and its normalized scenario classification after
Stage 4; it does not assign the final Bug Case disposition.

| Fix attempt | Retest attempt | Previous verification attempt | Canonical Stage 3 attempt | SC-ID | Original observation / neighbouring regression | Fixed artifact | Raw outcome | Normalized scenario classification | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| <1> | <1> | <original failed attempt> | <QA-RUN-ID/attempt> | <SC-ID> | <original observation / affected journey / neighbour> | <SHA + artifact/env> | <PASS / FAIL / BLOCKED / NOT RUN> | <PASS / FAIL / FLAKY / BLOCKED / NOT TESTED> | <durable link> |

After all required rows pass Stages 3–4, append one QA-owned Bug Case disposition event:
`verified`, `reopened`, `blocked`, or `pending human caveat`.

## Attempts

Append one row per scenario attempt or skipped/quarantined observation. A retry gets a new attempt
number; it never replaces an earlier raw outcome or scenario classification.

| Attempt | Previous attempt | Started at | Completed at | SC-ID | AC-ID | Ticket | Full source SHA | Exact artifact/environment revision | Artifact-provenance source / receipt | QA layer / risk probe | Method/command or manual steps | Raw attempt outcome | Scenario classification (Result) | Evidence | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <1> | <none> | <timestamp> | <timestamp / in-progress> | <SC-002> | <AC-2> | <ID> | <SHA> | <artifact/env> | <source + receipt> | <integration / E2E / exploratory / non-functional> | <configured QA command or exact manual steps> | <PASS / FAIL / BLOCKED / NOT RUN> | <PASS / FAIL / FLAKY / BLOCKED / NOT TESTED> | <durable screenshot/video/trace/log/assertion link> | <risk result> |

Normalize each appended row using this ordered precedence. Evaluate top to bottom; the **first
matching rule wins**:

- An executed attempt records raw `PASS`, `FAIL`, or `BLOCKED`. A skipped, quarantined, or
  unavailable attempt records raw `NOT RUN`; it is still an appended observation with evidence.

1. Latest raw outcome `NOT RUN` → scenario classification `NOT TESTED`.
2. Latest raw outcome `BLOCKED` → scenario classification `BLOCKED`.
3. Otherwise, any raw `FAIL` plus raw `PASS` for the same scenario and QA-RUN-ID → `FLAKY`.
4. Otherwise, latest raw outcome `PASS` → `PASS`.
5. Otherwise, latest raw outcome `FAIL` → `FAIL`.

- The acceptance report uses the latest scenario classification, never a raw attempt outcome, and
  links every attempt that contributed to `FLAKY`, `BLOCKED`, or `NOT TESTED`.

Composed-history examples:

- `FAIL → PASS` → `FLAKY`
- `PASS → FAIL` → `FLAKY`
- `FAIL → PASS → BLOCKED` → `BLOCKED`
- `FAIL → PASS → NOT RUN` → `NOT TESTED`

Every attempt inherits and records the ledger's full source SHA, exact artifact/environment
revision, artifact-provenance source, and provenance receipt. If any value changes, start a new
QA-RUN-ID and retain the old ledger.

## Assertion audit

One section per QA-RUN-ID and scenario audited in Stage 4. The denominator must equal the number of
rows; `scripts/fake_green.py check` recomputes the verdict and rejects a count that disagrees.

### Assertion audit — <QA-RUN-ID> / <SC-ID>
- Denominator: <N> assertions in the QA checks executed for this scenario

| Assertion | Classification | Reason |
|---|---|---|
| `<file:line>` | <static / weak / ok> | <required unless `ok`> |

A rejected audit appends a new raw `BLOCKED` observation and `BLOCKED` scenario classification for
each affected scenario, preserving every earlier attempt.

## Resume state

- **Last durable attempt:** <attempt>
- **Resume from:** <next scenario / interrupted attempt>
- **Blocker:** <none / missing capability / environment / artifact mismatch>
- **Next safe action:** <append attempt; never overwrite>
