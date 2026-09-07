---
name: exploratory-testing
description: >-
  Explore a completed feature before automating it, then read the existing test system and add the
  minimum sufficient regression coverage in the same context. Use when a new feature is runnable,
  when automation is about to be written, or when someone asks for exploratory testing. Triggers:
  "/exploratory-testing", "explore this feature", "test this manually before automating it".
---

# exploratory-testing

Learn how the feature actually behaves before choosing automation. This skill may edit test code.
It never changes expected behaviour to match an implementation. The only permitted product-code
edit is the temporary one-line P0 sensitivity injection below, on a local working copy, reverted
before anything else.

Read repository instructions, the current task, and explicit expected behaviour first. An existing
Test Contract is optional context. Missing or stale contract paperwork never prevents exploration
or test authoring. Clarify a material ambiguity before encoding it as an automated expectation;
continue independent work meanwhile.

## Candidate boundary

Use a runnable **non-production** surface: local, preview, simulator, or QA. Record:

- full source SHA and local changes, or the actual external candidate identifier;
- artifact/build/environment revision and how it maps to that SHA or identifier;
- access path, fixtures, permissions, and test data; and
- evidence destination.

Without trustworthy provenance, observations may guide investigation but cannot become release
evidence. Never seed synthetic data into production.

## Pass A — black-box exploration

Before reading existing test code, read only the approved behaviour, feature intent, and user-facing
surface. Exercise a bounded set of paths chosen by risk:

- the P0 happy path;
- invalid, empty, boundary, and permission states;
- interruption, retry, recovery, or state transitions where applicable; and
- interactions with the nearest external boundary.

Capture exact steps, observations, console/runtime failures, and durable evidence. If observed
behaviour contradicts the intended behaviour, preserve the finding and fix/retest within authorized
scope. Use `bug-workflow` when tracking or handoff is needed. Clarify ambiguous expectations before
automating them; no revised contract is required.

## Pass B — existing-test audit

After exploration:

1. inventory the complete test tree, runners, and CI wiring;
2. deeply read tests for the feature, the same public seam, overlapping user journeys, shared
   fixtures/helpers, and nearby failure modes; and
3. map every exploration finding to existing coverage before proposing a new case.

Large repositories do not require reading every unrelated test file.

## Minimum sufficient automation

Choose the cheapest stable seam that catches the failure a user would care about. Extend an existing
test or table-driven case before adding another file. Use E2E only when the risk crosses meaningful
product boundaries. Any layer—unit, contract, integration, or E2E—is allowed; selection follows risk
and seam stability, not role ownership.

There is no numeric test limit. Every new case must state:

- the distinct behaviour or risk it covers;
- the nearest existing test and why its current assertions do not cover the risk; and
- the concrete failure that would escape without this case.

If that marginal coverage cannot be shown, do not add the case.

For critical new coverage, check sensitivity: does the test fail for the wrong behaviour it claims
to catch? A meaningful RED observed before a fix already answers that question. Where behaviour
already works and sensitivity is uncertain, use a focused temporary fault on an isolated local
working copy when safe. Compare the new and nearest existing tests, then revert the fault and rerun
the same checks before any other work. Never inject into a shared/deployed surface or commit it.
An overly broad fault proves little; aim at the specific forbidden outcome. If existing coverage
already catches that exact risk, improve or reuse it rather than adding a redundant test.

Record useful sensitivity evidence with the test result. This checks assertion quality; it does
not require a contract row, revision, or receipt before a test can count as automation. A missing
historical sensitivity record alone is not a release blocker; a demonstrated ineffective assertion
is a real coverage gap.

Write the minimum sufficient tests in the same context as exploration. Run the changed tests and
the nearest relevant regression scope. Run a full suite only when repository policy requires it or
the suite is already cheap. Never install a framework without explicit user approval.

Choosing the right seam does not make the test at that seam a good one. Follow
[behaviour-first tests](tests.md) and [replacing dependencies](mocking.md) for the
test's own construction, and [scenario-craft.md](../test-plan/scenario-craft.md) when exploration
turns up a risk whose expected or forbidden outcome needs a clearer definition.

## Exploration report

Return one concise summary of candidate/environment, paths explored, findings, relevant existing
coverage, tests changed, commands/results, and remaining risks. Use the existing PR/issue or chosen
location when writes are authorized; separate contract and candidate records are optional.

Manual/exploratory observations count for their demonstrated scope. They do not replace explicitly
required automation. Reuse unchanged-code evidence only with an equivalence rationale; an earlier
run alone does not prove a new artifact or changed environment.
