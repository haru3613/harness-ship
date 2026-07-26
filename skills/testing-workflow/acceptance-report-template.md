# Acceptance Report — <feature name>

> A report for the person accepting the work, not for engineers. Say what a user would see.
> Fill every section; if something wasn't tested, say so — silent gaps read as "covered".

**Feature:** <one line, user-facing>
**Ticket(s):** <IDs / links>
**Acceptance contract:** <spec-id/acceptance-vN>
**Source commit:** <full SHA>
**Tested artifact/environment:** <deployment or artifact revision + environment>
**Date:** <YYYY-MM-DD>

---

## Verdict

> One line, first — so the reader knows the answer before the detail.

**<✅ Ready to accept  |  ⚠️ Accept with caveats  |  ❌ Not ready>** — <why, in one sentence>

---

## Journeys

> Each row is something a user does, in their words. Result maps to the ticket's acceptance
> criteria. Record the approved profile and produced evidence for every scenario, including ✅.

| # | User journey | Scenario | Spec criterion | Ticket | QA assurance profile | Execution method / automation | Result | Required evidence | Exact PR HEAD | Expected target HEAD | Observed merge SHA/derivation | Pair-bound RD receipt | PR automation/CI evidence | Handed-off source/artifact revision | Independent QA evidence | Produced evidence | Risk-probe result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | <what the user does> | <SC-001> | <AC-1> | <ID> | <integration; probes…> | <runner / manual> | ✅ | <trace + assertion> | <SHA> | <target SHA> | <merge SHA + derivation> | <RD receipt> | <CI run / exception receipt> | <source SHA + artifact/environment revision> | [trace](…) | [all evidence](…) | <probe → result> |
| 2 | <…> | <SC-002> | <AC-2> | <ID> | <E2E; probes…> | <runner> | ✅ | <video + trace> | <SHA> | <target SHA> | <merge SHA + derivation> | <RD receipt> | <CI run> | <source/artifact revision> | [video](…) [trace](…) | [all evidence](…) | <probe → result> |
| 3 | <…> | <SC-003> | <AC-3> | <ID> | <integration; probes…> | <runner> | ⚠️ | <trace> | <SHA> | <target SHA> | <merge SHA + derivation> | <RD receipt> | <CI run / exception receipt> | <source/artifact revision> | [trace](…) | [all evidence](…) | <probe → caveat> |
| 4 | <…> | <SC-004> | <AC-4> | <ID> | <E2E; probes…> | <runner> | ❌ | <video + trace> | <SHA> | <target SHA> | <merge SHA + derivation> | <RD receipt> | <CI run> | <source/artifact revision> | [video](…) [trace](…) | [all evidence](…) | <probe → failure> |

**Legend:** ✅ works as intended · ⚠️ works with a caveat (below) · ❌ broken

## Manual P0 exceptions

> Include one row for every manual P0 exception. Use `none` only when the approved contract has no
> manual P0 exception.

| Scenario | Exception approval | Exception ticket | Approved exception owner principal ID | Approved exception owner display label | Approved QA automation owner principal ID | Approved QA automation owner display label | Live ticket assignee principal ID | Live ticket assignee display label | Owner match | Exception expiry | Exception execution method | Exception required evidence | Exception produced evidence | Exception validated at | Exception evaluation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <SC-001 / none> | <user approval record> | <open ticket link> | <provider ID> | <label> | <provider ID> | <label> | <provider ID> | <label> | <all IDs match / mismatch> | <deadline> | <exact-candidate method> | <required artifact/trace> | <produced artifact/trace> | <timestamp> | <valid / incomplete / closed / expired / owner mismatch> |

## What failed / caveats

> For each ⚠️ / ❌: what the **user** would experience, not the stack trace.

- **#3 (⚠️):** <plain-language caveat> → follow-up ticket <ID?>
- **#4 (❌):** <what breaks for the user> → **blocking**, ticket <ID>

## Coverage — what was and wasn't tested

> Honesty here is the whole point. No silent gaps.

- **Automated (regression-safe):** <which journeys>
- **Manual only (not yet automated):** <which — automate as ticket …>
- **NOT tested:** <what, and why>
- **Test data:** <seeded where; accounts / fixtures used>

## Sign-off

- [ ] Only the user accepts the ✅ journeys as done.
- [ ] Caveats (⚠️) are acknowledged and ticketed.
- [ ] Blocking failures (❌) return to dev-workflow before release.

Automation cannot sign this gate.

Accepted by (user): __________   Date: __________
