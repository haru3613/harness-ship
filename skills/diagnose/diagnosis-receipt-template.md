# Diagnosis Receipt

- **Stable BUG-ID:** `<existing BUG-ID>`
- **Diagnosis attempt:** `<append-only number>`
- **Status:** `diagnosed | inconclusive | reproduction-blocked`
- **Acceptance contract / trace:** `<revision; SC-ID → AC-ID → originating ticket>`
- **Original failed-artifact evidence:** `<artifact/environment + ledger/evidence links>`
- **Observation method:** `<safe deterministic command or bounded non-destructive observation>`
- **Safety constraint:** `<none | unsafe | destructive | production-only | intermittent>`
- **Observed result:** `<what the evidence showed>`
- **Falsifiable hypotheses tested:** `<hypothesis → distinguishing evidence>`
- **Root cause / remaining uncertainty:** `<cause or unresolved alternatives>`
- **Safe repair seam:** `<approved RD seam | not established>`
- **Resume condition:** `<none | evidence/access needed>`
- **Recorded by / at:** `<RD identity + ISO-8601>`

Append this receipt to the same stable BUG-ID. Never overwrite an earlier diagnosis attempt, force
an unsafe reproduction, edit product code, create a second defect, or mark the case verified.
