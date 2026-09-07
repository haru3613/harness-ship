---
name: testing-workflow
description: >-
  Test a candidate using current task scope, existing coverage, and concrete risks. Report what
  passed, what failed, and what remains unverified. Use when asked to test a release candidate
  or verify an artifact.
---

# testing-workflow

Read the repository instructions, current task, relevant changes, and existing tests. Use the
repository's configured tools and a reproducible non-production surface. A Test Contract,
contract revision, candidate handoff, and `.harness-ship/` directory are optional; their absence or
age does not prevent testing. Existing issue criteria and user decisions are sufficient inputs.

## 1 — Establish scope and candidate

Identify what changed, the expected user behaviour, core regressions, and risks at affected
boundaries. Read existing criteria where useful, including `.harness-ship/test-contract.md` if
present. Carry forward standing requirements explicitly applicable to this release. Historical
release-specific requirements need a current reason to apply; do not import an old checklist
wholesale. Explain scope decisions. Ask only when an unresolved expectation or safety decision
changes the next action; continue independent checks while waiting.

Record once at execution start:

- full source SHA and local modifications, or the actual external build identifier;
- the tested build/artifact, environment, and how they map to that source;
- entry point, safe fixtures/accounts, and relevant permissions.

Use the candidate owner's identifier, never this test repository's HEAD as a substitute. Missing
provenance limits the conclusion: safe exploration can continue, but observations do not prove a
release artifact. Never seed production or execute this workflow against production.

## 2 — Choose the cheapest effective checks

Use existing tests and commands covering the changed behaviour, nearby regressions, negative and
permission cases, and relevant integration boundaries. Add migration, recovery, device, provider,
performance, or other checks only when current risk or explicit project policy calls for them.
Run required repository checks. Do not create a framework or duplicate layers to fill a checklist.

Reuse valid results for unchanged code when the relevant dependencies, configuration, fixtures,
and environment remain applicable. State the original tested identity and why reuse applies.
An older result alone never proves a new binary, deployment, signing configuration, or external
provider. Run the affected checks when that boundary changed or equivalence cannot be established.
Preserve an explicit requirement to run automation on the exact candidate.

Manual and exploratory checks can provide real behavioural evidence. Identify their scope and
limits; they do not silently replace automation explicitly required by the project or user.

## 3 — Execute and investigate

Run the selected checks and preserve commands/steps, results, and useful evidence links in one
summary. Recheck identity and scope when code, deployment, environment, or criteria change, rather
than before every unchanged test action. Stop affected checks on unsafe drift.

Distinguish PASS, FAIL, FLAKY, BLOCKED, and NOT TESTED. A failure followed by a pass under unchanged
conditions is FLAKY; retain both attempts. A repair or environment change starts a distinct retest
with the change recorded. Missing infrastructure is not PASS or a product defect.

Before trusting green results, check that assertions observe meaningful behaviour, have independent
expected values, and expose relevant runtime errors. Correct weak tests through
`exploratory-testing` when test changes are authorized, then rerun affected coverage.

Classify findings briefly before acting. Fix a routine test/environment problem within authorized
scope and rerun it. Use `bug-workflow` when a defect needs durable tracking, unresolved investigation,
or handoff; a non-pass does not automatically require a Bug Case. Preserve the original failure and
verify the repaired candidate without imposing a separate approval step on already-authorized work.

## 4 — Hand over one useful summary

Use [human-thread-template.md](human-thread-template.md) as an optional outline. State what was
tested, candidate/environment, commands and actual results, reused evidence with its limits, and
remaining user-visible risks. Name the next useful action. Testing completion is not release approval.

Prefer the existing PR/issue testing section or the user's chosen evidence location. A separate
handoff, ledger, report, fixed path, or contract revision is not required. Existing candidate files
remain readable evidence; link them instead of copying them. Optional detailed templates are
[candidate-handoff-template.md](candidate-handoff-template.md),
[execution-ledger-template.md](execution-ledger-template.md), and
[test-report-template.md](test-report-template.md) when a multi-person run benefits from them.

Publish only when the user has authorized that PR/issue write. Otherwise return the summary in the
session. When updating a candidate comment, resolve the exact review target and candidate key, find
its `<!-- harness-ship:testing:<candidate-key> -->` marker, and update only a single match owned by
the current authenticated identity. With zero matches, create one; with multiple matches or another
author's match, report the conflict without editing or duplicating it. Publication failure does not
change test results. Keep secrets, credentials, raw tokens, fixture PII, and full logs out of comments.
