# Acceptance Report — <feature name>

> A report for the person accepting the work, not for engineers. Say what a user would see.
> Fill every section; if something wasn't tested, say so — silent gaps read as "covered".

**Feature:** <one line, user-facing>
**Ticket(s):** <IDs / links>
**Tested on:** <test env / commit>
**Date:** <YYYY-MM-DD>

---

## Verdict

> One line, first — so the reader knows the answer before the detail.

**<✅ Ready to accept  |  ⚠️ Accept with caveats  |  ❌ Not ready>** — <why, in one sentence>

---

## Journeys

> Each row is something a user does, in their words. Result maps to the ticket's acceptance
> criteria. Evidence links open a screenshot / video / trace for anything not ✅.

| # | User journey | Acceptance criterion it proves | Result | Evidence |
|---|---|---|---|---|
| 1 | <what the user does> | <AC-1> | ✅ | — |
| 2 | <…> | <AC-2> | ✅ | — |
| 3 | <…> | <AC-3> | ⚠️ | [video](…) |
| 4 | <…> | <AC-4> | ❌ | [trace](…) |

**Legend:** ✅ works as intended · ⚠️ works with a caveat (below) · ❌ broken

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

- [ ] Reviewer accepts the ✅ journeys as done.
- [ ] Caveats (⚠️) are acknowledged and ticketed.
- [ ] Blocking failures (❌) return to dev-workflow before release.

Accepted by: __________   Date: __________
