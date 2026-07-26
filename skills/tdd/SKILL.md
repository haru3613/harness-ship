---
name: tdd
description: >-
  Implement one ticket through evidence-backed test-driven development: establish a green baseline,
  prove one behaviour is missing with a valid RED, add the smallest implementation for GREEN, and
  repeat at the approved test seams. Use during dev-workflow implementation, for test-first feature
  work, or for regression fixes. Triggers: "/tdd", "test first", "red green", "write the failing
  test", "implement this ticket".
---

# tdd

Turn an approved ticket into working code through small **RED → GREEN** cycles. TDD owns RD's unit
and contract tests. It does not replace `testing-workflow`: QA still owns integration and E2E
execution after handoff.

## Inputs — inherit the approved contract

Before editing code, read:

- the ticket's acceptance criteria and approved contract revision,
- its SC-ID → AC-ID traceability,
- the test seams and interfaces chosen in the spec,
- the repository's test commands and conventions.

Do not ask the user to approve the seams again. They were settled with the spec and acceptance
contract. If implementation reveals a different seam but does not change observable behaviour,
record the test-decision correction on the ticket. If it changes expected behaviour, stop and return
to `dev-workflow` Stage 3 for a revised acceptance contract.

For a bug-loopback ticket, the confirmed reproduction and regression criterion are the contract
when no new product behaviour is being introduced.

## Test quality

Test behaviour through a module's public interface at an approved seam. Prefer real implementation
behind that interface; replace only external adapters when isolation is necessary. A refactor that
preserves behaviour should not break the test.

Expected values must come from an independent source: the approved scenario, a worked example, a
known literal, or a protocol/schema contract. Never recompute the expected value with the same logic
as the implementation.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for adapter guidance.

## One cycle

### 0. Baseline

Run the narrowest relevant existing test command. If it is already red for an unrelated reason,
stop and report the pre-existing failure; do not bury it under the new change.

### 1. Choose one behaviour slice

Select the smallest observable outcome from one SC-ID / AC-ID pair. Name the seam and interface
where a caller observes it. Do not write all of a ticket's tests up front.

### 2. RED — prove the behaviour is missing

Write one focused test, run it, and capture the command plus failure reason.

A valid RED:

- reaches the intended interface,
- fails on the assertion that expresses the missing behaviour,
- would pass once that behaviour exists.

Syntax errors, import failures, broken fixtures, unavailable infrastructure, and unrelated failing
tests are **invalid REDs**. Repair the test harness and rerun until the failure proves the intended
gap. If the new test passes immediately, determine whether the behaviour already exists or the
assertion is insensitive; do not manufacture a failure.

### 3. GREEN — add the smallest implementation

Change only enough production code to satisfy that behaviour. Do not anticipate later slices or
add speculative options. Run the focused test, then the relevant surrounding suite.

### 4. Repeat

Record the cycle, select the next behaviour slice, and return to RED. Keep the ticket vertical:
one test → one implementation increment → one verified outcome.

## Refactoring and review

Do not mix structural redesign into GREEN. After the behaviour slices pass, run `review`; any
standards-only cleanup must keep the relevant suite green. If review changes observable behaviour,
start a new RED cycle. A wide prefactor remains its own ticket as defined by `tickets`.

A pure refactor ticket has no honest missing-behaviour RED. State that exception, establish
characterization or existing regression coverage, and keep it green throughout instead of creating
a fake failing test.

## TDD receipt

Attach this concise evidence to the ticket or PR before review:

```markdown
## TDD receipt
- Contract: <spec-id>/acceptance-vN
- Slice: <SC-ID> → <AC-ID> (or regression criterion)
- Seam/interface: <where behaviour is observed>
- RED: `<command>` — failed because <expected missing behaviour>
- GREEN: `<command>` — passed
- Regression: `<command>` — passed
- Tests changed: <behaviours covered>
- Not covered: <honest exclusions>
```

One receipt may list multiple cycles, but every behaviour-changing slice needs its own RED and GREEN
evidence. The receipt is implementation evidence, not the final acceptance report.
