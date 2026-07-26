# harness-ship

**Idea → shipped, humans on the ends.** A self-contained development + testing workflow for
Codex and Claude Code. You pilot five judgment gates; AI runs everything between them.

> The core belief: assume the user has stated ~10% of what a feature needs. The AI's job is to
> surface the other 90% — not by interrogating, but by answering it with stated assumptions and
> explaining *why*, then asking only about the few forks where the answer changes the plan.
> **Automate the labour, keep the judgment.**

## What's inside

One bootstrap skill, three orchestration skills, plus eight self-contained blocks they drive. No
external plugin dependencies — everything needed is in this repo.

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
| `diagnose` | red-repro-first bug diagnosis for the QA→dev loopback |

## The five human gates

1. **Feasibility** — go / spike-first / split / no.
2. **UI 定稿** — for UI features, the design is approved before backend.
3. **Acceptance contract** — do the pre-implementation scenarios describe the right behaviour.
4. **Ticket granularity** — are the slices and dependencies right.
5. **Acceptance** — after the testing-workflow produces a plain-language acceptance report.

Never sail past a gate autonomously. Between gates, don't stall for permission.

## Install

This repository is currently private. Collaborators must authenticate GitHub HTTPS access before
either plugin manager can clone it:

```sh
gh auth login       # skip when `gh auth status` is already green
gh auth setup-git
```

If the repository becomes public, this authentication step is no longer required. Users without
access to the private repository cannot install the plugin, even when a GitHub Release exists.

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

Start a new Codex session after installing or upgrading so Codex loads the refreshed skills. Invoke
`$harness-ship:setup` once per project.

**v0.5.0 migration:** run setup once again after this upgrade so the project config records the
host's pre-defined agent role profiles. Later plugin updates do not require setup unless the stack,
tracker, branches, or host agent profiles change.

**v0.6.0 migration:** call `$harness-ship:acceptance-design` for pre-implementation scenario design.
`$harness-ship:testing-workflow` redirects legacy pre-implementation and missing-contract calls
there for this minor release and otherwise starts only after the dev→QA handoff.

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

Restart Claude Code after installing or upgrading, then run `/setup` once per project.

**v0.5.0 migration:** run setup once again after this upgrade so the project config records the
host's pre-defined agent role profiles. Later plugin updates do not require setup unless the stack,
tracker, branches, or host agent profiles change.

**v0.6.0 migration:** call `/acceptance-design` for pre-implementation scenario design.
`/testing-workflow` redirects legacy pre-implementation and missing-contract calls there for this
minor release and otherwise starts only after the dev→QA handoff.

`setup` detects your stack, issue tracker, branch topology and test commands, asks only the few
forks it can't infer, and writes a `## harness-ship` config block into your `AGENTS.md` (or
`CLAUDE.md`). Every workflow reads that block, so nothing runs on generic guesses.

Then invoke the platform's `dev-workflow`, `acceptance-design`, `implement`, `tdd`, or
`testing-workflow` skill — or just describe a feature and the skills trigger themselves. Re-run
`setup` any time the stack, tracker, branches, or host agent profiles change.

## What `setup` configures

- **Issue tracker** — where `spec`/`tickets` publish (Jira via MCP, GitHub `gh`, Linear, local files…), its access method, and any forbidden tool. Issues and PRs may live in different systems.
- **Branch topology** — integration vs protected release branch (workflows never merge the release branch); collapses to one branch when the repo has only `main`.
- **Test / lint / typecheck / build commands** — per your stack.
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

## License

MIT. See `LICENSE`. Some blocks reimplement, in original wording, ideas popularized by other
open-source skill authors — see `NOTICE`.
