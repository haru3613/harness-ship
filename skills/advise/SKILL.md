---
name: advise
description: >-
  Diagnose a project's test gaps and name the cheapest next tests. Use after
  hs-setup, after plugin install, or when someone asks what to test, which
  framework to add, whether coverage is enough, or to audit the test suite.
  Triggers: "/advise", "what should we test", "which test framework",
  "is coverage enough", "audit this project's tests", "quality report".
---

# advise

Speak as a senior test engineer. Inspect the repository, then name at most three
**next cuts**. Write `.harness-ship/quality-report.md` from
[quality-report-template.md](quality-report-template.md). This skill does not
draft a Test Contract, install a tool, or return a release verdict.

Read repository instructions and the `## harness-ship` Config v3 block first.
Run `hs-setup` only when the block is absent or unsupported.

## 1 — Inventory

Collect what the project already has:

- product surface and the journeys a user can finish;
- the complete test tree, runners, and CI jobs, including path-gated no-ops;
- red, flaky, skipped, and empty suites, each named;
- defect history that clusters by failure mechanism, not by file; and
- any existing `.harness-ship/test-contract.md` or `.harness-ship/quality-report.md`.

An empty repository is a valid inventory: no runner, no CI, no journeys yet.
Stop inventory when another file would not change the next cut.

## 2 — Diagnose the portfolio

Name the **shape** from the inventory:

- **pyramid** — many fast narrow tests, a few integration seams, almost no UI E2E;
- **ice-cream** — most confidence sits in slow UI or device tests;
- **hourglass** — unit and E2E exist, the wiring in the middle does not;
- **empty** — no automated proof of user-visible behaviour;
- **thin-middle** — parsers or widgets are green, the content script, handler, or
  client that joins them is unproven.

Use coverage as a **flashlight**: list risky modules or journeys the suite never
touches. A percentage is not a target and not a gate.

A test that cannot fail for the reason a user would care about does not pay rent.
Record it as shape, not as proof.

## 3 — Speak the next cuts

Name at most three cuts, cheapest first. Each cut states:

- the distinct failure a user would feel;
- the cheapest stable seam that can catch it;
- the nearest existing test and why its assertions miss that failure; and
- a framework only when that seam has no runner.

The first cut on an empty repository is the first real behaviour's cheapest test,
not a stack. A hotfix that touches one contract field is one focused cut, not a
release baseline.

Present the list. Wait for approval before installing anything or writing test
code. If the user wants the tests written, hand to `exploratory-testing`. If they
want approved release criteria, hand to `test-plan`. If they want a GO/NO-GO,
hand to `release-gate` only after a contract and candidate evidence exist.

## 4 — Write the report

Overwrite `.harness-ship/quality-report.md` with the inventory's shape, the
flashlight findings, and the three cuts. The file is the latest diagnosis, not a
ledger. Commit it with the code it describes when the user wants it kept.

Done when the report names a shape, the flashlight findings, and at most three
cuts a later session can act on without re-deriving the inventory.
