# Upgrade guide

Choose one channel, upgrade its marketplace source, install the refreshed plugin, restart or reload
the real host process, and start a new session. Re-run setup only when the installed release does
not support the project's Config version.

`harness-ship` is the stable channel pinned to the release tag recorded in the marketplace catalog;
`harness-ship-next` is an explicit unreleased channel pinned to `main`. Both resolve to the same
underlying plugin namespace and are mutually exclusive. Remove the installed channel before
switching. A local editable checkout is a development source and does not receive managed upgrades
or prove the tagged release.
The marketplace catalog is added or refreshed from `main`; only its stable plugin entry is pinned
to the release tag. This lets a catalog refresh discover a future stable patch without silently
moving the already published stable source.

## Practical testing without a contract gate

Test Contract approval and fixed candidate files are no longer prerequisites for testing or release
assessment. Config stays v3; **do not rerun setup**. Existing records remain usable in place.

Use current task scope, explicit project requirements, and real risks to choose checks. Keep one
summary in the existing PR/issue or chosen location with candidate/environment, commands/results,
evidence links, and remaining risks. Do not create or refresh old contracts solely to unblock a run.
A historical release-specific checklist does not automatically govern the next release.

Projects explicitly maintaining a reusable contract can continue doing so. Preserve their current
requirements and approval decisions. Optional templates remain available, but integrations that
expect mandatory handoff/ledger/report files must opt into keeping those records or consume the
chosen summary instead. Comment consumers should no longer assume a separate canonical file set.

A missing sensitivity receipt does not downgrade existing automation; evaluate meaningful assertion
quality when writing or changing tests. Routine non-passes no longer require Bug Cases. Keep durable
tracking for unresolved defects, recurrence, or handoff, and preserve original failures and retests.
Real failures, identity mismatches, and unverified material risks remain visible in release verdicts.

## Test and release confidence migration

Releases with the test-and-release-confidence surface remove mandatory development orchestration
and keep Config v3.

- Replace `dev-workflow` with the independent command needed now: `advise`, `test-plan`,
  `exploratory-testing`, `testing-workflow`, or `release-gate`.
- Replace `acceptance-design` with `test-plan`. Existing acceptance criteria can become the first
  Release Delta; reusable P0 journeys become the Project Test Baseline.
- Bug Cases stop at a repair handoff. Remove automation that expects
  `bug-workflow → implement → tdd`; return a new exact candidate to `testing-workflow` instead.
- The seven development helpers — `clarify`, `spike`, `spec`, `tickets`, `implement`, `tdd`,
  `review` — are gone. They are not aliases and not opt-ins. Type those commands after upgrade
  and the host finds no skill. Use the repository's own development stack.
- Replace links to `qa-handoff-template.md` and `acceptance-report-template.md` with
  `candidate-handoff-template.md` and `test-report-template.md`.

Existing Config v3 projects **do not rerun setup**. After upgrade, run `advise` for the next
cuts. Use current scope and available evidence when invoking `release-gate`.

## Setup skill is now `hs-setup`

The published skill id is `hs-setup`. Invoke `/harness-ship:hs-setup` or `$harness-ship:hs-setup`.
Bare `/setup` is not a Harness Ship command. A host looking up `setup` finds no Harness Ship skill
by that id.

This is not a Config version change. Existing Config v3 projects do not rerun `hs-setup` solely
because of the rename. After upgrade, run `advise` for the next cuts.

## Test-engineer watch is first-run only

First-run `hs-setup` now also writes `## harness-ship-watch` standing rules into `AGENTS.md` or
`CLAUDE.md`, copies `.harness-ship/watch/detect.py`, and merges project-scoped hooks for Claude
Code, Codex, and Grok Build. The detector is zero-LLM and fail-open. Grok `SessionEnd` is unused.

Existing Config v3 blocks without **Test engineer watch** stay off. Do not rerun `hs-setup` to
pick this up unless the user explicitly asks to enable watch. Config version remains `3`.

## Advise is now the default job

After `hs-setup`, or when someone asks what to test, which framework to add, or whether
coverage is enough, run `advise`. It overwrites `.harness-ship/quality-report.md`
with the suite's shape and at most three next cuts. Existing Test Contracts,
candidate ledgers, and Config v3 are unchanged. `test-plan` offers optional planning; `release-gate` assesses current scope and evidence without a
mandatory contract.

## Codex

```sh
codex plugin marketplace add haru3613/harness-ship --ref main
codex plugin marketplace upgrade harness-ship
codex plugin add harness-ship@harness-ship
```

Start a new Codex session before running `$harness-ship:hs-setup`.

To opt in to unreleased next source after removing or deactivating stable:

```sh
codex plugin marketplace add haru3613/harness-ship --ref main
codex plugin add harness-ship-next@harness-ship
```

**After v2.0.0:** the generic readiness command is gone. Each workflow now resolves missing
test, QA, UI, and data-mutation capabilities only when an actual task needs them. Existing
Config v3 blocks remain valid and do not need setup again.

**Which upgrades need a re-run of setup:** only a **Config version** change. The plugin version in
the block records what wrote it and is never a gate, so a patch or compatible minor release leaves
every configured project working. Workflow preflight fails with an actionable message when the
schema is one this release does not support.

**v1.0.0 migration (breaking):** Config version 2 → 3, and the verifier binding format changed.
The 13-column host binding table, the `Verifier binding-contract version` field, and the
discovery-receipt input are gone. Re-run setup once per configured project to regenerate the
`## harness-ship` block without a verifier binding and stamp `Config version: 3`. Nothing else in
the block changes, and no automatic migration is attempted — the machinery that migrated the old
table was removed along with
the digest chain it existed to preserve, and reconstructing it would cost more than re-running
setup.

A project still carrying the old table fails closed on its `Config version`, which is the intended
detection.

**v0.7.0 migration (historical):** setup proposed Config v1 → v2 without writing it, and applied
the proposal only after an exact confirmation of the reviewed diff. That two-phase planner was
removed in v1.0.0; a block on an unsupported Config version is now regenerated, not migrated.

**v0.6.4 migration (historical):** that release required a configured live verifier. Current
versions do not; do not create or repair a profile when upgrading now.

**v0.6.3 migration (historical):** Config v1 projects ran `$harness-ship:setup` to reconcile the
legacy binding row. That profile-selection flow was removed in v1.0.0.

**v0.5.0 migration (historical):** setup began recording host role profiles; current versions do
not.

## Claude Code

```sh
claude plugin marketplace add haru3613/harness-ship@main
claude plugin marketplace update harness-ship
claude plugin update harness-ship@harness-ship
```

Restart Claude Code before running `/harness-ship:hs-setup`.

To opt in to unreleased next source after uninstalling stable:

```sh
claude plugin marketplace add haru3613/harness-ship@main
claude plugin install harness-ship-next@harness-ship
```

**v1.0.0 migration (breaking):** Config version 2 → 3, and the verifier binding format changed.
The 13-column host binding table, the `Verifier binding-contract version` field, and the
discovery-receipt input are gone. Re-run setup once per configured project to regenerate the
`## harness-ship` block without a verifier binding and stamp `Config version: 3`. No automatic
migration is attempted. A project still carrying the old table fails closed on its
`Config version`, which is the intended detection.

**v0.7.0 migration (historical):** setup proposed Config v1 → v2 without writing it, and applied
the proposal only after an exact confirmation of the reviewed diff. That two-phase planner was
removed in v1.0.0; a block on an unsupported Config version is now regenerated, not migrated.

**v0.6.4 migration (historical):** that release required a configured live verifier. Current
versions do not; do not create or repair a profile when upgrading now.

**v0.6.3 migration (historical):** Config v1 projects ran `/harness-ship:setup` to reconcile the
legacy binding row. That profile-selection flow was removed in v1.0.0.

**v0.5.0 migration (historical):** setup began recording host role profiles; current versions do
not.

## Editable local development

Run Python and lifecycle contracts directly in an editable checkout, or use the host's temporary
local plugin-directory facility for attended testing. Do not register or alter global plugin state
as part of repository validation. Local source changes are immediate, so restart/reload the
consumer after each source change; managed marketplace upgrade commands do not update a checkout.

## Projects on an earlier Config version

A block whose `Config version` is not the one this release supports is a zero-mutation stop, not an
automatic migration. Re-run setup once to regenerate it. Resolve test capabilities and release criteria from the task and repository policy rather than
Config; unavailable capabilities remain explicit gaps.

Harness Ship updates only the single `## harness-ship` block. It does not replace global agents or
settings.
