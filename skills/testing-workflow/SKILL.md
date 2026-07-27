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

**Prerequisite:** require the project's `## harness-ship` block on a supported **Config version** in
`AGENTS.md` / `CLAUDE.md`; the plugin version is informational and never a gate. Its QA environment,
artifact-provenance source, QA evidence location, and tracker must be concrete and non-placeholder.
If the block is absent or on an unsupported Config version, run `setup` and stop before Stage 2.
Reconcile duplicate blocks directly; setup must not guess which one to replace. Configure
missing/placeholder/`not-configured` required QA fields here and stop until they are concrete.
Never guess or downgrade them. Do not reinterpret a legacy generic test command. Individual QA
command capabilities may remain `not-configured`; Stage 3 records those scenarios NOT TESTED rather
than inferring PASS.

## Ownership + pyramid (settle first — prevents duplication)

| Tier | Owner | What |
|---|---|---|
| Unit | **RD** | logic in isolation, at seams |
| Contract | **RD** | the API shape between front-end and back-end (from the API contract, if any) |
| Integration | **QA** | modules together, real wiring |
| E2E / journey | **QA** | the user's actual path — UI and/or app |

Keep the pyramid shape: **many unit, some integration, few E2E.** An E2E-heavy suite is slow and
flaky — reach for E2E only where a journey crosses the whole stack.

## Stage 2 — Route approved scenarios by ownership

Resume here only after the dev→QA handoff uses `qa-handoff-template.md`. Validate its handoff
status, approved contract revision and SC-ID → AC-ID scope, **full 40-character source SHA**,
**deployed artifact/environment revision**, **artifact-provenance source** and receipt,
**fixtures/accounts**, **known risks**, access path, and **RD coverage summary**. Do not redesign
scenarios to match what was built.

Any required field that is missing, still a placeholder, or mismatched makes the handoff **Not
ready**. Do not start Stage 3. In particular, the provenance receipt must bind the exact deployed
artifact to the full source SHA. Also validate that the configured **QA evidence location** is a
concrete, writable, durable destination available to the run; `not-configured` is Not ready.

- **RD coverage summary is informational only:** use it to **avoid duplicate testing**. QA does not
  audit the TDD cycle and does not execute unit or API-contract tests. Missing or red RD
  prerequisites return to RD; QA does not repair or rerun them.
- **QA tier:** execute only the approved integration + E2E/user-journey and risk-selected checks in
  Stage 3.

## Stage 3 — Execute QA scope

This stage is **QA execution only**. Use the configured QA commands and append every attempt to
`execution-ledger-template.md`. The approved QA scope is limited to:

- integration checks at real module/service boundaries;
- E2E / user journeys through the approved surface; and
- risk-selected manual, exploratory, or non-functional checks named by the approved assurance
  profile or handoff risks.

Route by surface and layer using the configured QA command (web UI → browser automation; native app
→ its journey/integration harness; service seam → the configured integration runner). A QA
capability is either an executable command, an explicit `manual: <steps + required evidence>`
method, or `not-configured`. A `not-configured` capability cannot run: record **NOT TESTED** and make
the result **Not ready**; never infer PASS from an unknown capability.

Run a fail-closed **QA execution ownership preflight** immediately before every trigger-capable QA
action. Re-read the current validated Config block, the capability's QA ownership, and the
current command, workflow, and job wiring; revalidate the handoff-bound source/artifact/provenance and evidence
destination. On configuration or ownership drift, an RD-owned/unclassified action, or a mismatch,
do not execute: append raw `NOT RUN` → `NOT TESTED` with preflight evidence.

- **Initial direct or manual execution:** run the preflight immediately, then start the configured
  QA command or approved manual steps.
- **CI workflow dispatch or job rerun:** run the preflight immediately, then dispatch or rerun only
  the positively classified QA job.
- **Retry execution:** rerun the preflight immediately, then retry the same handoff-bound QA action.
- **Scheduled regression execution:** after the timer launches, run the preflight as the **first
  in-job gate**, then execute only the still-current, positively classified, handoff-bound QA job.

Before each scenario, revalidate that the ledger's source SHA, exact artifact/environment revision,
and artifact provenance receipt still match the handoff, and that the configured **QA evidence
location** is still writable. Record the SC-ID, AC-ID, QA layer/risk probe, method/command or manual
steps, **raw attempt outcome**, **scenario classification**, and durable evidence for every attempt,
including PASS.

Then:

- **Run against a test environment**, never production. Seed test data on staging/local only —
  **never write fake/seed data into a production database.**
- A bounded retry appends its complete **attempt history**. Raw attempt outcomes are `PASS`, `FAIL`,
  `BLOCKED`, or `NOT RUN`. Apply the ledger template's **ordered first-match precedence**:
  latest `NOT RUN` → `NOT TESTED`; else latest `BLOCKED` → `BLOCKED`; else mixed raw `FAIL` +
  `PASS` → `FLAKY`; else latest `PASS` → `PASS`; else latest `FAIL` → `FAIL`.
- A raw `FAIL` followed by raw `PASS` for the same scenario and QA-RUN-ID is **retry-green**; the
  reverse order is also inconsistent. When neither a later `NOT RUN` nor `BLOCKED` takes precedence,
  the latest classification is **FLAKY**, never rewritten as PASS.
- A skipped, quarantined, unavailable, or `not-configured` attempt appends raw `NOT RUN` with the
  reason and evidence; by first-match precedence its latest scenario classification is **NOT
  TESTED**. Never omit it.
- For a **P0** journey, **every classification except PASS**—`FAIL`, `FLAKY`, `BLOCKED`, or `NOT
  TESTED`—forces the verdict **Not ready**. A skipped or quarantined P0 therefore cannot clear the
  gate and **must not count as PASS**; it cannot be quarantined to manufacture acceptance.
- A non-P0 flaky check may be quarantined only with a linked QA-maintenance ticket; its current
  result remains FLAKY or NOT TESTED rather than PASS.
- **QA layering**: P0 journeys run against **every valid handoff's QA candidate artifact**. The QA
  full suite runs for a pre-release candidate and may run as scheduled regression only while a
  current valid handoff still binds its source, artifact, environment, and provenance receipt. A
  **PR smoke gate**, when needed before handoff, is an **RD-owned** command and must not invoke a QA
  command. Never run QA P0/full-suite commands against an unhanded-off PR artifact.

## Stage 4 — Anti-fake-green gate

Before trusting any green, audit the executed QA checks — not RD's unit/API-contract suite — for
tests that *look* like coverage but assert nothing. Classifying an assertion needs judgement; the
threshold does not. **Write the judgement down per assertion and let the arithmetic be checked.**

Append an assertion audit to the execution ledger: state the denominator, then classify every
assertion in scope as `static`, `weak`, or `ok`, each with its location and — for anything not `ok` —
a reason. Then recompute the verdict:

```sh
python3 <plugin-root>/scripts/fake_green.py check --ledger <execution-ledger>
```

- **static** — status-200 / element-exists / title-only; asserts no operation or flow. Over **50%** → reject.
- **weak** — no real assert, tautological, or recomputes the expected value with the implementation's logic. Over **30%** → reject.
- **Console/runtime errors must be intercepted**, not ignored.
- "Verified only what's visible → marked PASS" → reject.

A missing, unenumerated, or miscounted audit exits non-zero and is itself a blocking result: an
unauditable verdict is not a verdict. A green suite that fails this gate is worse than none — it
manufactures false confidence.
For every affected scenario, append a new raw `BLOCKED` observation and `BLOCKED` scenario
classification to the execution ledger with the audit evidence. Preserve every earlier PASS and
attempt; never rewrite them. The verdict is **Not ready**. After the QA check is repaired, execute
it again and append a new attempt with new evidence before that scenario can return to PASS.

## Stage 5 — Acceptance report

Produce a **plain-language report the user signs off on**, using `acceptance-report-template.md` in
this folder and deriving every result from the append-only execution ledger. It must:

- List each **user journey** with ✅ / ⚠️ / ❌, in the user's words (not test-function names).
- Name the acceptance-contract revision and map every result through **SC-ID → AC-ID → ticket** —
  "done" = the thing they asked for works, not "some tests passed".
- For every result, link the ledger attempt, exact artifact, method/steps, and **evidence**
  (screenshot / video / trace / assertion); for failures, also say what the user would see.
- Preserve retry-green as **FLAKY** and enforce the P0 Not-ready rule.
- State coverage **honestly** — what's automated, what was checked manually, what was NOT tested.
- End with a one-line **verdict**: ready to accept / accept-with-caveats / not ready + why.

This report is dev-workflow's gate 5. Hand it to the user.

## Stage 6 — Bug loopback

For every QA **non-pass** (`FAIL`, `FLAKY`, `BLOCKED`, or `NOT TESTED`), run **`bug-workflow`** and
link the ledger evidence to one stable BUG-ID. Classify before routing: only a `product-defect`
enters **`diagnose`** for safe cause analysis and a Diagnosis Receipt. Test defects, environment
defects, spec ambiguities, duplicates, and known limitations follow their distinct Bug Case routes.
Handoffs and later retests append to the same Bug Case rather than replacing it.

## Stage 7 — Fixed-artifact Bug Case verification

Resume a classified product Bug Case only from a valid fixed-artifact addendum in
`qa-handoff-template.md`. Require the stable BUG-ID, numbered fix attempt, original failed artifact
and evidence, `diagnose` Diagnosis Receipt, `implement` defect receipt, exact new full source SHA,
exact new deployed artifact/environment revision, new deployment receipt, affected SC-IDs, and RD
verification summary.

If the new deployment evidence is missing or mismatched, do not execute QA: append a resumable
`blocked` observation to the same BUG-ID with the exact resume condition. Never infer a fixed
artifact from a green RD check.

After the fixed-artifact addendum passes **Stage 2** handoff validation, execute every recheck
through the existing **Stage 3** QA ownership preflight, per-scenario artifact/evidence
revalidation, and ordered first-match normalization. Then apply the **Stage 4** anti-fake-green
gate. The fixed-artifact section of the ledger indexes these canonical attempts; it does not create
a parallel result model. In particular, retry-green remains `FLAKY` and cannot become `verified`.

On the fixed artifact, QA reruns:

1. the **original observation**;
2. each **affected SC-ID journey**; and
3. a **proportionate neighbouring regression** scope selected from the approved risks.

This remains **QA execution only**. QA does not execute unit or API-contract tests, audit RD TDD, or
repair product code. Append a numbered fix attempt and retest attempt as a **QA verification
attempt** in `execution-ledger-template.md`; preserve the original failed-artifact evidence and
never overwrite any earlier attempt.

Disposition is evidence-bound:

- only QA can set `verified`, after every required scenario classification is `PASS` under Stages
  3–4;
- a repeated failure sets `reopened` and routes the same BUG-ID through `bug-workflow`;
- missing or mismatched deployment evidence sets resumable `blocked`; and
- accept-with-caveat requires an explicit human decision and a linked follow-up where applicable.

After disposition, regenerate the Stage 5 acceptance report so it compares the original failure and
fixed-artifact retest under the same contract trace and BUG-ID. Release promotion remains outside
`testing-workflow`.
