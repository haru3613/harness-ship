# Upgrade guide

Upgrade the marketplace source, install the refreshed plugin, start a new host session, and re-run
setup in every configured project.

## Codex

```sh
codex plugin marketplace upgrade harness-ship
codex plugin add harness-ship@harness-ship
```

Start a new Codex session before running `$harness-ship:setup`.

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

**v0.6.0 migration:** call `$harness-ship:acceptance-design` for pre-implementation scenario design.
`$harness-ship:testing-workflow` redirects legacy pre-implementation and missing-contract calls
there for this minor release and otherwise starts only after the dev→QA handoff.

## Claude Code

```sh
claude plugin marketplace update harness-ship
claude plugin update harness-ship@harness-ship
```

Restart Claude Code before running `/harness-ship:setup`.

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

**v0.6.0 migration:** call `/harness-ship:acceptance-design` for pre-implementation scenario
design. `/harness-ship:testing-workflow` redirects legacy pre-implementation and missing-contract
calls there for this minor release and otherwise starts only after the dev→QA handoff.

## Earlier Config v1 projects

Setup upgrades the existing Harness Ship block in place. Known values are preserved while RD
unit/API-contract commands remain separate from QA integration/P0/full-suite commands. It records
the QA environment, artifact provenance, and evidence location; unavailable capabilities remain
`not-configured`.

Harness Ship updates only the current host section. It does not replace global agents or settings,
and it does not silently weaken or select an ambiguous verifier profile.
