# Upgrade guide

Choose one channel, upgrade its marketplace source, install the refreshed plugin, restart or reload
the real host process, start a new session, and re-run setup in every configured project.

`harness-ship` is the stable channel pinned to `v0.7.0`; `harness-ship-next` is an explicit
unreleased channel pinned to `main`. Both resolve to the same underlying plugin namespace and are
mutually exclusive. Remove the installed channel before switching. A local editable checkout is a
development source and does not receive managed upgrades or prove the tagged release.
The marketplace catalog is added or refreshed from `main`; only its stable plugin entry is pinned
to the release tag. This lets a catalog refresh discover a future stable patch without silently
moving the already published stable source.

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

**Which upgrades need a re-run of setup:** only a **Config version** change. The plugin version in
the block records what wrote it and is never a gate, so a patch or compatible minor release leaves
every configured project working. `preflight` reports the config version it read and fails closed —
with an actionable message — when the schema is one this release does not support.

**v0.8.0 migration (breaking):** Config version 2 → 3, and the verifier binding format changed.
The 13-column host binding table, the `Verifier binding-contract version` field, and the
discovery-receipt input are gone. Re-run setup once per configured project to regenerate the
`## harness-ship` block; setup writes a single `Independent verifier:` line in their place and
stamps `Config version: 3`. Nothing else in the block changes, and no automatic migration is
attempted — the machinery that migrated the old table was removed along with
the digest chain it existed to preserve, and reconstructing it would cost more than re-running
setup.

Verify with `python3 <plugin-root>/scripts/role_binding_contract.py preflight --config AGENTS.md`.
A project still carrying the old table fails closed on its `Config version`, which is the intended
detection.

The gate now reports an `assurance` field. `host-enforced` (Claude Code) means the packaged agent
definition was read at check time and its tools, model and effort matched. `independence: not
established` (every other host) means this plugin ships no verifier there; preflight exits `1`,
which marks `implement`'s gate unmet rather than passed.

**v0.7.0 migration:** setup proposes Config v1 → v2 without writing it. Review the complete plan
and exact configuration diff, correct unsafe or unknown bindings, and explicitly confirm that exact
proposal. Only then apply it. If repository state or the proposal changes, discard the old
confirmation and repeat plan → review → exact confirmation → apply. Restart/reload Codex and begin
a new session before trusting the new plugin source.

**v0.6.4 migration:** upgrade and activate the plugin, then restart Codex. If the verifier
diagnostic reports an unsafe boundary, configure or select one **safe live verifier** with
host-enforced read-only permissions. Harness Ship performs **zero mutation** of global profiles or
an unsafe persisted binding: after reviewing the mismatch, explicitly clear or repair only the
project's **current-host binding**, rerun setup, then rerun preflight before implementation.

**v0.6.3 migration:** every Config v1 project must run `$harness-ship:setup` once after install or
upgrade. Raw-text reconciliation upgrades the legacy binding row, preserves an exact valid binding
across plugin relocation, and changes only the current-host payload. Re-run setup after a profile
change or profile removal. A collision, stale source, ambiguous default, or drift stops unchanged;
repair or explicitly choose the safe live profile, then rerun setup.

**v0.5.0 migration:** setup began recording the host's pre-defined agent role profiles.

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

**v0.7.0 migration:** setup proposes Config v1 → v2 without writing it. Review the complete plan
and exact configuration diff, correct unsafe or unknown bindings, and explicitly confirm that exact
proposal. Only then apply it. If repository state or the proposal changes, discard the old
confirmation and repeat plan → review → exact confirmation → apply. Restart Claude Code and begin
a new session before trusting the new plugin source.

**v0.6.4 migration:** upgrade the plugin, then restart Claude Code. If the verifier diagnostic
reports an unsafe boundary, configure or select one **safe live verifier** with host-enforced
read-only permissions. Harness Ship performs **zero mutation** of global profiles or an unsafe
persisted binding: after reviewing the mismatch, explicitly clear or repair only the project's
**current-host binding**, rerun setup, then rerun preflight before implementation.

**v0.6.3 migration:** every Config v1 project must run `/harness-ship:setup` once after install or
upgrade. Raw-text reconciliation upgrades the legacy binding row, preserves an exact valid binding
across plugin relocation, and changes only the current-host payload. Re-run setup after a profile
change or profile removal. A collision, stale source, ambiguous default, or drift stops unchanged;
repair or explicitly choose the safe live profile, then rerun setup.

**v0.5.0 migration:** setup began recording the host's pre-defined agent role profiles.

## Editable local development

Run Python and lifecycle contracts directly in an editable checkout, or use the host's temporary
local plugin-directory facility for attended testing. Do not register or alter global plugin state
as part of repository validation. Local source changes are immediate, so restart/reload the
consumer after each source change; managed marketplace upgrade commands do not update a checkout.

## Earlier Config v1 projects

Setup proposes the upgraded Harness Ship block before applying it. Known values are preserved while RD
unit/API-contract commands remain separate from QA integration/P0/full-suite commands. It records
the QA environment, artifact provenance, and evidence location; unavailable capabilities remain
`not-configured`.

Harness Ship updates only the current host section. It does not replace global agents or settings,
and it does not silently weaken or select an ambiguous verifier profile. Config v2 apply requires
review and exact confirmation of the current proposal.
