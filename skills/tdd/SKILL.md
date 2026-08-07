---
name: tdd
description: >-
  Run evidence-backed test-driven development for one ticket: green baseline, valid RED, smallest GREEN, repeated at the approved test seams.
disable-model-invocation: true
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

- the ticket's expected behaviour and approved Test Contract revision at
  `.harness-ship/test-contract.md` when one exists,
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
assertion is insensitive; do not manufacture a failure. When the behaviour already exists there is
no honest RED to watch — see [no RED to watch](#when-there-is-no-red-to-watch) for what stands in
for one.

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

## When there is no RED to watch

A RED you watched fail proves the test is sensitive to the behaviour it names: the assertion fired,
then it stopped. A test written against behaviour that already works never earns that proof — it
passes on its first run whether it asserts the right thing, the wrong thing, or nothing at all.

This skill is the only one that may edit code that ships, so producing the substitute is its job.
For a **P0 scenario** whose coverage was added without a RED — characterization for a refactor, or
a test for behaviour that already ships — inject the row's **forbidden** state in one line of
product code, run the new test and the nearest existing tests, then revert:

- **new test fails, existing tests stay green** — the coverage is real and specific. This is the
  receipt.
- **existing tests go red too** — that risk was already covered. Re-aim at the exact forbidden state
  before concluding the new test is redundant; a break wide enough to redden everything proves
  nothing about either.
- **new test passes** — it does not catch what it claims, whatever else it asserts. Fix the test, not
  the mutation.

Aim at the forbidden clause, not at the function. "Swap these two booleans at submit time" is the
mutation; "throw here" is not, and a suite that survives the first while catching the second was
never guarding the row.

**Scope, because this breaks working code on purpose:** a local working copy only — never a deployed,
shared, preview, or QA surface, and never a commit. Revert before running anything else, and confirm
the revert by re-running the same tests and seeing the pre-injection results return. A run that ends
between injection and revert leaves broken product code behind a report that says otherwise.

Record the injected line — the file and symbol it went into — both commands, both results, and the
confirmed revert, alongside the cycle's RED evidence. Then hand it to `test-plan` as the input for
the revision that promotes the row to `automated`. **`tdd` does not edit the contract**, the same way
a seam correction is recorded on the ticket rather than written into it: the promotion is a
classification change to an approved artifact, and only the user approves those.

The unit is the row's forbidden clause, not the slice. One P0 scenario has many slices, and a RED on
an earlier slice says nothing about a later one; a RED counts as this evidence only when the
assertion that fired is the one naming the row's forbidden clause. Greenfield REDs usually fail on
*the code path does not exist yet*, which is not sensitivity to *it stores the wrong field*.
