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

## Test and release confidence migration

Releases with the test-and-release-confidence surface remove mandatory development orchestration
and keep Config v3.

- Replace `dev-workflow` with the independent command needed now: `test-plan`,
  `exploratory-testing`, `testing-workflow`, or `release-gate`.
- Replace `acceptance-design` with `test-plan`. Existing acceptance criteria can become the first
  Release Delta; reusable P0 journeys become the Project Test Baseline.
- Bug Cases stop at a repair handoff. Remove automation that expects
  `bug-workflow → implement → tdd`; return a new exact candidate to `testing-workflow` instead.
- `implement` and `tdd` remain available only as explicit opt-ins. They are not release
  prerequisites.
- The seven development helpers — `clarify`, `spike`, `spec`, `tickets`, `implement`, `tdd`,
  `review` — are now user-invoked only. Natural language no longer reaches them: "review this"
  runs whatever your own stack provides. Type `/harness-ship:review` (Codex:
  `$harness-ship:review`) to run this plugin's version.
- Replace links to `qa-handoff-template.md` and `acceptance-report-template.md` with
  `candidate-handoff-template.md` and `test-report-template.md`.

Existing Config v3 projects **do not rerun setup**. Approve a Test Contract before invoking
`release-gate`.

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

**Invocation-time review routing:** no reviewer identity is stored in project config and no custom
Codex profile is required. Review resolves fresh children from the running host. A specialised
read-only verifier is preferred; an available generic host child is valid and carries the assurance
the host can actually establish. This change needs no setup migration.

**After v2.0.0:** the generic `role_binding_contract.py readiness` command is removed. Delete direct
calls to it; each workflow now resolves missing test, QA, UI, and data-mutation capabilities only
when an actual task needs them. Existing Config v3 blocks remain valid and do not need setup again.

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
detection. Reviewer assurance is recorded after invocation and is not an implementation-readiness
gate.

**v0.7.0 migration (historical):** setup proposed Config v1 → v2 without writing it, and applied
the proposal only after an exact confirmation of the reviewed diff. That two-phase planner was
removed in v1.0.0; a block on an unsupported Config version is now regenerated, not migrated.

**v0.6.4 migration (historical):** that release required a configured live verifier. Current
versions supersede that binding with invocation-time reviewer routing; do not create or repair a
profile when upgrading now.

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
migration is attempted. Verify the packaged Claude agent with
`python3 <plugin-root>/scripts/role_binding_contract.py preflight --config CLAUDE.md`; a project
still carrying the old table fails closed on its `Config version`, which is the intended detection.
Run it from a Claude Code session — the host sets `CLAUDECODE`, and a plain terminal instead reports
`independence: not established` and exits `1`. From that session the gate reports
`assurance: host-enforced`, meaning the packaged verifier agent definition was read and compared at
check time; `status: pass` is what reports that its tools, model and effort matched.

**v0.7.0 migration (historical):** setup proposed Config v1 → v2 without writing it, and applied
the proposal only after an exact confirmation of the reviewed diff. That two-phase planner was
removed in v1.0.0; a block on an unsupported Config version is now regenerated, not migrated.

**v0.6.4 migration (historical):** that release required a configured live verifier. Current
versions resolve reviewers at invocation; the packaged Claude verifier remains preferred without a
project binding.

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
settings; reviewer identity is resolved from the running host when review starts.
