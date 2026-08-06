# Test Contract — `<contract-id>` rev.`<n>` — `DRAFT | APPROVED`

Drafted to `.harness-ship/test-contract.draft.md`; at approval it replaces
`.harness-ship/test-contract.md`, which holds only the approved revision.

While `DRAFT`, `release-gate` returns `NO-GO`. Only the user approves this contract.

- **Product type and supported surfaces:** `<what ships, on what>`
- **Release target:** `<milestone or release train>`
- **Release surface owner:** `<this repository | the repository, team, or vendor that owns the candidate and decides its release>`
- **Visible from here:** `<all — this repository owns the surface | what of the owner's CI, provenance, and artifacts this repository can actually read>`
- **Revision reason:** `<new project | test audit | release delta | approved change to expected behaviour>`

An owner other than this repository means `release-gate` returns `NO-GO` because the verdict belongs
to the owning repository. That is intended, not a gap to close here.

Unchanged baseline content from an earlier revision is referenced, never copied or re-approved.

## Project Test Baseline

### Established capability

| Layer | Command or exact manual steps | Environment, fixtures, permissions | Status |
|---|---|---|---|
| `<unit/API/E2E/manual>` | `<established command>` | `<what it needs>` | `<green/red/flaky/skipped/not-configured>` |

- **Safe test-data rule:** `<fixtures and environments that may be written; never production>`

### Scenarios

Stable IDs survive retirement so old evidence stays interpretable. Unknown capability is
`not-configured`, never PASS.

| Scenario ID | Journey | P0/P1 | Expected (externally observable) | Forbidden | Cheapest stable seam | Method | Evidence required | Classification | Reason |
|---|---|---|---|---|---|---|---|---|---|
| `<SC-001>` | `<journey>` | `<P0>` | `<what the user must be able to do>` | `<what must never happen>` | `<layer + a citation that resolves: path::test name, command, or CI job>` | `<automated/manual/exploratory/not-configured>` | `<what a passing run must produce>` | `<required/observe-only/deferred/retired>` | `<why>` |

P0 covers core value, auth, money, destructive state changes, or a flow that must not regress. When
a seam cannot prove a scenario, say so in the seam column rather than recording a weaker proof. A
`retired` scenario keeps its ID and its row so earlier evidence stays interpretable.

An `automated` row's seam must stay resolvable against the repository — `release-gate` re-resolves
it at the candidate SHA, and a citation that no longer exists makes the row unevaluated rather than
passing.

### Source-to-artifact provenance

- **Method:** `<how a tested artifact is bound to a full source SHA | not-configured>`
- **Candidate identifier:** `<the full source SHA — or, when this repository did not build the candidate, what it exposes plus what that is read from and what makes it unique per candidate>`
- **Durable evidence location:** `.harness-ship/candidates/`, one directory per candidate

`not-configured` provenance blocks release on its own; no amount of passing tests substitutes for it.

### Prior failure evidence

What has already broken, clustered by mechanism. Sampled history yields floors, not ceilings.

| Mechanism | Recurrences | Escaped or caught | Evidence and source | Maps to | Existing defence | Classification |
|---|---|---|---|---|---|---|
| `<one sentence: what actually goes wrong>` | `<count + date range>` | `<escaped / caught before release / unclassified>` | `<this repo or predecessor: commits, incidents, prior Bug Cases and Diagnosis Receipts>` | `<SC-001 / none — baseline gap>` | `<what already guards it / none>` | `<required / observe-only / deferred>` |

- **Sampling method and limits:** `<what was read, what was not>`
- **Classification rule used:** `<what counted as escaped; unclassified stays unclassified rather than guessed>`

### Deferred and out of scope

| Item | Reason |
|---|---|
| `<scenario or risk>` | `<product decision, dropped surface, or blocked dependency>` |

## Release Delta — `<candidate>`

- **Full candidate source SHA:** `<40-character SHA | not yet fixed | unobtainable — this repository did not build the candidate and the owner does not expose one; blocks the source gate on its own>`
- **Source range:** `<base..head>`
- **Release scope:** `<what this candidate changes>`
- **Affected baseline scenarios:** `<SC-IDs; unchanged ones are referenced, not restated>`
- **New or changed behaviour and risks:** `<what is newly at stake>`
- **Added scenarios or evidence requirements:** `<SC-IDs added by this delta>`

| Operational check | Applicable | Evidence or reason |
|---|---|---|
| Migration | `<yes/no>` | `<evidence, or the concrete reason it is not applicable>` |
| Compatibility | `<yes/no>` | `<...>` |
| Security | `<yes/no>` | `<...>` |
| Performance | `<yes/no>` | `<...>` |
| Accessibility | `<yes/no>` | `<...>` |
| Recovery | `<yes/no>` | `<...>` |
| Rollback | `<yes/no>` | `<...>` |

Mark an item not applicable only with a concrete reason. Without one the item is unevaluated, not
inapplicable, and it blocks like any other missing evidence.

## Approval

- **Decisions required from the user:** `<the specific choices this revision cannot make alone>`
- **Approved by / date:** `<user + date | pending>`

After approval, any semantic change to expected behaviour, priority, required evidence, test method,
or blocking status creates a new revision. Implementation details and equivalent seam corrections do
not.
