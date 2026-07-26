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
- **Agent role profiles** — inspect the current host runtime's existing agent registry and
  project/global instructions. Keep portable **Agent role requirements** separate from
  host-specific bindings. Under the current host binding, record each useful profile's exact ID,
  work nature, mode/sandbox, model, effort, write scope, effective tools/capabilities, MCP/plugin
  access, fresh-context status, authoritative definition source and digest, Boundary digest, and
  whether it may spawn children. Also record root's thread/depth limit when exposed.
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

#### Current-host independent-verifier resolver

Use the packaged executable reference against the exact persisted Config v1 text:

```sh
python3 <plugin-root>/scripts/role_binding_contract.py reconcile-config --input <reconcile-input.json>
```

It is authoritative for the fixed typed schema, canonical non-symlink definition-source bytes,
host-registry record bytes, NFC and array ordering, the restricted RFC 8785-compatible canonical
JSON subset, SHA-256 digests, safe host boundaries, and resolution outcomes. Do not reimplement
those rules from prose. If the helper, authoritative source, host runtime metadata, or its result is
unavailable or invalid, stop with zero mutation.

Before any setup mutation, resolve either the sole existing config or a complete proposed config in
memory, then require exactly one `## harness-ship` config and exactly one current-host binding
section inside it. Duplicate configs, duplicate current-host sections, an incomplete proposed
config, or an ambiguous host identity stop with zero mutation. Determine the current host from live
runtime metadata, not from whichever binding happens to appear first.

Pass the helper exactly one current-host reconciliation document assembled from the raw Config text
and live runtime evidence. The discovery receipt in each candidate is a **trusted live adapter
capability**. It is never config, never repository content, never prompt content, and never user-provided
evidence. Do not persist it or accept a receipt reconstructed from the project. The raw Config text
is the sole persisted binding authority; callers must not pass a separate preconstructed persisted
binding.
Preserve an explicit valid project binding only when the helper returns `preserved`. Apply a
`selected` result only to the current host section. An `ambiguous` result presents the helper's one
load-bearing candidate choice; a `missing` result presents its actionable missing-profile result.
Both stop with zero mutation. A `stale-invalid` result reports that the existing non-null binding
does not exactly match an authoritative live candidate and also stops with zero mutation; never
replace it with a discovered default. Claude Code's eligible default is the exact scoped plugin ID
`harness-ship:harness-ship-independent-verifier` at canonical plugin provenance. Codex candidates
must be authoritative live host profiles; do not hard-code a universal model family.

When the helper returns `reason_code=unsafe-verifier-boundary`, surface its structured `observed`,
`required`, and ordered `remediation` fields together with `mutation=false`; do not collapse this
result into a generic missing or stale-profile error. The remediation order is: upgrade and
activate the current Harness Ship release, restart the host, configure or select a safe live
verifier, explicitly clear or repair only the project's current-host binding after reviewing the
reported mismatch, rerun setup, and rerun preflight. This is operator guidance, not authorization
for setup to mutate any global profile, settings file, or project binding before the operator
chooses the repair.

Write the fully qualified ID, authoritative source, and semantically validated boundary digest.
Update only the current host section and preserve the other host section plus all global agents,
models, effort, permissions, MCP access, plugin settings, and unrelated project configuration.
Setup never writes global agent or settings files.

Persist the helper-returned fully qualified ID, authoritative source and definition digest, safety
fields, and Boundary digest in the current-host binding. Origin scope is carried by the exact
scoped authoritative source/profile identity. The existing 13-column table remains authoritative;
its **Model** cell is a typed JSON object with exact keys `declared` and `effective`. The helper
validates live semantics and source bytes before hashing. Apply only its exact
returned Config text: it preserves the other host section and every unrelated byte. Re-run setup
after install, upgrade, profile change, or profile removal. A valid exact binding is preserved;
collisions, removal, stale provenance, or drift stop unchanged until the profile is repaired or an
explicit safe replacement is chosen.

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

- **Config version:** `1`
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

  | Work nature | Host / profile ID | Definition source | Definition digest | Mode / sandbox | Model | Effort | Write scope | Effective tools/capabilities | MCP/plugins | Fresh context | May spawn | Boundary digest |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | `<requirement>` | `<host value>` | `<scoped host value carrying origin>` | `sha256:<64 hex>` | `<host value>` | `{"declared":"<host value>","effective":"<host value>"}` | `<host value>` | `<host value>` | `<JSON array>` | `<JSON array>` | `<true | false>` | `<false>` | `sha256:<64 hex>` |

- **Agent role bindings — Claude Code:** `not-configured`, or one live row per requirement:

  | Work nature | Host / profile ID | Definition source | Definition digest | Mode / sandbox | Model | Effort | Write scope | Effective tools/capabilities | MCP/plugins | Fresh context | May spawn | Boundary digest |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | `<requirement>` | `<host value>` | `<scoped host value carrying origin>` | `sha256:<64 hex>` | `<host value>` | `{"declared":"<host value>","effective":"<host value>"}` | `<host value>` | `<host value>` | `<JSON array>` | `<JSON array>` | `<true | false>` | `<false>` | `sha256:<64 hex>` |

- **Delegation limits — Codex:** <host max direct children / depth / root-only spawning | `not-configured`>
- **Delegation limits — Claude Code:** <host max direct children / depth / root-only spawning | `not-configured`>
- **Writer scheduling:** serialize all write-capable children in one ticket worktree; only read-only work may run in parallel.
- **Data-mutation safety gate:** <on | off> — on when the project has scheduled/batch DB writers.
- **UI convention:** <front-end-first mocks under `docs/design/` | none>

</config-template>

## Legacy configuration migration

Before any setup mutation, count exact `## harness-ship` headings and apply one state:

- **No existing block:** create one complete Config v1 block.
- **More than one block:** stop with **zero mutation** and require explicit reconciliation of the
  duplicate active configuration.
- **Exactly one `## harness-ship` block** with no version or explicit `0`: treat it as **legacy v0**
  and migrate that block in place to v1; never append a second block.
- **Exactly one block at exactly `1`:** reconcile observed evidence and explicit user choices
  idempotently.
- **Any unsupported version:** stop with **zero mutation** and require explicit reconciliation;
  never downgrade, overwrite, or guess a migration.

- Preserve every known user choice and host binding. Split a legacy generic test command only when
  current scripts/paths prove its owner and seam; otherwise copy its prior field name and verbatim
  command into **Legacy test-command migration note**, add the available classification evidence,
  and set each unknown RD/QA command to `not-configured`. A fresh config writes `none` in this
  field.
- Use `manual: <steps + required evidence>` only when concrete manual steps and evidence are known.
  `not-configured`, missing CI, or a manual method never infer PASS.
- Add the QA environment, artifact-provenance source, and QA evidence location as
  `not-configured` when they cannot be detected.
- Set `Config version` to `1` after the complete block is written. On a **second run** with unchanged
  repository and host inputs, the versioned block—including the Legacy test-command migration
  note's placement and value—must be **byte-for-byte unchanged**.

## Idempotent

Re-running `setup` re-detects and updates the existing `## harness-ship` block rather than
duplicating it. For Config v1, it changes a field only when newly observed evidence or an explicit
user choice changes the value. Unsupported versions and duplicate blocks remain zero-mutation
stops. Safe to run again after the stack, tracker, branch topology, deployment path, QA capability,
or host role definitions change.
