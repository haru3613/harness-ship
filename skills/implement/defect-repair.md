# Defect repair entry — opt-in

Load this only when `bug-workflow` hands `implement` a versioned defect packet instead of a delivery
ticket. Ordinary ticket delivery never touches it.

## The packet

`implement` also accepts a versioned defect packet `HS-DEFECT-PACKET/v1` from `bug-workflow`, using
`defect-repair-receipt-template.md`. The packet must contain one stable BUG-ID classified
`product-defect`, the approved contract revision with `SC-ID → AC-ID → originating ticket`, the
original failed-artifact evidence, a `diagnose` receipt whose status is `diagnosed`, and the next
append-only repair attempt number. An `inconclusive` or `reproduction-blocked` diagnosis stops
before any worktree or code change.

RD owns root-cause repair, regression coverage, TDD, and review; root's ownership of worktrees, PRs,
CI, deployment, and tracker mutations is unchanged. After the fix merges and RD verification passes,
append the implement defect receipt; after the controller deploys that exact source, append the new
deployment receipt under the same BUG-ID and attempt. The QA return handoff names the exact new full
source SHA, the new deployed artifact/environment revision, affected SC-IDs, and the RD verification
summary. Complete the product-defect addendum in `testing-workflow/qa-handoff-template.md` and
preserve every prior attempt. **`implement` must never set `verified`** — only `testing-workflow`
may append the QA verification attempt and disposition.
