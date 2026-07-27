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
- **Deployment / test environment** — infer the non-production environment, deployment/status
  access method, artifact revision/source-SHA surface, URL, fixtures/accounts, and whether deploy is
  automatic or manual. Record `none/manual` honestly; `implement` then stops before QA until an
  external deployment receipt exists.
- **Agent role profiles** — inspect the current host's existing agent registry. Record each useful
  profile's ID and work nature. Profiles must already exist in the host: **do not create or override**
  global agents, models, effort, mode, permissions, or MCP/plugin access during project setup.
  Undefined generic/default workers do not satisfy a required role.

#### The independent-verifier gate

`implement` is blocked unless one independent verifier is bound and satisfies the required boundary:
read-only, cannot spawn children, fresh context, effort high or higher. Record it as one line:

```markdown
- **Independent verifier:** `claude-code` / `harness-ship:harness-ship-independent-verifier`
- **Independent verifier:** `codex` / `Codex/verifier` — mode=read-only, write=none, spawn=no, context=fresh, effort=high
```

Verify it with the packaged executable, which is authoritative — do not substitute a prose check:

```sh
python3 <plugin-root>/scripts/role_binding_contract.py preflight --config <AGENTS.md|CLAUDE.md>
```

The two hosts give different strengths of guarantee, and the gate reports which one you have:

- **Claude Code** (`assurance: host-enforced`) — the binding must be the packaged plugin agent. The
  gate reads that agent file at check time and compares its tools, model and effort against the
  boundary. The tool whitelist is enforced by the host permission layer, so a verifier that cannot
  invoke Edit is not merely promising to abstain. A failure names the field that drifted.
- **Codex** (`assurance: operator-declared`) — no Codex interface exposes live profile metadata. The
  operator writes the boundary down and the gate re-asserts it. This proves the declaration is
  correct; it cannot prove the live profile matches. Say so rather than implying more.

A non-zero exit stops setup and `implement` with zero mutation. Never replace a failing binding with
a discovered default, and never write global agent or settings files.

### 2. Propose, then ask only the forks

Present the detected config as an **Assumptions** list (each line with its *why*). Ask ONLY the
questions a wrong guess would get wrong — typically at most ~3:
- which branch is the **protected release branch** (never auto-merged) vs the integration branch
  (skip if only one branch exists — they're the same);
- the **tracker system and its access method**, if ambiguous — and whether issues/PRs are split;
- the **data-mutation gate** on/off, if cron/batch writes are unclear.
- the **ready criteria** and atomic **claim transition**, if the tracker does not expose an obvious
  ready → claimed/in-progress path with owner/session identity;
- the **claim recovery** policy (atomic claim + initial recovery receipt, lease/heartbeat,
  generation/fencing token, write-ahead checkpoints, receipt-backed resume, expired-claim takeover,
  and release) when the tracker does not provide one;
- the deployment/test environment path when no non-production target or artifact-source receipt is
  discoverable;
- a missing required verifier/security profile. Do not ask about profiles that can be read from the
  host config.

Everything with a safe default → state the default, don't ask.

### 3. Write the config where the workflows read it

Write (creating if absent) a `## harness-ship` section into the project's **`AGENTS.md`** — or
`CLAUDE.md` if that is the project's convention. Use the template below. Confirm the written block
with the user. After this, every harness-ship workflow consumes it automatically.

<config-template>

## harness-ship

- **Plugin version:** `0.7.0`
- **Config version:** `2`
- **Issue tracker:** <system + access method, e.g. `Jira project CB via Atlassian MCP` | `GitHub issues via gh` | `Linear MCP` | `local .scratch/ files`>
- **Code review / PR host:** <e.g. `GitHub via MCP` | `GitHub via gh` | `GitLab MR`> — may differ from the issue tracker.
- **Forbidden tools:** <e.g. `gh` CLI (policy) | none> — workflows must avoid these even when installed.
- **Integration branch:** <e.g. `staging`> — feature PRs target this; never push to it directly. If the repo has only one branch, this equals the release branch below.
- **Protected release branch:** <e.g. `main`> — human + release gate only; workflows never merge here.
- **RD unit command:** `<command | not-configured>`
- **RD API-contract command:** `<command | not-configured>`
- **QA integration command:** `<command | manual: <steps + required evidence> | not-configured>`
- **QA P0 command:** `<command | manual: <steps + required evidence> | not-configured>`
- **QA full-suite command:** `<command | manual: <steps + required evidence> | not-configured>`
- **Legacy test-command migration note:** <none | prior field name + verbatim command + classification evidence>
- **Lint / typecheck / build:** `<lint cmd>` / `<typecheck cmd>` / `<build cmd>` — write `none` only when the project is known not to have that check.
- **QA environment:** <non-production environment + URL/access + fixtures/accounts | not-configured>
- **Artifact-provenance source:** <provider/API/build manifest that binds full source SHA to artifact revision | not-configured>
- **QA evidence location:** <durable artifact store/path accessible from the tracker | not-configured>
- **Ready criteria:** <label / status / sprint that makes a ticket eligible, e.g. `ready-for-agent`>
- **Claim transition:** <atomic assignment + claimed/in-progress state with root/session identity, fencing generation, and initial recovery receipt | single-root/manual claim policy>
- **Claim recovery:** <lease + heartbeat interval; ownership/fencing checks before mutations; write-ahead checkpoints; live-state reconciliation; same-owner resume; receipt validation; expired-claim takeover; release policy>
- **Remote CI infrastructure retry:** <attempt limit + backoff | none> — applies only to unrelated infrastructure failures, never code/test failures.
- **Deployment / test environment:** <artifact producer + deploy/status path; its receipt must agree with the QA environment and artifact-provenance source above | manual/none>
- **Agent orchestration:** root session owns planning, delegation, integration, external state, and final decision; children may not spawn.
- **Independent verifier:** `<claude-code | codex>` / `<profile id>`<` — mode=…, write=…, spawn=…, context=…, effort=…` for Codex>
- **Writer scheduling:** serialize all write-capable children in one ticket worktree; only read-only work may run in parallel.
- **Data-mutation safety gate:** <on | off> — on when the project has scheduled/batch DB writers.
- **UI convention:** <front-end-first mocks under `docs/design/` | none>

</config-template>

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

Blocks written before v0.8.0 carried a 13-column host binding table per host and a
**Verifier binding-contract version** field. Both are gone: the gate reads the binding line directly
and fails closed on anything it cannot parse, so a separate version for it detected nothing the gate
does not. Re-run setup once to regenerate the block.

## Idempotent

Re-running `setup` re-detects and plans updates to the existing `## harness-ship` block rather than
duplicating it. For Config v2, it changes a field only when newly observed evidence or an explicit
user choice changes the value. Unsupported versions and duplicate blocks remain zero-mutation
stops. Safe to run again after the stack, tracker, branch topology, deployment path, QA capability,
or host role definitions change.
