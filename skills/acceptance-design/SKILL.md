---
name: acceptance-design
description: >-
  Turn an approved spec's acceptance criteria into a versioned, platform-neutral acceptance
  contract before implementation. Use at dev-workflow's acceptance gate, or when asked to design
  acceptance scenarios, journeys, Given/When/Then cases, or a P0/P1 acceptance matrix.
---

# acceptance-design

Design the behavioural contract that implementation and QA share. This is a **design only** skill:
it translates an approved spec, without inferring expected behaviour from implementation.

## Inputs

Require the current approved spec and its stable acceptance criteria. If criteria are missing,
ambiguous, or not externally observable, return to `spec`; do not invent the product decision here.
If an approved acceptance contract already exists, preserve its identifiers unless observable
behaviour changes.

## Produce the acceptance contract

Assign the scenario set the identifier `<spec-id>/acceptance-vN`. Start at `acceptance-v1` and
increment `vN` only when approved behaviour changes. Publish it alongside the spec.

Every scenario must contain:

- a stable SC-ID and its stable AC-ID mapping, written explicitly as **SC-ID → AC-ID**;
- priority **P0** or **P1**: P0 covers core value, money, auth, or a flow that must never break;
  P1 is important but degradable;
- the user-visible **surface**, such as `[UI]`, `[APP]`, or `[API/contract]`;
- platform-neutral **Given / When / Then** behaviour;
- a **negative assertion**: what must not happen;
- a **QA-executable seam**: the observable boundary at which QA can prove the behaviour without
  depending on implementation internals;
- **fixture/data needs**, including required state, accounts, permissions, and safe seed data, or
  `none`;
- a **QA assurance profile** naming the intended integration or E2E layer, automation expectation,
  required evidence, and risk-specific probes.

Show the complete set as a P0/P1 matrix so omissions and priority are reviewable. Map every stable
SC-ID to at least one stable AC-ID, and map every in-scope AC-ID to at least one scenario. Do not
silently renumber identifiers when revising the contract.

## Gate and stop

Check that the scenarios describe the spec rather than the current code, that every assertion is
observable at its QA-executable seam, and that fixture/data needs are safe outside production.
Present the spec criteria and scenario set together for user approval.

Then **stop**. Do not implement or generate runner code. Do not begin QA execution. Implementation
starts only after approval of the named acceptance-contract revision; QA execution starts only after
the later dev→QA handoff names that approved revision and the exact artifact under test.
