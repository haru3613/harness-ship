---
name: testing-workflow
description: >-
  QA a feature the way a user hits it — derive journeys, split ownership (RD: unit+contract; QA:
  integration+E2E), run tests on a test environment, gate against fake-green suites, and produce a
  plain-language acceptance report the user can sign off. Use after a dev→QA handoff or when someone
  says /testing-workflow, "QA this", "write e2e tests", "is this ready to ship?".
---

# testing-workflow

QA is the role closest to the user. Tests written from the **user's path through the product** catch
the bugs unit tests structurally can't. This workflow turns a dev→QA handoff into user-journey tests
and a report the user can actually read and accept.

## Ownership + pyramid (settle first — prevents duplication)

| Tier | Owner | What |
|---|---|---|
| Unit | **RD** | logic in isolation, at seams |
| Contract | **RD** | the API shape between front-end and back-end (from the API contract, if any) |
| Integration | **QA** | modules together, real wiring |
| E2E / journey | **QA** | the user's actual path — UI and/or app |

Keep the pyramid shape: **many unit, some integration, few E2E.** An E2E-heavy suite is slow and
flaky — reach for E2E only where a journey crosses the whole stack.

---

## Stage 1 — Journeys → scenarios (design only)

Derive journeys from the **acceptance criteria in the dev→QA handoff / ticket**, not from
imagination. Output **platform-neutral scenarios**, each tagged by surface — `[UI]` / `[APP]` /
`[API/contract]` — and written Given/When/Then plus a **negative** assertion (the "but it must NOT…").
**Stop at design here** — hand each scenario to its runner in the next stage. Produce a **P0/P1
matrix**: P0 = core value / money / auth / the flow that must never break (automate first); P1 =
important but degradable.

## Stage 2 — Route by ownership

- **RD tier** (may already be covered — check the handoff's "what unit+contract tests cover"): unit +
  contract tests. Test the contract against the API schema; don't re-test at E2E what a contract test
  already pins.
- **QA tier**: integration + E2E → Stage 3.

## Stage 3 — Execute E2E

Route by surface, using whatever runner fits the stack (web UI → a browser-automation runner such as
Playwright; native app → the platform's integration-test harness). Then:

- **Run against a test environment**, never production. Seed test data on staging/local only —
  **never write fake/seed data into a production database.**
- **Flaky → quarantine** (skip + a linked issue), never delete; add a retry policy so one flaky test
  can't red the whole run. Fix quarantined tests as their own tickets.
- **CI layering**: P0 journeys run on **every PR**; the full suite runs **nightly / pre-release**.
  E2E is too slow to run whole on every push.

## Stage 4 — Anti-fake-green gate

Before trusting any green, audit the suite for tests that *look* like coverage but assert nothing:

- **> 50% static assertions** (status-200 / element-exists / title-only, no operation or flow) → reject.
- **> 30% weak assertions** (no real assert, tautological, recomputes the expected value) → reject.
- **Console/runtime errors must be intercepted**, not ignored.
- "Verified only what's visible → marked PASS" → reject.

A green suite that fails this gate is worse than none — it manufactures false confidence.

## Stage 5 — Acceptance report

Produce a **plain-language report the user signs off on**, using `acceptance-report-template.md` in
this folder. It must:

- List each **user journey** with ✅ / ⚠️ / ❌, in the user's words (not test-function names).
- Map every result back to the **ticket's acceptance criteria** — "done" = the thing they asked for
  works, not "some tests passed".
- For failures, link the **evidence** (screenshot / video / trace) and say what the user would see.
- State coverage **honestly** — what's automated, what was checked manually, what was NOT tested.
- End with a one-line **verdict**: ready to accept / accept-with-caveats / not ready + why.

This report is dev-workflow's gate 4. Hand it to the user.

## Stage 6 — Bug loopback

Any confirmed failure → **`diagnose`** (red-capable repro first, then falsifiable hypotheses), then
file it back into `dev-workflow` as a new ticket with a regression test at the seam. Loop closed.
