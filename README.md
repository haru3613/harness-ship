# harness-ship

**Idea → shipped, humans on the ends.** A development + testing workflow for Codex and Claude
Code. You pilot five judgment gates; AI runs the bounded work between them.

> The core belief: assume the user has stated ~10% of what a feature needs. The AI's job is to
> surface the other 90% — not by interrogating, but by answering it with stated assumptions and
> explaining *why*, then asking only about the few forks where the answer changes the plan.
> **Automate the labour, keep the judgment.**

## What's inside

One bootstrap skill and three orchestration skills, plus nine self-contained blocks, make 13
bundled skills. Harness Ship has no third-party skill-pack dependency, but it relies on the
selected host, its tools, and validated role profiles for execution.

| Skill | Role |
|---|---|
| **`setup`** | one-time: detect the project's stack/tracker/branches and write the config the workflows read |
| **`dev-workflow`** | idea → clarify → feasibility → spec → acceptance contract → tickets → implement → QA handoff |
| **`implement`** | root-orchestrated, role-routed ticket delivery → TDD slices → review → exact-SHA PR/CI evidence |
| **`testing-workflow`** | approved scenarios after handoff → QA execution → gate → acceptance report |
| `clarify` | bounded requirement clarification — only load-bearing questions, defaults become assumptions |
| `spike` | time-boxed throwaway prototype that returns a feasible / not / needs-more verdict |
| `spec` | synthesize the conversation into a spec/PRD with explicit AC at the highest test seam |
| `acceptance-design` | current stable spec → versioned, traceable Given/When/Then acceptance contract |
| `tickets` | break an approved spec + acceptance contract into vertical-slice tracer-bullet tickets |
| `tdd` | implement one ticket through evidence-backed RED → GREEN behaviour slices at approved seams |
| `review` | dual-axis code review (Standards × Spec) with an optional data-mutation safety gate |
| `bug-workflow` | QA non-pass → one Bug Case → classification route → product-defect closure receipts |
| `diagnose` | safe RD cause analysis → append-only Diagnosis Receipt; never product repair |

## The five human gates

1. **Feasibility** — go / spike-first / split / no.
2. **UI 定稿** — for UI features, the design is approved before backend.
3. **Acceptance contract** — do the pre-implementation scenarios describe the right behaviour.
4. **Ticket granularity** — are the slices and dependencies right.
5. **Acceptance** — after the testing-workflow produces a plain-language acceptance report.

Never sail past a gate autonomously. Between gates, don't stall for permission.

## Project status

Harness Ship is usable from Git today, but this repository is still private while its public-release
gates are reviewed. The source, plugin lifecycle, and contract suite are maintained; public
visibility, history privacy, and GitHub security settings are separate maintainer decisions.

See [Releases](https://github.com/haru3613/harness-ship/releases) for version-specific changes.
The plugin manifests are the version source of truth.

## Prerequisites

- Git.
- Codex or Claude Code with plugin marketplace commands available.
- Access to this repository while it remains private. Public clones will not require GitHub
  authentication after visibility changes.
- A target repository where Harness Ship may write its generated project configuration.

Check the host capability before installing:

```sh
codex plugin --help
# or
claude plugin --help
```

## Install

While this repository is private, collaborators must authenticate GitHub HTTPS access before either
plugin manager can clone it:

```sh
gh auth login       # skip when `gh auth status` is already green
gh auth setup-git
```

After the repository becomes public, skip this authentication step. Until then, a GitHub Release
does not grant repository access.

### Codex

First install:

```sh
codex plugin marketplace add haru3613/harness-ship --ref main
codex plugin add harness-ship@harness-ship
```

If marketplace installation reports `could not read Username for 'https://github.com'`, run
`gh auth setup-git`, verify that
`git ls-remote https://github.com/haru3613/harness-ship.git refs/heads/main` succeeds, then retry.

Update an existing install:

```sh
codex plugin marketplace upgrade harness-ship
codex plugin add harness-ship@harness-ship
```

The marketplace upgrade refreshes the Git source; the second command activates that refreshed
plugin version.

Start a new Codex session after installing or upgrading so Codex loads the refreshed skills. Invoke
`$harness-ship:setup` once per project.

Codex installation supplies skills only; it does not supply an independent verifier. Setup binds
only a validated existing live host profile and fails closed when none is available. It never
creates or overwrites global agents or settings.

**v0.5.0 migration:** setup began recording the host's pre-defined agent role profiles.

**v0.6.0 migration:** call `$harness-ship:acceptance-design` for pre-implementation scenario design.
`$harness-ship:testing-workflow` redirects legacy pre-implementation and missing-contract calls
there for this minor release and otherwise starts only after the dev→QA handoff.

**v0.6.3 migration:** every Config v1 project must run `$harness-ship:setup` once after install or
upgrade. Raw-text reconciliation upgrades the legacy binding row, preserves an exact valid binding
across plugin relocation, and changes only the current-host payload. Re-run setup after a profile
change or profile removal. A collision, stale source, ambiguous default, or drift stops unchanged;
repair or explicitly choose the safe live profile, then rerun setup.

### Claude Code

First install:

```sh
claude plugin marketplace add haru3613/harness-ship
claude plugin install harness-ship@harness-ship
```

Update an existing install:

```sh
claude plugin marketplace update harness-ship
claude plugin update harness-ship@harness-ship
```

The marketplace update refreshes the catalog; the plugin update installs the refreshed plugin.

Restart Claude Code after installing or upgrading, then run `/setup` once per project.

Install supplies the verifier capability as the scoped Claude plugin agent
`harness-ship:harness-ship-independent-verifier`; project setup performs the current-host binding
after validating the effective live boundary. Harness Ship never copies agents into
`~/.claude/agents` and never overwrites global agents or settings.

**v0.5.0 migration:** setup began recording the host's pre-defined agent role profiles.

**v0.6.0 migration:** call `/harness-ship:acceptance-design` for pre-implementation scenario
design. `/harness-ship:testing-workflow` redirects legacy pre-implementation and missing-contract
calls there for this minor release and otherwise starts only after the dev→QA handoff.

**v0.6.3 migration:** every Config v1 project must run `/harness-ship:setup` once after install or
upgrade. Raw-text reconciliation upgrades the legacy binding row, preserves an exact valid binding
across plugin relocation, and changes only the current-host payload. Re-run setup after a profile
change or profile removal. A collision, stale source, ambiguous default, or drift stops unchanged;
repair or explicitly choose the safe live profile, then rerun setup.

Canonical direct commands are not compatibility aliases and remain after the v0.6 redirect expires:
Codex uses `$harness-ship:acceptance-design` and `$harness-ship:testing-workflow`; Claude Code uses
`/harness-ship:acceptance-design` and `/harness-ship:testing-workflow`.

**Config v1 migration:** re-run `setup` once. It upgrades the existing block in place, preserves
known values, separates RD unit/API-contract commands from QA integration/P0/full-suite commands,
and records the QA environment, artifact provenance, and evidence location. Unknown QA capability
stays `not-configured` or uses explicit manual steps; it never implies PASS.

## First use

1. Install or update the plugin, then start a new host session.
2. Open the target repository and run `$harness-ship:setup` in Codex or
   `/harness-ship:setup` in Claude Code.
3. Review the generated `## harness-ship` block in that project's `AGENTS.md` or `CLAUDE.md`.
4. Describe the feature or invoke `dev-workflow`; approve the feasibility, UI (when applicable),
   acceptance-contract, and ticket-granularity gates.
5. Let `implement` deliver one claimed ticket through RD evidence and a QA handoff.
6. Run `testing-workflow` against the approved current stable spec and exact handed-off artifact,
   then make the final acceptance decision.

`setup` detects your stack, issue tracker, branch topology and test commands, asks only the few
forks it can't infer, and writes a `## harness-ship` config block into your `AGENTS.md` (or
`CLAUDE.md`). Every workflow reads that block, so nothing runs on generic guesses.

Then invoke the platform's `dev-workflow`, `acceptance-design`, `implement`, `tdd`,
`testing-workflow`, or `bug-workflow` skill — or just describe a feature and the skills trigger
themselves. Re-run `setup` any time the stack, tracker, branches, or host agent profiles change.

## What `setup` configures

- **Issue tracker** — where `spec`/`tickets` publish (Jira via MCP, GitHub `gh`, Linear, local files…), its access method, and any forbidden tool. Issues and PRs may live in different systems.
- **Branch topology** — integration vs protected release branch (workflows never merge the release branch); collapses to one branch when the repo has only `main`.
- **Versioned RD/QA commands** — separate RD unit/API-contract from QA
  integration/P0/full-suite commands; unknown capabilities remain `not-configured`.
- **QA evidence boundary** — the non-production QA environment, artifact provenance source, and
  durable evidence location used by handoffs, execution ledgers, and acceptance reports.
- **Agent role profiles** — maps work nature to host-defined profiles and records each profile's
  definition source, mode/sandbox, model, effort, write scope, MCP/plugin boundary, and no-spawn
  status. Portable requirements are shared, while Codex and Claude Code keep separate live bindings.
  Setup never creates or overrides global agents.
- **Ready/claim and deployment paths** — separates ticket eligibility from an atomic owner/session
  claim, and records how QA obtains an exact-source deployment receipt for a non-production
  environment.
- **Data-mutation safety gate** — turns on `review`'s cron/batch-write BLOCK gate when the project
  has scheduled jobs that write the database (abort guard before the write loop, sparse-input test,
  failure alerting). Off unless detected.
- **UI convention** — front-end-first mocks, if the project uses them.

## Design notes

- **Composition, not monolith.** The workflows are thin orchestration layers; each block does one
  job and is usable on its own.
- **Root owns the control plane.** `implement` keeps planning, delegation, integration, Git/tracker
  state, and final decisions in the main session. It delegates only bounded work to pre-defined
  profiles selected by task nature and independently verifies their output.
- **Evidence, not ritual.** TDD requires a RED that fails for the missing behaviour and a GREEN that
  passes at the same interface; harness or infrastructure failures do not count.
- **Blocks were chosen after auditing quality.** Weak patterns (planning that yields a monolithic
  plan instead of tickets; feasibility "review" that emits no verdict) were deliberately left out.
- **Two things are original to this pack** because nothing off-the-shelf did them: an explicit
  feasibility *verdict*, and a plain-language *acceptance report* for non-technical sign-off.

## Boundaries and limitations

- Harness Ship ships source-only plugin content. It does not run a hosted service or deployment
  environment.
- It orchestrates the host's existing tools and permissions; installing it does not create a
  security boundary or grant new credentials.
- Codex installation supplies skills only and requires a validated live independent-verifier
  profile. Claude Code installs the scoped verifier agent described above.
- Missing test, QA, deployment, or artifact capabilities remain `not-configured`; the workflows do
  not convert missing evidence into PASS.
- Setup writes only the target project's Harness Ship configuration block. This repository's local
  maintainer `AGENTS.md` is not a consumer template.

## Contributing, support, and security

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.
- Use [GitHub Issues](https://github.com/haru3613/harness-ship/issues) for reproducible bugs,
  questions, and focused feature proposals.
- Follow [SECURITY.md](SECURITY.md) for vulnerabilities. Do not include vulnerability details in a
  public issue.
- Attribution and source provenance are recorded in [NOTICE](NOTICE).

## License

MIT. See [LICENSE](LICENSE). Some blocks reimplement, in original wording, ideas popularized by
other open-source skill authors; see [NOTICE](NOTICE).
