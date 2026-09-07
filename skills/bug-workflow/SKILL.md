---
name: bug-workflow
description: >-
  Triage a finding that needs tracking, investigation, or handoff. Preserve expected/actual
  behaviour, evidence, and repair/retest conditions in the existing issue or chosen record.
---

# bug-workflow

Classify the finding before choosing a repair. A routine failure fixed and retested within the
current authorized task can stay in its test summary. NOT TESTED and unavailable infrastructure
are gaps, not automatically new bugs. Create a durable case when unresolved work, recurrence, or
cross-session handoff warrants it.

## Record and classify

Read the observation or test summary directly; no contract, scenario ID, handoff, or ledger is
required. Preserve expected/actual behaviour, reproduction steps, source/build/environment,
relevant permissions, and evidence. State unknown provenance rather than inventing it.

Distinguish product defect, test defect, environment problem, ambiguous expectation, duplicate,
and known limitation. Diagnose product defects when the cause remains uncertain; use `diagnose`
for substantial investigation. Fix routine test/environment problems within authorization and
rerun affected checks. Ask about ambiguous expectations only when the answer changes the fix.

## Track only what needs tracking

Use the existing issue or user-chosen record as the single home. Reuse its ID and preserve the
original failure when adding investigation or retest results. The optional
[bug-case-template.md](bug-case-template.md) and legacy `.harness-ship/bugs/<BUG-ID>.md` remain
available for teams that use them; a local mirror of a tracker issue is not mandatory.

Publish or update tracker records only with user authorization. Otherwise return the finding and
next action in the session. Report publication failure separately from the product finding.

## Repair and verify

State the cause if known, affected paths, expected fix, and cheapest meaningful retest. Continue
already-authorized repair through the host's development workflow; a handoff is needed only when
another owner or session must take over. Unresolved findings carry the blocker and resume condition.

Retest the actual repaired source/build, including relevant sibling paths. Record both original
failure and repaired result. A code change or green unrelated suite does not verify the defect.
Known limitations remain visible; never invent user acceptance or close an unverified finding.
