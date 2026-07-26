# Bug Case

- **Stable BUG-ID:** `BUG-<tracker-or-portable-id>` — assign once
- **Phase:** `intake | classification | routed | blocked | needs-evidence`
- **Classification:** `pending | product-defect | test-defect | environment-defect | spec-ambiguity | duplicate | known-limitation`
- **Disposition:** `<owner + next action | pending>`
- **Acceptance contract revision:** `<contract-id/revision>`
- **Trace:** `<SC-ID> → <AC-ID> → <originating ticket>`
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
| `<ISO-8601>` | `intake` | `pending` | `QA triage` | `<source ledger attempt>` | `none` |
