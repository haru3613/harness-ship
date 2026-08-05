# Bug Case

Written to `.harness-ship/bugs/<BUG-ID>.md`. Diagnosis Receipts append to the same file.

- **Stable BUG-ID:** `BUG-<tracker-or-portable-id>` — assign once
- **Phase:** `intake | classification | routed | blocked | needs-evidence`
- **Classification:** `pending | product-defect | test-defect | environment-defect | spec-ambiguity | duplicate | known-limitation`
- **Disposition:** `<owner + next action | pending>`
- **Test Contract revision:** `<contract-id/revision>`
- **Trace:** `<scenario ID → baseline/release delta → originating work>`
- **Full source SHA:** `<40-character SHA>`
- **Exact tested artifact/environment revision:** `<artifact + non-production environment>`
- **Artifact provenance receipt:** `<durable link/receipt>`

## Observation

- **Expected:** `<approved expected behaviour>`
- **Actual:** `<observed behaviour and user impact>`
- **Reproducibility:** `<always/intermittent/unknown + bounded attempts>`
- **Evidence:** `<ledger attempt + screenshot/video/trace/assertion links>`

## Classification evidence

`<why the evidence supports this classification; alternatives ruled out>`

## Append-only history

Never replace or overwrite an event. Append every classification, handoff, diagnosis, blocker,
needs-evidence resume, and retest under the same stable BUG-ID.

| Timestamp | Phase | Classification | Disposition / owner | Event and evidence | Previous event |
|---|---|---|---|---|---|
| `<ISO-8601>` | `intake` | `pending` | `test triage` | `<source ledger attempt>` | `none` |

## Repair handoff

- **Diagnosis Receipt:** `<link | not produced>`
- **Shared-root-cause reach:** `<affected callers, from the Diagnosis Receipt | reaches only the reported caller>`
- **Expected fixed behaviour:** `<observable outcome, covering every affected caller>`
- **Affected scenarios:** `<scenario IDs>`
- **Retest evidence required:** `<candidate provenance + checks>`

The repair method is intentionally unspecified. A fixed candidate returns with its repair summary,
full source SHA, exact artifact/environment revision, and new provenance receipt.
