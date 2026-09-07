---
name: release-gate
description: >-
  Assess whether a candidate is ready to release from current scope, actual test evidence, and
  remaining risks. Return GO, GO WITH CAVEATS, or NO-GO without performing the release.
---

# release-gate

Evaluate existing evidence; this skill is read-only and does not run suites, merge, deploy, tag,
publish, or mutate production. Read the current task and repository release policy first.

## Establish what is being released

Identify the intended release surface, candidate source SHA or external build identifier, artifact,
and environment. Read the PR/issue, relevant changes, CI results, test summaries, and user decisions.
An existing `.harness-ship/test-contract.md` may help explain criteria; it is optional, as are
handoff, ledger, and report files. Missing, stale, draft, or differently formatted documents alone
are never a release blocker. Do not ask the user to create or refresh a contract to obtain a verdict.

Apply current explicit requirements and risk-based checks for this candidate. Distinguish standing
project policy from requirements for an older release. Explain why a historical check still applies
or falls outside this release. Preserve explicit current user review gates; ask about a material
conflict rather than silently dropping a required check. An old contract's age does not erase a
real unresolved defect or a still-applicable security requirement.

For a separately owned release surface, evaluate the actual owner's candidate if evidence is
accessible. Never substitute the test repository's HEAD. If visibility is partial, give a bounded
assessment of what is known and identify the missing evidence that prevents a full verdict.

## Evaluate actual evidence

- **Source and artifact:** verify what checks ran and which build/environment they cover. Skipped,
  stale, or mismatched results are not successful evidence for the candidate. Reuse unchanged-code
  results only with a stated equivalence rationale covering dependencies/configuration/environment;
  new binary, signing, deployment, and provider behaviour need evidence at those boundaries.
- **Behaviour:** assess changed journeys, core regressions, negative/permission cases, and relevant
  boundaries. A green suite proves only what it observes. Manual/exploratory evidence counts for
  its demonstrated scope; preserve explicitly required automation.
- **Operational risk:** require migration, recovery, device/provider, compatibility, or other
  evidence when this change or standing policy warrants it. Name the concrete risk behind a gap.
- **Remaining findings:** distinguish failures, flaky checks, blocked checks, and untested scope.
  Inspect referenced results rather than trusting a PASS label. Retain prior failed attempts and
  the explanation/evidence for a successful repair.

There is no universal coverage percentage, framework list, document layout, or interview gate.

## Give a decision the release owner can use

- **NO-GO:** a concrete release-blocking defect, source/artifact mismatch, missing evidence for a
  material risk, or an unmet current explicit requirement. State the user impact and cheapest
  action that resolves it. An unknown required outcome is not PASS.
- **GO WITH CAVEATS:** the candidate has sufficient evidence for the release scope and only
  non-blocking risks remain. State their impact, evidence limits, and useful follow-up. This is a
  recommendation, not invented user acceptance; preserve any explicit acceptance gate before release.
- **GO:** applicable requirements and material risks are covered by valid evidence with no
  outstanding release caveat.

Lead with the verdict and reason, then candidate/artifact/environment, commands or evidence links,
remaining risks, and the human release action. A short PR-ready summary is enough; no separate
contract revision or gate ledger is needed. Do not publish the summary from this read-only skill.
