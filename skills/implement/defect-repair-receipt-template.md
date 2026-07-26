# Defect Repair Packet and Receipt

## Versioned defect packet — `HS-DEFECT-PACKET/v1`

- **Stable BUG-ID:** `<existing product-defect BUG-ID>`
- **Classification:** `product-defect`
- **Acceptance contract / trace:** `<revision; SC-ID → AC-ID → originating ticket>`
- **Original failed-artifact evidence:** `<source SHA + artifact/environment + evidence links>`
- **Diagnosis Receipt:** `<diagnosed receipt link>`
- **Repair attempt:** `<append-only number>`

## Implement defect receipt

- **Repair attempt:** `<same number>`
- **Root-cause repair scope:** `<approved seam and changed behaviour>`
- **Exact fixed source SHA / PR:** `<40-character SHA + PR>`
- **RD unit regression RED → GREEN:** `<command + receipt>`
- **RD API-contract regression RED → GREEN:** `<command + receipt | not-applicable reason>`
- **TDD / review / CI evidence:** `<durable links>`
- **Controller worktree / recovery / tracker receipt:** `<durable link>`

## New deployment receipt

- **Stable BUG-ID / repair attempt:** `<same BUG-ID + repair attempt>`
- **Exact new full source SHA:** `<same fixed 40-character SHA>`
- **Exact new deployed artifact/environment revision:** `<immutable artifact + non-production env>`
- **Artifact provenance source / receipt:** `<binding evidence>`
- **Access path / fixtures:** `<safe QA access; no secrets>`
- **Affected SC-IDs:** `<original + risk-selected neighbours>`
- **RD verification summary:** `<informational only; QA does not rerun RD tests>`

## QA return

- **Fixed-artifact handoff:** `<durable QA handoff link>`
- **State:** `awaiting-QA`

Append this receipt to the same stable BUG-ID. It is not a QA verification attempt and must not set
`verified`.
