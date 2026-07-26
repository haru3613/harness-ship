# Acceptance Report — <feature name>

> A report for the person accepting the work, not for engineers. Say what a user would see.
> Fill every section; if something wasn't tested, say so — silent gaps read as "covered".

**Feature:** <one line, user-facing>
**Ticket(s):** <IDs / links>
**Acceptance contract:** <spec-id/acceptance-vN>
**QA-RUN-ID:** <execution ledger run>
**Source commit:** <full 40-character SHA>
**Tested artifact/environment:** <exact artifact/environment revision>
**Artifact provenance:** <source + receipt link>
**Date:** <YYYY-MM-DD>

---

## Verdict

> One line, first — so the reader knows the answer before the detail.

**<✅ Ready to accept  |  🟡 Accept with caveats  |  ❌ Not ready>** — <why, in one sentence>

---

## Journeys

> Each row is something a user does, in their words. It records the exact artifact and links the
> append-only ledger attempt and durable evidence, including for PASS.

| # | User journey | Scenario | Spec criterion | Ticket | Exact artifact/environment revision | QA layer / risk probe | Method/command or manual steps | Result | Caveat / acceptance disposition | Ledger attempt | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | <what the user does> | <SC-001> | <AC-1> | <ID> | <artifact/env> | <integration> | `<command>` | ✅ PASS | <none> | <run/attempt> | [assertion + log](…) |
| 2 | <…> | <SC-002> | <AC-2> | <ID> | <artifact/env> | <E2E> | `<command>` | ⚠️ FLAKY | <not accepted / follow-up ticket> | <run/attempts> | [video + attempts](…) |
| 3 | <…> | <SC-003> | <AC-3> | <ID> | <artifact/env> | <exploratory> | <manual steps> | ✅ PASS | <accepted caveat + ticket> | <run/attempt> | [notes](…) |
| 4 | <…> | <SC-004> | <AC-4> | <ID> | <artifact/env> | <non-functional> | <method> | ❌ NOT TESTED | <blocking gap> | <run/attempt> | [trace](…) |

**Result legend:** ✅ PASS · ⚠️ FLAKY · ❌ FAIL / BLOCKED / NOT TESTED. Keep caveats and
acceptance disposition separate so the Result remains exactly derived from the ledger.

## What failed / caveats

> For each Caveat, ⚠️ FLAKY, or ❌ result: what the **user** would experience, not the stack trace.

- **#2 (FLAKY):** <plain-language retry instability> → QA-maintenance ticket <ID>
- **#3 (Caveat):** <plain-language caveat> → follow-up ticket <ID?>
- **#4 (❌):** <what breaks for the user> → **blocking**, ticket <ID>

## Coverage — what was and wasn't tested

> Honesty here is the whole point. No silent gaps.

- **Automated (regression-safe):** <which journeys>
- **Manual only (not yet automated):** <which — automate as ticket …>
- **Exploratory / non-functional:** <risk-selected checks and outcomes>
- **NOT tested:** <what, and why>
- **Test data:** <seeded where; accounts / fixtures used>

## Sign-off

- [ ] Only the user accepts the ✅ journeys as done.
- [ ] Caveats are acknowledged and ticketed.
- [ ] Blocking failures (❌) return to dev-workflow before release.

Accepted by (user): __________   Date: __________
