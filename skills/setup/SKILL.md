---
name: setup
description: >-
  Configure the small amount of project policy Harness Ship cannot safely infer when a workflow
  needs it. Empty and early repositories are valid inputs. Triggers: "/setup", "set up
  harness-ship", "configure harness-ship", "harness-ship setup", or immediately after
  `/plugin install harness-ship`.
---

# setup

Write the smallest repository config that cannot be recovered safely at the point of use. Setup is
not a framework selector, readiness gate, or repository audit. An empty repository needs no lint,
test, UI, QA, CI, deployment, or automation decision yet.

## Fast path

Read `AGENTS.md` or `CLAUDE.md` first. If it already contains exactly one supported
`## harness-ship` block and the user did not request a policy change, report that it is
configured and run `advise`. Do not rescan for policy, run a readiness command, or rewrite
informational versions.

Duplicate blocks and unsupported Config versions are zero-mutation stops. Preserve every explicit
choice in a supported existing block, including fields written later by other workflows.

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

Otherwise write the block, summarize the assumptions, and run `advise` in the same turn.

## Write

Create the section in the repository's `AGENTS.md`, or `CLAUDE.md` when that is its established
convention:

```markdown
## harness-ship

- **Plugin version:** `<version that wrote this block>`
- **Config version:** `3`
- **Issue tracker:** <system + allowed access method>
- **Code review / PR host:** <system + allowed access method>
- **Forbidden tools:** <policy | none>
- **Integration branch:** <branch>
- **Protected release branch:** <branch>
```

The plugin version is informational. Config version is the compatibility gate. If the repository
has one branch, record it for both branch fields.

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

Re-running setup changes a supported block only for an explicit policy change. Ordinary edits are
recoverable from version control; no planner, cache, digest, or migration machinery is needed.
