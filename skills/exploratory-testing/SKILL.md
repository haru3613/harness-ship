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

Read repository instructions and the current Test Contract at `.harness-ship/test-contract.md`
first. Exploration may proceed against a draft, but do not author automated expectations until the
relevant behaviour is user-approved.

## Candidate boundary

Use a runnable **non-production** surface: local, preview, simulator, or QA. Record:

- full source SHA, or the candidate identifier where the contract's **Release surface owner** is not
  this repository;
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
behaviour contradicts the Test Contract, record a Bug Case at `.harness-ship/bugs/<BUG-ID>.md`; do
not automate the defect as expected behaviour. If expected behaviour is ambiguous, stop for a
revised Test Contract.

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

Those three are an argument, made by whoever wants the case to exist and checked by nobody. For a
**P0 scenario** an argument is not enough: the row is classified `automated` only once something has
shown the test failing for the reason the row names.

If the new test is a valid RED — it reaches the intended interface and fails on the assertion that
names the missing behaviour — that watched fail is the receipt. Record the test, the command, and
the failure reason.

If the behaviour already exists, there is no honest RED to watch. A test that passes on its first
run may assert the right thing, the wrong thing, or nothing at all. Produce the substitute on a
**local working copy only** — never the exploration surface recorded above, never a deployed,
shared, preview, or QA candidate, and never a commit. Inject the row's **forbidden** state in one
line of product code, run the new test and the nearest existing tests, then revert:

- **new test fails, existing tests stay green** — the coverage is real and specific. This is the
  receipt.
- **existing tests go red too** — that risk was already covered. Re-aim at the exact forbidden
  state before concluding the new test is redundant; a break wide enough to redden everything
  proves nothing about either.
- **new test passes** — it does not catch what it claims, whatever else it asserts. Fix the test,
  not the mutation.

Aim at the forbidden clause, not at the function. "Swap these two booleans at submit time" is the
mutation; "throw here" is not.

Revert before running anything else, and confirm the revert by re-running the same tests and seeing
the pre-injection results return. Record the injected line — the file and symbol it went into —
both commands, both results, and the confirmed revert. Then propose the row as `automated` in the
report's proposed Test Contract revision, citing that receipt. Until the receipt exists, propose
the row as `not-configured`. Below P0, the argument stands on its own.

Write the minimum sufficient tests in the same context as exploration. Run the changed tests and
the nearest relevant regression scope. Run a full suite only when repository policy requires it or
the suite is already cheap. Never install a framework without explicit user approval.

Choosing the right seam does not make the test at that seam a good one. Follow
[behaviour-first tests](tests.md) and [replacing dependencies](mocking.md) for the
test's own construction, and [scenario-craft.md](../test-plan/scenario-craft.md) when exploration
turns up a risk the contract has no scenario for.

## Exploration report

Publish one durable report containing candidate provenance, paths explored, observations and Bug
Cases, the existing-coverage map, the automation delta, changed test files, commands/results, and
any proposed Test Contract revision.

Exploration evidence satisfies a release criterion only when the approved Test Contract labels that
criterion `manual` or `exploratory`. It never substitutes for required automation, and evidence from
an earlier artifact never proves a later release candidate.
