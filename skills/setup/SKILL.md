---
name: setup
description: >-
  Configure harness-ship for THIS project — detect the stack, issue tracker, branch topology and
  test commands, then write a config block the workflows read. Run once right after installing the
  plugin. Triggers: "/setup", "set up harness-ship", "configure harness-ship", "harness-ship setup",
  or immediately after `/plugin install harness-ship`.
---

# setup

A one-time step so `dev-workflow`, `testing-workflow`, `spec`, `tickets`, and `review` run against
this project's **real** specifics instead of generic defaults. Detect what you can, ask only the
forks a wrong guess would get wrong, and write the result where the workflows look.

Follow the same discipline the workflows preach: **answer the 90% with stated assumptions, ask only
the load-bearing forks** (don't interrogate).

## Process

### 1. Detect (never ask what you can read)

- **Stack + commands** — infer test / lint / typecheck from what's present:
  - `package.json` scripts (`test`, `lint`, `typecheck`) → npm/pnpm/yarn per lockfile.
  - `pyproject.toml` / `setup.cfg` (ruff, mypy, pytest) → `uv run` / `python -m` per config.
  - `pubspec.yaml` → `flutter analyze` / `flutter test`.
  - `go.mod` → `go vet ./...` / `go test ./...`.
  - `Makefile` lint/test/check targets → prefer them if they exist.
- **Issue tracker** — a GitHub remote + `gh` available → GitHub issues; a Linear MCP/config → Linear;
  otherwise local files under `.scratch/`.
- **Branch topology** — the default branch; whether a distinct integration branch
  (`staging` / `develop`) exists separate from the release branch.
- **Data-mutation risk** — any `.github/workflows/*.yml` with `schedule:`, or batch/cron DB writers
  in the code → the `review` safety gate should be **on**.
- **UI convention** — a `docs/design/` mocks directory or an existing design-system/tokens file →
  front-end-first applies.

### 2. Propose, then ask only the forks

Present the detected config as an **Assumptions** list (each line with its *why*). Ask ONLY the
questions a wrong guess would get wrong — typically at most ~3:
- which branch is the **protected release branch** (never auto-merged) vs the integration branch;
- the **tracker**, if GitHub vs Linear vs local is ambiguous;
- the **data-mutation gate** on/off, if cron/batch writes are unclear.

Everything with a safe default → state the default, don't ask.

### 3. Write the config where the workflows read it

Write (creating if absent) a `## harness-ship` section into the project's **`AGENTS.md`** — or
`CLAUDE.md` if that is the project's convention. Use the template below. Confirm the written block
with the user. After this, every harness-ship workflow consumes it automatically.

<config-template>

## harness-ship

- **Issue tracker:** <GitHub issues via `gh` | Linear | local `.scratch/` files>
- **Integration branch:** <e.g. `staging`> — feature PRs target this; never push to it directly.
- **Protected release branch:** <e.g. `main`> — human + release gate only; workflows never merge here.
- **Test / lint / typecheck:** `<test cmd>` / `<lint cmd>` / `<typecheck cmd>`
- **Agent-ready label:** <e.g. `ready-for-agent`>
- **Data-mutation safety gate:** <on | off> — on when the project has scheduled/batch DB writers.
- **UI convention:** <front-end-first mocks under `docs/design/` | none>

</config-template>

## Idempotent

Re-running `setup` re-detects and updates the existing `## harness-ship` block rather than
duplicating it. Safe to run again after the stack, tracker, or branch topology changes.
