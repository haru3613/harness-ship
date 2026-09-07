---
name: test-plan
description: >-
  Plan risk-based verification for a task or release, or create an optional reusable Test Contract
  when the user wants one. Use when asked to plan tests or define release criteria.
---

# test-plan

Produce the smallest useful plan from the current task, user decisions, repository policy, and
existing tests. Planning is optional before testing and release assessment. A Test Contract is an
opt-in planning document, not a prerequisite for either workflow.

## Inspect the relevant surface

Identify changed user behaviour, dependencies, core regressions, and plausible failure modes.
Read the relevant tests, runners, CI, and defect history. Follow recurring mechanisms into nearby
callers where a fix may have missed a sibling. Broaden inspection only when it changes the plan.
For a new project, start with its first real behaviour rather than inventing a testing stack.

Use existing issue criteria and project-native checklists directly. An old contract may supply
context; separate still-applicable standing requirements from old release-specific choices.
Do not create a pointer document merely to make existing criteria acceptable to another skill.

## Select verification

For each material risk, name the observable expected result, what must not happen, the cheapest
stable check, and the environment needed. Reuse existing tests; add coverage only for a concrete gap.
Read [scenario-craft.md](scenario-craft.md) when a complex journey needs clearer boundaries or
negative assertions. A small change can use a few bullets instead of a scenario table.

Keep core regression and explicit project checks. Select extra device, provider, migration,
security, recovery, or other checks from current risks. Explain reuse of valid unchanged-code
evidence and its limits. Do not require historical release checklists wholesale.

Ask only about missing decisions that materially change expected behaviour, risk acceptance, or
safe execution. Use answers already given. Complete independently useful planning and checks while
waiting; an unattended session can record assumptions and open decisions without inventing approval.
Unknown expected behaviour remains an open question, not an assertion copied from implementation.

## Deliver the plan

Default to a short plan in the current conversation or existing PR/issue, following write
authorization. State selected checks, existing coverage, genuine gaps, and decisions still needed.
Routine verification choices within authorized scope do not need a separate approval round.

When the user explicitly wants a reusable Test Contract, use
[test-contract-template.md](test-contract-template.md). Keep it at the user-chosen location; the
legacy `.harness-ship/test-contract.md` and `.harness-ship/test-contract.draft.md` paths remain
supported. Preserve existing approved content while drafting. Identify approval and revision only
when maintaining that opted-in contract; draft text must not masquerade as an approved requirement.
Reference existing criteria rather than duplicating them. Contract maintenance never blocks testing
or evidence-based release assessment by itself.
