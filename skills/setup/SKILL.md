---
name: setup
description: >-
  Configure harness-ship for THIS project — detect the stack, issue tracker, branch topology and
  test commands, then write a config block the workflows read. Run once right after installing the
  plugin. Triggers: "/setup", "set up harness-ship", "configure harness-ship", "harness-ship setup",
  or immediately after `/plugin install harness-ship`.
---

# setup

A one-time step so `dev-workflow`, `acceptance-design`, `implement`, `testing-workflow`, `spec`,
`tickets`, `tdd`, and `review` run against this project's **real** specifics instead of generic
defaults. Detect what you can, ask only the forks a wrong guess would get wrong, and write the
result where the workflows look.

Follow the same discipline the workflows preach: **answer the 90% with stated assumptions, ask only
the load-bearing forks** (don't interrogate).

## Process

### 1. Detect (never ask what you can read)

- **Stack + commands** — infer test / lint / typecheck / build from what's present:
  - `package.json` scripts (`test`, `lint`, `typecheck`, `build`) → npm/pnpm/yarn per lockfile.
  - `pyproject.toml` / `setup.cfg` (ruff, mypy, pytest) → `uv run` / `python -m` per config.
  - `pubspec.yaml` → `flutter analyze` / `flutter test`.
  - `go.mod` → `go vet ./...` / `go test ./...`.
  - `Makefile` lint/test/check targets → prefer them if they exist.
  - Classify commands by owner and seam only when scripts, paths, or framework configuration prove
    the distinction: RD unit, RD API-contract, QA integration, QA P0, and QA full-suite. Unknown
    capability is `not-configured`; an explicit manual QA path is
    `manual: <steps + required evidence>`. Never infer PASS from a command's absence.
- **Issue tracker** — infer the system AND its access method; they are separate questions:
  - a Jira/Atlassian MCP or `[A-Z]+-\d+` keys in commit messages → Jira via that MCP;
  - a Linear MCP/config → Linear;
  - a GitHub remote → GitHub issues **only if** a usable access path exists (MCP, or `gh`
    that policy permits — a `gh` binary being installed does NOT mean it's allowed);
  - otherwise local files under `.scratch/`.
  - **Issues and PRs may live in different systems** (e.g. Jira issues + GitHub PRs) — capture both.
  - Note any **forbidden tool** you spot (e.g. a `gh` ban in `CLAUDE.md`/policy) so workflows avoid it.
- **Branch topology** — the default branch; whether a distinct integration branch
  (`staging` / `develop`) exists separate from the release branch. **If only one branch exists**
  (the common case), integration and release collapse onto it — record the same branch for both.
- **Data-mutation risk** — any `.github/workflows/*.yml` with `schedule:`, or batch/cron DB writers
  in the code → the `review` safety gate should be **on**.
- **UI convention** — a `docs/design/` mocks directory or an existing design-system/tokens file →
  front-end-first applies.
Do **not** detect or ask about the QA environment, artifact-provenance source, QA evidence location,
deployment path, or claim/fencing policy at first run. They are irrelevant until a workflow reaches
them, and demanding them up front is what made setup an all-or-nothing exercise.

#### Reviewer routing is not configured

Nothing about reviewer identity belongs in project or global setup. `implement` and `review` resolve
fresh children from the running host when review starts: prefer a purpose-built read-only verifier
when one exists, otherwise use an available generic host child with the same bounded brief. Record
the actual run identity and assurance afterward. Setup never creates, overrides, or asks for an
agent profile.

Earlier versions wrote an `Independent verifier:` line into config. It is ignored, not an error.

### 2. Propose, then ask at most three questions

Present the detected config as an **Assumptions** list, each line with its *why*. Then ask **no more
than three** questions — only the forks where a wrong guess changes the plan:

1. the **protected release branch** vs the integration branch — skip when only one branch exists,
   which is the common case and needs no question at all;
2. the **tracker system and its access method**, when ambiguous, including whether issues and PRs
   live in different systems;
3. the **data-mutation gate**, when cron or batch DB writes are unclear.

Everything else has a safe default: state it, do not ask. Never ask the user to create or select a
reviewer profile, and never ask about a field that belongs to a later tier — those are asked at the
point of use, by the workflow that needs them.

### 3. Write the config where the workflows read it

Write (creating if absent) a `## harness-ship` section into the project's **`AGENTS.md`** — or
`CLAUDE.md` if that is the project's convention. Use the template below. Confirm the written block
with the user. After this, every harness-ship workflow consumes it automatically.

<config-template>

Write only the **first-run block**. Later tiers are appended by the workflow that needs them, not
requested up front.

## harness-ship

- **Plugin version:** `<version that wrote this block>` — informational, not a gate.
- **Config version:** `3`
- **Issue tracker:** <system + access method, e.g. `Jira project CB via Atlassian MCP` | `GitHub issues via gh` | `Linear MCP` | `local .scratch/ files`>
- **Code review / PR host:** <e.g. `GitHub via MCP` | `GitHub via gh` | `GitLab MR`> — may differ from the issue tracker.
- **Forbidden tools:** <e.g. `gh` CLI (policy) | none> — workflows must avoid these even when installed.
- **Integration branch:** <e.g. `staging`> — feature PRs target this; never push to it directly. If the repo has only one branch, this equals the release branch below.
- **Protected release branch:** <e.g. `main`> — human + release gate only; workflows never merge here.
- **RD unit command:** `<command | not-configured>`
- **RD API-contract command:** `<command | not-configured>`
- **Lint / typecheck / build:** `<lint cmd>` / `<typecheck cmd>` / `<build cmd>` — write `none` only when the project is known not to have that check.
- **Legacy test-command migration note:** <none | prior field name + verbatim command + classification evidence>
- **Data-mutation safety gate:** <on | off> — on when the project has scheduled/batch DB writers.
- **UI convention:** <front-end-first mocks under `docs/design/` | none>

Appended later, each by the workflow that first needs it — absent means the tier is not ready, never
that it passed:

- **QA integration command:** / **QA P0 command:** / **QA full-suite command:** `<command | manual: <steps + required evidence> | not-configured>`
- **QA environment:** <non-production environment + URL/access + fixtures/accounts>
- **Artifact-provenance source:** <provider/API/build manifest binding full source SHA to artifact revision>
- **QA evidence location:** <durable artifact store/path reachable from the tracker>
- **Deployment / test environment:** <artifact producer + deploy/status path | manual/none>
- **Ready criteria:** <label / status / sprint that makes a ticket eligible>
- **Claim transition:** / **Claim recovery:** <only when more than one session works this tracker>
- **Remote CI infrastructure retry:** <attempt limit + backoff | none>
- **Agent orchestration:** root owns planning, delegation, integration, external state, and the final decision; children may not spawn.
- **Writer scheduling:** serialize write-capable children in one ticket worktree; parallelize read-only work only.

</config-template>

## Report readiness, do not report a verdict

A project is not ready or unready as a whole. Report the three tiers separately so a missing
capability blocks only what depends on it:

```sh
python3 <plugin-root>/scripts/role_binding_contract.py readiness --config <AGENTS.md|CLAUDE.md>
```

| Tier | Needs | Unlocks |
|---|---|---|
| `planning` | a tracker | `clarify`, `spec`, `acceptance-design`, `tickets` |
| `implementation` | + integration branch, one RD command | `implement`, `tdd`, `review` |
| `qa` | + QA environment, artifact provenance, evidence location, one QA command | `testing-workflow` |

Show the blockers and the smallest next action for every tier that is not ready. A tier that is
blocked is reported as blocked — never as PASS, and never by declaring the whole project unusable.
Reviewer assurance is recorded by `review` after dispatch and is not a setup-readiness field.



## Existing configuration

Read the existing `## harness-ship` block before writing. Exactly one block may exist: **more than
one is a zero-mutation stop** until the duplicate is reconciled, because workflows would otherwise
read the wrong one.

Preserve every known user choice. Split a legacy generic test command only when current scripts or
paths prove its owner and seam; otherwise copy its prior field name and verbatim command into
**Legacy test-command migration note** and set each unknown RD/QA command to `not-configured`.
Use `manual: <steps + required evidence>` only when concrete manual steps and evidence are known.
`not-configured`, missing CI, or a manual method never infer PASS. Undetectable QA fields are written
`not-configured`.

Blocks written before v1.0.0 carried a 13-column host binding table per host and a
**Verifier binding-contract version** field. Both are gone: reviewer identity is resolved from the
running host when review starts, not persisted by setup. Re-run setup once to regenerate the block.

## Idempotent

Re-running `setup` updates the existing `## harness-ship` block rather than duplicating it, and
changes a field only when newly observed evidence or an explicit user choice changes its value. A
second run over unchanged repository and host inputs must leave the block byte-identical.
Unsupported Config versions and duplicate blocks remain zero-mutation stops.

That byte-identity is now a **discipline, not a guarantee**: the two-phase planner that enforced it
was removed with the digest machinery it existed to protect. The block is written with an ordinary
edit, and the recovery from a bad write is `git checkout AGENTS.md` — the file is version-controlled
by design. Say so rather than implying an atomicity that is no longer there.

Safe to run again after the stack, tracker, branch topology, or host role definitions change. A
later tier's fields are added when its workflow first needs them, so reaching QA does not mean
re-running setup from scratch.
