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

For every scenario, read its approved **QA assurance profile** and execute each approved profile
unchanged: preserve its integration/E2E layer, automation expectation, required evidence, and
risk-specific probes. If the profile is missing, contradictory, or cannot be executed at the named
artifact seam, return to `acceptance-design`; QA must not silently redesign it during execution.

For every manual P0 exception, validate its **current explicit user approval**, that the
**follow-up ticket exists and is open**, its **named owner**, its **unexpired deadline**, the
**exact-candidate execution method**, and the **required evidence**. Any incomplete, closed, or
expired exception makes the handoff **Not ready**: do not execute it, and return to
`acceptance-design` through `dev-workflow` Stage 3 for a revised approved contract. Preserve all six
fields and this evaluation in the acceptance report.

- **RD tier** (may already be covered — check the handoff's "what unit+contract tests cover"): unit +
  contract tests. Test the contract against the API schema; don't re-test at E2E what a contract test
  already pins.
- **QA tier**: integration + E2E → Stage 3, routed by the approved profile layer.

## Stage 3 — Execute approved QA layer

Route by the approved QA assurance profile:

- **Integration profile:** execute at its named seam with the stack's integration harness and real
  module/service wiring.
- **E2E / journey profile:** route by surface through a journey runner (web UI → browser automation
  such as Playwright; native app → the platform's journey/integration-test harness).

Do not escalate an integration profile to E2E or replace an E2E journey with a narrower integration
check. Then:

- **Independently execute the exact handed-off artifact.** Pre-merge automation evidence on the
  implementation PR is a prerequisite, not a substitute for QA rerunning the approved profile
  against the exact source and artifact/environment revision named in the handoff.
- Before running a manual P0 exception, freshly validate its **current explicit user approval**,
  that the **follow-up ticket exists and is open**, its **named owner**, its **unexpired deadline**,
  the **exact-candidate execution method**, and the **required evidence**. Any invalid field is
  **Not ready** and returns through `dev-workflow` Stage 3.
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
