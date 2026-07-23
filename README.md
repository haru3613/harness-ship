# harness-ship

**Idea → shipped, humans on the ends.** A self-contained development + testing workflow for
Claude Code. You pilot four judgment gates; AI runs everything between them.

> The core belief: assume the user has stated ~10% of what a feature needs. The AI's job is to
> surface the other 90% — not by interrogating, but by answering it with stated assumptions and
> explaining *why*, then asking only about the few forks where the answer changes the plan.
> **Automate the labour, keep the judgment.**

## What's inside

Two orchestration skills, plus the six self-contained blocks they drive. No external plugin
dependencies — everything needed is in this repo.

| Skill | Role |
|---|---|
| **`setup`** | one-time: detect the project's stack/tracker/branches and write the config the workflows read |
| **`dev-workflow`** | idea → clarify → feasibility → spec → tickets → implement → QA handoff |
| **`testing-workflow`** | journeys → tests (RD unit+contract / QA integration+E2E) → gate → acceptance report |
| `clarify` | bounded requirement clarification — only load-bearing questions, defaults become assumptions |
| `spike` | time-boxed throwaway prototype that returns a feasible / not / needs-more verdict |
| `spec` | synthesize the conversation into a spec/PRD at the highest test seam |
| `tickets` | break a spec into vertical-slice tracer-bullet tickets with blocking edges + per-ticket AC |
| `review` | dual-axis code review (Standards × Spec) with an optional data-mutation safety gate |
| `diagnose` | red-repro-first bug diagnosis for the QA→dev loopback |

## The four human gates

1. **Feasibility** — go / spike-first / split / no.
2. **Ticket granularity** — are the slices and dependencies right.
3. **UI 定稿** — for UI features, the design is approved before backend.
4. **Acceptance** — after the testing-workflow produces a plain-language acceptance report.

Never sail past a gate autonomously. Between gates, don't stall for permission.

## Install

```
/plugin marketplace add haru3613/harness-ship
/plugin install harness-ship
/setup                          # once per project — configures the workflows for your repo
```

`setup` detects your stack, issue tracker, branch topology and test commands, asks only the few
forks it can't infer, and writes a `## harness-ship` config block into your `AGENTS.md` (or
`CLAUDE.md`). Every workflow reads that block, so nothing runs on generic guesses.

Then invoke `/dev-workflow <your idea>` or `/testing-workflow` — or just describe a feature and the
skills trigger themselves. Re-run `/setup` any time the stack, tracker, or branches change.

## What `setup` configures

- **Issue tracker** — where `spec`/`tickets` publish (Jira via MCP, GitHub `gh`, Linear, local files…), its access method, and any forbidden tool. Issues and PRs may live in different systems.
- **Branch topology** — integration vs protected release branch (workflows never merge the release branch); collapses to one branch when the repo has only `main`.
- **Test / lint / typecheck commands** — per your stack.
- **Data-mutation safety gate** — turns on `review`'s cron/batch-write BLOCK gate when the project
  has scheduled jobs that write the database (abort guard before the write loop, sparse-input test,
  failure alerting). Off unless detected.
- **UI convention** — front-end-first mocks, if the project uses them.

## Design notes

- **Composition, not monolith.** The workflows are thin orchestration layers; each block does one
  job and is usable on its own.
- **Blocks were chosen after auditing quality.** Weak patterns (planning that yields a monolithic
  plan instead of tickets; feasibility "review" that emits no verdict) were deliberately left out.
- **Two things are original to this pack** because nothing off-the-shelf did them: an explicit
  feasibility *verdict*, and a plain-language *acceptance report* for non-technical sign-off.

## License

MIT. See `LICENSE`. Some blocks reimplement, in original wording, ideas popularized by other
open-source skill authors — see `NOTICE`.
