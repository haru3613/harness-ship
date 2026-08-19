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

## Records move into the repository

Records used to be "portable" — a filled template with no home, which in practice meant it lived in
the conversation that produced it. They now have fixed paths under `.harness-ship/`, committed with
the code. Config stays v3; **do not rerun setup**.

```text
.harness-ship/
  quality-report.md             # latest diagnosis: shape, flashlight, next cuts
  test-contract.md              # the approved Project Test Baseline + Release Delta
  test-contract.draft.md        # a revision in progress, until the user approves it
  bugs/<BUG-ID>.md              # Bug Case, with each Diagnosis Receipt appended
  candidates/<short-sha>/       # handoff.md, ledger.md, report.md
```

To migrate a project already using Harness Ship:

- Move the current approved Test Contract into `.harness-ship/test-contract.md`, keeping its
  contract ID, revision number, and `APPROVED` header. Approval does not need to be re-obtained; an
  unchanged contract that only moved is the same revision.
- If a revision was mid-review when you upgraded, put it at `.harness-ship/test-contract.draft.md`
  instead. The approved file must never carry a `DRAFT` header — `release-gate` gates against it,
  and a draft parked there would block every candidate the approved revision still covers.
- Move open Bug Cases to `.harness-ship/bugs/<BUG-ID>.md`, keeping each stable BUG-ID as the
  filename, and append their existing Diagnosis Receipts to the same file in attempt order.
- Leave closed candidates where they are. Backfilling `.harness-ship/candidates/` for releases that
  already shipped proves nothing; the next candidate `testing-workflow` runs writes its own.
- Where a tracker holds this work, keep it. The tracker holds the discussion, the repository holds
  the evidence — the file carries the durable link to its tracker item.

Until the contract is at its path, `release-gate` returns `NO-GO` with the reason that the project
has no contract to gate against. That is the intended behaviour, not a regression: a verdict the
session cannot re-derive from the repository is not a verdict.

## P0 rows now cite what showed their test can fail

A P0 scenario is classified `automated` once something has shown its test failing for the reason the
row names — a RED watched fail, or the one-line break `exploratory-testing` injects on a local
working copy where no RED was available. The row's `Reason` cites it.

**Existing contracts are not downgraded.** The rule binds on coverage added or changed from here; a
P0 row already approved `automated` keeps its classification until a revision touches it, and is
backfilled then. Nothing to do at upgrade time.

New P0 coverage is a different matter, and deliberately so: a P0 row added from here is
`not-configured` until the receipt exists, which blocks a gate. `exploratory-testing` produces the
receipt when it writes the coverage, so schedule that cycle when the coverage is written rather
than meeting the block at gate time.

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
cuts. Approve a Test Contract before invoking `release-gate`.

## Advise is now the default job

After setup, or when someone asks what to test, which framework to add, or whether
coverage is enough, run `advise`. It overwrites `.harness-ship/quality-report.md`
with the suite's shape and at most three next cuts. Existing Test Contracts,
candidate ledgers, and Config v3 are unchanged. `test-plan` still owns approved
release criteria; `release-gate` remains optional and still needs that contract.

## Codex

```sh
codex plugin marketplace add haru3613/harness-ship --ref main
codex plugin marketplace upgrade harness-ship
codex plugin add harness-ship@harness-ship
```

Start a new Codex session before running `$harness-ship:setup`.

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

Restart Claude Code before running `/harness-ship:setup`.

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
automatic migration. Re-run setup once to regenerate it. Test capabilities and release criteria
belong in the Test Contract rather than Config; unavailable capabilities remain `not-configured`.

Harness Ship updates only the single `## harness-ship` block. It does not replace global agents or
settings.
