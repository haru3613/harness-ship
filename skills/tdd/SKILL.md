---
name: tdd
description: >-
  Opt in to evidence-backed test-driven development for one ticket: establish a green baseline,
  prove one behaviour is missing with a valid RED, add the smallest implementation for GREEN, and
  repeat at the approved test seams. Use only when the user explicitly requests TDD. Triggers:
  "/tdd", "test first", "red green", "write the failing test".
---

# tdd

Turn an approved ticket into working code through small **RED → GREEN** cycles. This is an optional
implementation technique, not a release prerequisite or a test-ownership boundary.

## Inputs — inherit the approved contract

Read the project's `## harness-ship` block before a baseline or edit. A supported **Config version**
is the gate; the plugin version is informational. If the block is absent or on an unsupported
Config version, run `setup` and stop until it is regenerated. Reconcile duplicate blocks directly;
setup must not guess which one to replace. Resolve missing test capabilities here before the
baseline. Do not reinterpret a legacy generic test command.

Before editing code, read:

- the ticket's expected behaviour and approved Test Contract revision when one exists,
- its scenario traceability,
- the test seams and interfaces chosen in the spec,
- any established test commands and repository conventions.

Resolve a missing capability only when the current slice needs it. Prefer an existing runner or
the language's standard library. For Python without an established unit-test runner, ask whether
the user wants to add `pytest`, and mention `unittest` as the no-dependency option. Do not ask during
setup or for an empty repository with no testable slice. Never install a framework or append its
command without approval. If the user declines and no native seam can cover this slice, report that
capability as missing; unrelated work remains unblocked. Never infer PASS.

Do not ask the user to approve an equivalent seam again. A different seam that preserves observable
behaviour is a test-decision correction recorded on the ticket. One that changes expected behaviour
stops and returns to `test-plan` for a revised Test Contract.

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

Run the narrowest relevant established test command. If the slice needs a
runner that has not been selected, resolve it as described above before claiming a baseline. If the
baseline is already red for an unrelated reason, stop and report the pre-existing failure; do not
bury it under the new change.

### 1. Choose one behaviour slice

Select the smallest observable outcome from one Test Contract scenario. Name the seam and interface
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

Select the next behaviour slice and return to RED. Keep the ticket vertical: one test → one
implementation increment → one verified outcome.

## Refactoring and review

Do not mix structural redesign into GREEN. After the behaviour slices pass, run `review`; any
standards-only cleanup must keep the relevant suite green. If review changes observable
behaviour, start a new RED cycle. A wide prefactor remains its own ticket as defined by `tickets`.

A pure refactor ticket has no honest missing-behaviour RED. State that exception, establish
characterization or existing regression coverage, and keep it green throughout instead of creating
a fake failing test.
