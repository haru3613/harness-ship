---
name: acceptance-design
description: >-
  Turn a current stable spec's acceptance criteria into a versioned, platform-neutral acceptance
  contract before implementation. Use at dev-workflow's acceptance gate, or when asked to design
  acceptance scenarios, journeys, Given/When/Then cases, or a P0/P1 acceptance matrix.
---

# acceptance-design

Design the behavioural contract that implementation and QA share. This is a **design only** skill:
it translates the current stable spec without inferring expected behaviour from implementation.

**Prerequisite:** read the project's `## harness-ship` config in `AGENTS.md` / `CLAUDE.md`,
including the configured tracker/access path and forbidden tools. Run `setup` if the block is
absent; publishing must use that configured path.

## Inputs

Require the current stable spec and its stable acceptance criteria. If criteria are missing,
ambiguous, or not externally observable, return to `spec`; do not invent the product decision here.
Do not require a separate spec-approval gate: `dev-workflow` presents the spec criteria and scenario
set together at its acceptance-contract gate, where the user approves them. If an approved
acceptance contract already exists, preserve stable SC-ID and AC-ID values unless observable
behaviour changes; the contract revision still follows the rule below for every approved content
change.

## Produce the acceptance contract

Assign the scenario set the identifier `<spec-id>/acceptance-vN`. Start at `acceptance-v1` and
publish it alongside the spec. After approval, increment `vN` whenever **any approved contract
content changes**, including behaviour, priority, surface or QA-executable seam, fixture/data needs,
or the QA assurance profile. Preserve stable SC-ID and AC-ID values when behaviour is unchanged;
draft edits before the first approval stay within `acceptance-v1`.

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

Every **P0 assurance profile** expects the scenario to be automated on every PR. If that is not
currently possible, record a manual P0 exception with explicit user approval, a follow-up ticket,
owner, expiry, exact-candidate execution method, and required evidence. The exception caps the
acceptance verdict at **Accept with caveats** until its automation ticket closes.

Show the complete set as a P0/P1 matrix so omissions and priority are reviewable. Map every stable
SC-ID to at least one stable AC-ID, and map every in-scope AC-ID to at least one scenario. Do not
silently renumber identifiers when revising the contract.

## Gate and stop

Check that the scenarios describe the spec rather than the current code, that every assertion is
observable at its QA-executable seam, and that fixture/data needs are safe outside production.
Present the spec criteria and scenario set together for explicit user approval. **Only the user may
approve** the acceptance contract; never self-approve it. Until that approval is recorded, label
the result an **unapproved draft** and stop.

Then **stop**. Do not implement or generate runner code. Do not begin QA execution. Implementation
starts only after approval of the named acceptance-contract revision; QA execution starts only after
the later dev→QA handoff names that approved revision and the exact artifact under test.
