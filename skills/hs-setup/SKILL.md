---
name: hs-setup
description: >-
  Configure the small amount of project policy Harness Ship cannot safely infer when a workflow
  needs it. Empty and early repositories are valid inputs. Triggers: "/hs-setup", "set up
  harness-ship", "configure harness-ship", "harness-ship setup", or immediately after
  `/plugin install harness-ship`.
---

# hs-setup

Write the smallest repository config that cannot be recovered safely at the point of use. Setup is
not a framework selector, readiness gate, or repository audit. An empty repository needs no lint,
test, UI, QA, CI, deployment, or automation decision yet.

## Fast path

Read `AGENTS.md` or `CLAUDE.md` first. If it already contains exactly one supported
`## harness-ship` block and the user did not request a policy change, report that it is
configured and run `advise`. Do not rescan for policy, run a readiness command, or rewrite
informational versions. Do not add `## harness-ship-watch`, `.harness-ship/watch/`, or host
hooks on this path.

Duplicate blocks and unsupported Config versions are zero-mutation stops. Preserve every explicit
choice in a supported existing block, including fields written later by other workflows. A missing
**Test engineer watch** field means off.

## First run

Inspect local evidence once:

- repository instructions for forbidden tools;
- configured remotes and remote-tracking refs for the tracker/PR host and branch topology; and
- an existing repository convention file only when it directly identifies those policies.

Do not run tests, query for a preferred framework, or probe network services when local evidence is
enough. The absence of code or tooling is valid, not a blocker.

Ask only when either of these cannot be resolved safely:

1. the tracker and its allowed access method; or
2. the integration branch versus protected release branch.

Otherwise write the block, the standing-rules section, and any project-scoped hooks, summarize the
assumptions, and run `advise` in the same turn.

## Write

Create the section in the repository's `AGENTS.md`, or `CLAUDE.md` when that is its established
convention:

```markdown
## harness-ship

- **Plugin version:** `<version that wrote this block>`
- **Config version:** `3`
- **Test engineer watch:** `standing-rules` | `standing-rules+hooks` | `off`
- **Issue tracker:** <system + allowed access method>
- **Code review / PR host:** <system + allowed access method>
- **Forbidden tools:** <policy | none>
- **Integration branch:** <branch>
- **Protected release branch:** <branch>
```

The plugin version is informational. Config version is the compatibility gate. If the repository
has one branch, record it for both branch fields.

**Test engineer watch** is optional. Omit it on a block you are not rewriting; absence means off.
First-run default is `standing-rules`. Use `standing-rules+hooks` only after the project-scoped
hook files below exist. Do not bump Config version to record this field.

Immediately after that block, write `## harness-ship-watch` by copying
[watch/RULES.md](../../watch/RULES.md) verbatim. Claude Code, Codex, and Grok Build all load
`AGENTS.md` / `CLAUDE.md`; do not write a second host-specific copy of the rules.

Copy [watch/detect.py](../../watch/detect.py) to `.harness-ship/watch/detect.py` and
[watch/RULES.md](../../watch/RULES.md) to `.harness-ship/watch/RULES.md`. The detector is
zero-LLM and fail-open. Never spawn Claude, Codex, or Grok from a hook.

When a documented **project-scoped** hook path exists, merge the matching adapter so the same
repository works when the user switches hosts:

- Claude Code: merge [watch/adapters/claude.settings.json](../../watch/adapters/claude.settings.json)
  into `.claude/settings.json` without replacing unrelated keys.
- Codex: merge [watch/adapters/codex.hooks.json](../../watch/adapters/codex.hooks.json) into
  `.codex/hooks.json`.
- Grok Build: write [watch/adapters/grok.hooks.json](../../watch/adapters/grok.hooks.json) as
  `.grok/hooks/harness-ship-watch.json`.

If those project files already exist, merge the `Stop`, `UserPromptSubmit`, and `PostToolUse`
command that runs `python3 .harness-ship/watch/detect.py`. Do not add `SessionEnd`.
Grok `SessionEnd` stays zero-LLM.

Never write `~/.codex/hooks.json`, `~/.claude/settings.json`, or `~/.grok/hooks/` unless the
user explicitly asks for user-global hooks. If a host has no project-scoped hook path, keep
**Test engineer watch** at `standing-rules` and skip that host's adapter.

An explicit policy change may add, change, or remove **Test engineer watch**, `## harness-ship-watch`,
and the project-scoped hook files without treating Config v3 as unsupported.

## Progressive disclosure

`advise` is the default job after this block exists. Other workflows inspect capabilities
when they first need them:

- `advise` inventories the test tree and names the next cuts;
- `test-plan` records approved release criteria;
- `exploratory-testing` resolves automation only when a runnable feature justifies it;
- `testing-workflow` resolves candidate environment, evidence, and test capabilities; and
- `release-gate` consumes existing evidence without mutating release state.

Never install a framework or append its command without explicit user approval. Do not infer PASS
from a missing capability. Reviewer identity is not configured here.

Re-running `hs-setup` changes a supported block only for an explicit policy change. Ordinary edits are
recoverable from version control; no planner, cache, digest, or migration machinery is needed.
