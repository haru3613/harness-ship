---
name: testing-workflow
description: >-
  Execute an approved acceptance contract after the dev handoff — split ownership (RD:
  unit+contract; QA: integration+E2E), run tests on a test environment, gate against fake-green
  suites, and produce a plain-language acceptance report the user can sign off. Use after a dev→QA
  handoff, or when someone says /testing-workflow, "QA this", "write e2e tests", or "is this ready
  to ship?".
---

# testing-workflow

QA is the role closest to the user. Tests written from the **user's path through the product** catch
the bugs unit tests structurally can't. This workflow executes the **approved acceptance contract**
after the dev→QA handoff and produces a report the user can actually read and accept. Scenario
ownership belongs to `acceptance-design`; this workflow must not author or redesign those scenarios.

**Prerequisite:** read the project's `## harness-ship` config (test env, test/lint commands, tracker)
in `AGENTS.md` / `CLAUDE.md`; run `setup` if it is absent.

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

## v0.6 compatibility redirect

For one minor release, v0.6, redirect either legacy entry state to **`acceptance-design`**:

- a pre-implementation `testing-workflow` call; or
- a call where implementation already exists but there is no approved acceptance contract.

Use the original or current stable spec and never infer expected behaviour from code. Stop when
`acceptance-design` reaches its approval gate. Do not begin QA execution, route tests, or continue
to Stage 2. This redirect expires after one minor release; new workflow guidance should call
`acceptance-design` directly.

## Stage 2 — Route approved scenarios by ownership

Resume here only after the dev→QA handoff. Confirm the handoff names the approved scenario set and
the exact source commit and deployed artifact/environment revision under test; do not redesign
scenarios to match what was built.

Require the handoff's **expected target HEAD**, **observed merge SHA**, **merge derivation**,
**pair-bound RD receipt**, and **pair-bound P0 receipt**. Each receipt must name the same exact PR
HEAD/target HEAD pair that produced the observed merge and handed-off artifact. A **mismatched or
unrelated** receipt makes the handoff **Not ready**.

Owner records use an **immutable provider principal ID** plus a human-readable **display label**.
Compare principal IDs; labels are informational and may change.

For every scenario, read its approved **QA assurance profile** and execute each approved profile
unchanged: preserve its integration/E2E layer, automation expectation, required evidence, and
risk-specific probes. If the profile is missing, contradictory, or cannot be executed at the named
artifact seam, return to `acceptance-design`; QA must not silently redesign it during execution.

For every manual P0 exception, validate its **current explicit user approval**, that the
**follow-up ticket exists and is open**, its **named owner**, its **unexpired deadline**, the
**exact-candidate execution method**, and the **required evidence**; verify the **live
follow-up-ticket assignee equals the approved QA automation owner** copied unchanged from the
approved contract and the **approved exception owner equals the approved QA automation owner**.
Any incomplete, closed, expired, or **owner mismatch** makes the handoff **Not ready**: do not
execute it, and return to `acceptance-design` through `dev-workflow` Stage 3 for a revised approved
contract. Preserve all six fields, all three owner values, and this evaluation in the acceptance
report.

- **RD tier is a handoff prerequisite:** verify the RD unit/contract receipt and its exact-HEAD
  results. If RD coverage is missing or red, return to RD; QA does not write or execute those tests.
- **QA tier:** QA executes only the approved integration + E2E profiles in Stage 3.

## Stage 3 — Execute approved QA layer

Route by the approved QA assurance profile:

- **Integration profile:** execute at its named seam with the stack's integration harness and real
  module/service wiring.
- **E2E / journey profile:** route by surface through a journey runner (web UI → browser automation
  such as Playwright; native app → the platform's journey/integration-test harness).

Do not escalate an integration profile to E2E or replace an E2E journey with a narrower integration
check. Resolve the prerequisite and exact-artifact run through one branch:

- **Without a manual exception:** require exact-PR-HEAD automation evidence for the approved
  profile, then independently execute it against the **exact handed-off artifact**. PR evidence is
  a prerequisite, not a substitute for this QA run.
- **With an approved manual exception:** require a **fresh six-field-and-owner-match exception
  receipt**. Revalidate its **current explicit user approval**, that the **follow-up ticket exists
  and is open**, its **named owner**, its **unexpired deadline**, the **exact-candidate execution
  method**, the **required evidence**, and that the **live follow-up-ticket assignee equals the
  approved QA automation owner**; also verify the **approved exception owner equals the approved QA
  automation owner**. Any invalid field or **owner mismatch** is **Not ready** and returns through
  `dev-workflow` Stage 3. If valid, execute the **manual exact-candidate method** against the **exact
  handed-off artifact** and attach the produced evidence.

Then:

- **Run against a test environment**, never production. Seed test data on staging/local only —
  **never write fake/seed data into a production database.**
- **Flaky quarantine is non-P0 only** (skip + a linked issue), never delete; add a retry policy so
  one flaky non-P0 test cannot red the whole run. A **P0 flaky** result is **Not ready** and must not
  be skipped: return through `dev-workflow` Stage 3 if the user chooses to approve a complete manual
  P0 exception; otherwise fix and rerun it. Fix quarantined non-P0 tests as their own tickets.
- **CI layering**: automated P0 profiles run on every PR; the full suite runs **nightly /
  pre-release**. A user-approved manual P0 exception must run against the exact candidate artifact
  and attach its required evidence; it cannot produce **Ready to accept**, only **Accept with
  caveats** at best, until the follow-up automation ticket closes. Never infer PASS from absent CI.
  E2E is too slow to run whole on every push.

## Stage 4 — Anti-fake-green gate

Before trusting any green, audit the suite for tests that *look* like coverage but assert nothing:

- **> 50% static assertions** (status-200 / element-exists / title-only, no operation or flow) → reject.
- **> 30% weak assertions** (no real assert, tautological, recomputes the expected value) → reject.
- **Console/runtime errors must be intercepted**, not ignored.
- "Verified only what's visible → marked PASS" → reject.

A green suite that fails this gate is worse than none — it manufactures false confidence.

## Stage 5 — Acceptance report

Immediately before generating the report and verdict for any manual P0 exception, revalidate its
**current explicit user approval**, that the **follow-up ticket exists and is open**, its
**named owner**, its **unexpired deadline**, the **exact-candidate execution method**, the
**required evidence**, and that the **live follow-up-ticket assignee equals the approved QA
automation owner**; also verify the **approved exception owner equals the approved QA automation
owner**. Record the validation timestamp, all owner values, and both owner-match results. Any invalid
field or **owner mismatch** makes the result **Not ready** and returns through `dev-workflow`
Stage 3; a prior Stage 2/3 validation is not reusable.

Produce a **plain-language report the user signs off on**, using `acceptance-report-template.md` in
this folder. It must:

- List each **user journey** with ✅ / ⚠️ / ❌, in the user's words (not test-function names).
- Name the acceptance-contract revision and map every result through **SC-ID → AC-ID → ticket** —
  "done" = the thing they asked for works, not "some tests passed".
- For failures, link the **evidence** (screenshot / video / trace) and say what the user would see.
- Report the profile and evidence for every scenario, including the method/evidence required by its
  approved QA assurance profile—not only failures.
- State coverage **honestly** — what's automated, what was checked manually, what was NOT tested.
- End with a one-line **verdict**: ready to accept / accept-with-caveats / not ready + why.

This report is dev-workflow's gate 5. Hand it to the user.

## Stage 6 — Bug loopback

Any confirmed failure → **`diagnose`** (red-capable repro first, then falsifiable hypotheses), then
file it back into `dev-workflow` as a new ticket with a regression test at the seam. Loop closed.
