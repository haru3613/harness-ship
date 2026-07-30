---
name: test-plan
description: >-
  Create or revise the user-approved Test Contract that defines what must be proven before release.
  Use for a new project, an existing project's test audit, a feature's release delta, or when someone
  asks what should be tested. Triggers: "/test-plan", "plan the tests", "define the release
  criteria", "audit this project's tests".
---

# test-plan

Define **what must be proven**, not how development must proceed. The Test Contract may be written
before implementation or added to an existing project later, but its release criteria must be fixed
before `release-gate` executes.

Read the repository instructions and its `## harness-ship` Config v3 block first. Run `setup` only
when the block is absent or unsupported. Keep Config v3 policy-only; store test capabilities and
release criteria in the Test Contract instead of expanding project configuration.

## Two-layer Test Contract

Give the contract a stable ID and revision. It has two independently reviewable layers:

### Project Test Baseline

Record the reusable release expectations:

- product type, supported surfaces, and release target;
- P0/P1 user journeys with stable scenario IDs and externally observable expected and forbidden
  behaviour;
- the cheapest stable seam that can prove each journey or risk;
- method: `automated`, `manual`, `exploratory`, or `not-configured`;
- established command or exact manual steps, required evidence, environment, fixtures, permissions,
  and safe test-data rules;
- source-to-artifact provenance method and durable evidence location; and
- required, observe-only, and deferred checks, with reasons.

P0 covers core value, auth, money, destructive state changes, or a flow that must not regress.
Unknown capability is `not-configured`, never PASS.

### Release Delta

For one candidate, record:

- source range, release scope, and affected baseline scenarios;
- new or changed behaviour and risks;
- added scenarios or evidence requirements; and
- applicable migration, compatibility, security, performance, accessibility, recovery, or rollback
  checks. Mark an item not applicable only with a concrete reason.

Unchanged baseline content is referenced, not copied or re-approved.

## Greenfield project

Start with the product surface and first real risks. Do not install a framework, invent commands, or
create E2E infrastructure for an empty repository. A draft may honestly leave capabilities
`not-configured` until a testable slice exists. Add automation only when a real behaviour and seam
justify it.

## Existing project

Inspect before proposing change:

1. inventory the complete test tree, runners, CI jobs, deployment path, and artifact provenance;
2. identify current green, red, flaky, skipped, and missing capabilities;
3. map existing tests to user journeys and risks; and
4. preserve repository-native tools while classifying gates as required, observe-only, or deferred.

Do not replace a framework or duplicate coverage merely to make the project resemble a template.

## Approval and revision

Present the complete baseline plus release delta. Only the user may approve the Test Contract.
Until then label it `DRAFT`; `release-gate` must return `NO-GO`.

After approval, any semantic change to expected behaviour, priority, required evidence, test method,
or blocking status creates a new revision. Implementation details and equivalent seam corrections
do not. Preserve retired scenarios and IDs so old evidence remains interpretable.
