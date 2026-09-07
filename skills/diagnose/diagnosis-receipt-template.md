# Diagnosis Receipt

Optional detail for substantial investigation. Append to the existing issue or chosen record.

- **Finding:** `<existing issue or observation>`
- **Diagnosis attempt:** `<append-only number>`
- **Status:** `diagnosed | inconclusive | reproduction-blocked`
- **Original failed-artifact evidence:** `<artifact/environment + ledger/evidence links>`
- **Observation method:** `<safe deterministic command or bounded non-destructive observation>`
- **Safety constraint:** `<none | unsafe | destructive | production-only | intermittent>`
- **Observed result:** `<what the evidence showed>`
- **Falsifiable hypotheses tested:** `<hypothesis → distinguishing evidence>`
- **Root cause / remaining uncertainty:** `<cause or unresolved alternatives>`
- **Safe repair seam:** `<observed seam | not established>`
- **Expected fixed behaviour / retest:** `<observable outcome + affected scenarios>`
- **Resume condition:** `<none | evidence/access needed>`
- **Recorded by / at:** `<identity + ISO-8601>`

## Shared-root-cause reach

Required for a `diagnosed` status. The seam is only as wide as the callers it covers.

| Caller or entry point of the root cause | Affected | Distinguishing evidence |
|---|---|---|
| `<path:symbol>` | `yes/no` | `<what shows it is affected, or rules it out>` |

A row may name a call surface rather than an individual caller when that is the honest unit — every
external consumer of a public entry point, or every dispatch through one dynamic seam. `<root cause
reaches only the reported caller>` is a valid single row when the evidence establishes it. An
unenumerated caller is not a caller ruled out.

Keep this result with the original finding. Never overwrite an earlier diagnosis attempt, force
an unsafe reproduction, edit product code, create a second defect, or mark the case verified.
