---
name: setup
description: >-
  Configure harness-ship for THIS project — detect the stack, issue tracker, branch topology and
  test commands, then write a config block the workflows read. Run once right after installing the
  plugin. Triggers: "/setup", "set up harness-ship", "configure harness-ship", "harness-ship setup",
  or immediately after `/plugin install harness-ship`.
---

# setup

A one-time step so `dev-workflow`, `implement`, `testing-workflow`, `spec`, `tickets`, `tdd`, and
`review` run against this project's **real** specifics instead of generic defaults. Detect what you
can, ask only the forks a wrong guess would get wrong, and write the result where the workflows
look.

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
- **Agent role profiles** — inspect the current host runtime's existing agent registry and
  project/global instructions. Keep portable **Agent role requirements** separate from
  host-specific bindings. Under the current host binding, record each useful profile's exact ID,
  work nature, mode/sandbox, model, effort, write scope, MCP/plugin access, authoritative definition
  source, and whether it may spawn children. Also record root's thread/depth limit when exposed.
  - Route by nature: narrow lookup, exploration, mechanical implementation, judgment-bearing
    implementation, plan verification, independent verification, and security review/execution.
  - Profiles must already exist in the host. **Do not create or override** global agents, model
    assignments, effort, mode, permissions, or MCP/plugin access during project setup.
  - Persist `may_spawn=false` for every leaf profile. Record fields the host cannot expose as
    `unsupported`; do not claim they were verified.
  - Undefined generic/default workers do not satisfy a required role. A pre-defined independent
    verifier is mandatory; if it is missing, drifted, or unverifiable, `implement` is blocked.
  - Codex and Claude Code bindings are separate. Update only the current host's binding and preserve
    the other host section; never apply one host's profile IDs or model/effort values to the other.

### 2. Propose, then ask only the forks

Present the detected config as an **Assumptions** list (each line with its *why*). Ask ONLY the
questions a wrong guess would get wrong — typically at most ~3:
- which branch is the **protected release branch** (never auto-merged) vs the integration branch
  (skip if only one branch exists — they're the same);
- the **tracker system and its access method**, if ambiguous — and whether issues/PRs are split;
- the **data-mutation gate** on/off, if cron/batch writes are unclear.
- the **ready criteria** and atomic **claim transition**, if the tracker does not expose an obvious
  ready → claimed/in-progress path with owner/session identity;
- the **claim recovery** policy (lease/heartbeat, receipt-backed resume, expired-claim takeover, and
  release) when the tracker does not provide one;
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

- **Issue tracker:** <system + access method, e.g. `Jira project CB via Atlassian MCP` | `GitHub issues via gh` | `Linear MCP` | `local .scratch/ files`>
- **Code review / PR host:** <e.g. `GitHub via MCP` | `GitHub via gh` | `GitLab MR`> — may differ from the issue tracker.
- **Forbidden tools:** <e.g. `gh` CLI (policy) | none> — workflows must avoid these even when installed.
- **Integration branch:** <e.g. `staging`> — feature PRs target this; never push to it directly. If the repo has only one branch, this equals the release branch below.
- **Protected release branch:** <e.g. `main`> — human + release gate only; workflows never merge here.
- **Test / lint / typecheck / build:** `<test cmd>` / `<lint cmd>` / `<typecheck cmd>` / `<build cmd>` — write `none` for any the project lacks; workflows skip a `none` step instead of flagging it missing.
- **Ready criteria:** <label / status / sprint that makes a ticket eligible, e.g. `ready-for-agent`>
- **Claim transition:** <atomic assignment + claimed/in-progress state with root/session identity | single-root/manual claim policy>
- **Claim recovery:** <lease + heartbeat interval; same-owner resume; receipt validation; expired-claim takeover; release policy>
- **Remote CI infrastructure retry:** <attempt limit + backoff | none> — applies only to unrelated infrastructure failures, never code/test failures.
- **Deployment / test environment:** <environment + deploy/status access + exact source-SHA/artifact revision surface + URL/fixtures | manual/none>
- **Agent orchestration:** root session owns planning, delegation, integration, external state, and final decision; children may not spawn.
- **Agent role requirements:** portable policy; host bindings below must satisfy it.

  | Work nature | Required capability boundary | Minimum effort class |
  |---|---|---|
  | narrow lookup | read-only, no MCP/plugins | low |
  | exploration | read-only, no MCP/plugins | medium |
  | mechanical implementation | bounded workspace write | medium |
  | judgment implementation | bounded workspace write | medium |
  | plan verification | read-only and independent | high |
  | independent verification | no source edits and fresh context | high |
  | security review | read-only trust-boundary analysis | highest configured |
  | security implementation | bounded write, already-scoped security fix | highest configured |

- **Agent role bindings — Codex:** `not-configured`, or one live row per requirement:

  | Work nature | Host / profile ID | Definition source | Mode / sandbox | Model | Effort | Write scope | MCP/plugins | May spawn |
  |---|---|---|---|---|---|---|---|---|
  | `<requirement>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value or unsupported>` |

- **Agent role bindings — Claude Code:** `not-configured`, or one live row per requirement:

  | Work nature | Host / profile ID | Definition source | Mode / sandbox | Model | Effort | Write scope | MCP/plugins | May spawn |
  |---|---|---|---|---|---|---|---|---|
  | `<requirement>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value>` | `<host value or unsupported>` |

- **Delegation limits — Codex:** <host max direct children / depth / root-only spawning | `not-configured`>
- **Delegation limits — Claude Code:** <host max direct children / depth / root-only spawning | `not-configured`>
- **Writer scheduling:** serialize all write-capable children in one ticket worktree; only read-only work may run in parallel.
- **Data-mutation safety gate:** <on | off> — on when the project has scheduled/batch DB writers.
- **UI convention:** <front-end-first mocks under `docs/design/` | none>

</config-template>

## Idempotent

Re-running `setup` re-detects and updates the existing `## harness-ship` block rather than
duplicating it. Safe to run again after the stack, tracker, branch topology, deployment path, or
host role definitions change.
