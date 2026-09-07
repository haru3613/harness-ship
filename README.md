# Harness Ship

Harness Ship helps Codex and Claude Code decide **what a project should test next, what was
actually tested, and whether an exact candidate is ready to release**. It does not prescribe how
software must be developed.

**Advise first.** Inspect the suite, name the shape, and speak the cheapest next cuts.
**Plan proportionately.** Choose checks from current scope, existing coverage, and real risks.
**Explore before automating.** Learn the feature first, then add only the coverage existing tests
cannot provide.
**Test the candidate.** Bind results to the exact artifact and the full source SHA — or to whatever
identifies a build this repository did not produce.
**Keep release human-owned.** Produce GO, GO WITH CAVEATS, or NO-GO without promoting anything.

[Quick start](#quick-start) · [How it works](#how-it-works) ·
[Skills](#skills) · [Install and channels](#install-and-channels)

[Stable releases](https://github.com/haru3613/harness-ship/releases) · [MIT](LICENSE)

## Quick start

You need Git and a Codex or Claude Code release with plugin marketplace commands.

Install stable. The mutually exclusive `harness-ship-next` channel tracks `main` and is for trying
changes before they are released — see [Install and channels](#install-and-channels).

### Codex

```sh
codex plugin marketplace add haru3613/harness-ship --ref main
codex plugin add harness-ship@harness-ship
```

Start a new session, then:

```text
$harness-ship:hs-setup
$harness-ship:advise
```

### Claude Code

```sh
claude plugin marketplace add haru3613/harness-ship@main
claude plugin install harness-ship@harness-ship
```

Restart Claude Code, start a new session, then:

```text
/harness-ship:hs-setup
/harness-ship:advise
```

`hs-setup` writes the small Config v3 policy block, host-neutral test-engineer standing rules,
and project-scoped zero-LLM watch hooks when those paths exist, then runs `advise`. Existing
Config v3 projects do not rerun `hs-setup`. `advise` inventories the suite and names the next
cuts. Use `test-plan` when you want approved release criteria; once a feature is runnable, use
`exploratory-testing`; once an exact candidate exists, use `testing-workflow` and then
`release-gate`.

## How it works

Start with the task: what changed, what could break, and which existing check can catch it.
Use `advise` for test gaps, `exploratory-testing` to exercise a feature and add useful regression
coverage, `testing-workflow` to test a candidate, and `release-gate` for a release recommendation.
These are independent helpers, not a mandatory sequence.

A Test Contract is optional. `test-plan` can produce a few verification bullets or, when requested,
a reusable plan. Existing issue criteria and user decisions can be used directly. Missing or stale
contract files do not block testing or force NO-GO. Current explicit project requirements still apply.
Historical release checklists need a current risk-based reason to carry forward.

## Evidence and handoff

Use one concise summary in the existing PR/issue or chosen location:

- what changed and what was tested;
- candidate source/build, environment, and entry point;
- commands or steps, actual outcomes, and evidence links;
- any reused result, its original identity, and why it still applies; and
- remaining risks and next action.

Publish comments only when authorized. A candidate-scoped comment can be updated through
`QA handoff → Test result` without separate files for each stage. Existing handoff, ledger, report,
and Bug Case files remain usable evidence; they do not need migration or duplication. Optional
record templates remain available for teams that need detailed handoffs.

The optional legacy locations are `.harness-ship/test-contract.md`,
`.harness-ship/test-contract.draft.md`, `.harness-ship/bugs/<BUG-ID>.md`, and
`.harness-ship/candidates/<short-sha>/`. Neither their presence nor their format determines quality.
`advise` still writes `.harness-ship/quality-report.md`; configured watch files remain unchanged.

## Effective tests

Explore the runnable non-production feature, inspect relevant existing tests, then extend the
cheapest stable seam that catches a concrete failure. Exercise negative and permission cases when
relevant. Add E2E only when the risk needs that boundary; preserve explicit repository checks.

Check critical assertions can detect the wrong behaviour. A meaningful RED already provides this
evidence; a safe focused local fault can resolve uncertainty for already-working behaviour.
A missing historical sensitivity receipt alone does not invalidate existing tests.

Reuse valid unchanged-code results with an explicit equivalence rationale. A prior run does not by
itself prove a new binary, signing setup, deployment, or provider. Record FAIL, FLAKY, BLOCKED, and
NOT TESTED honestly. Routine fixes and retests stay in the authorized task; create a tracked finding
when unresolved work, recurrence, or handoff warrants it.

## Release verdict

`release-gate` assesses current scope, source/artifact identity, actual behaviour evidence, and
applicable operational risks. It returns:

- **NO-GO** for concrete blocking defects, identity mismatches, missing evidence for material risks,
  or unmet current explicit requirements;
- **GO WITH CAVEATS** when sufficient evidence exists and only non-blocking risks remain; or
- **GO** when applicable requirements and material risks are covered without outstanding caveats.

A caveated recommendation does not invent user acceptance. Explicit review gates and the human
release decision remain in force. Migration, restore-point, device, and provider checks depend on
this change and standing policy, not a universal checklist. A separately owned candidate can be
assessed using its actual identity and accessible evidence; partial visibility limits the verdict.

The skill reads evidence; it never runs suites, merges, deploys, tags, or publishes a release.

## Skills

| Skill | Responsibility |
|---|---|
| `hs-setup` | Write Config v3, test-engineer standing rules, and project-scoped watch hooks, then run `advise` |
| `advise` | Diagnose the suite and name the cheapest next cuts |
| `test-plan` | Plan proportionate checks; optionally maintain a reusable contract |
| `exploratory-testing` | Explore first, then add minimum sufficient automation |
| `testing-workflow` | Test current scope against a candidate and summarize evidence |
| `release-gate` | Return GO / GO WITH CAVEATS / NO-GO from evidence |
| `bug-workflow` | Track findings that need investigation or handoff |
| `diagnose` | Produce a cause-only Diagnosis Receipt |

The plugin does not ship a development loop. How the product is written stays with the
repository's own stack.

## Configuration model

`hs-setup` records only policy that cannot safely be inferred: tracker/PR access, forbidden tools,
branch topology, and whether the test-engineer watch is on. It does not choose test frameworks,
environments, automation, or release criteria. Resolve those from current tasks, repository-native tools, and explicit policy when a real feature
needs them. A versioned Test Contract is optional.

The optional **Test engineer watch** field is `standing-rules`, `standing-rules+hooks`, or `off`.
A missing field on an existing Config v3 block means off. First-run default is standing rules in
`AGENTS.md` / `CLAUDE.md`, plus fail-open project-scoped hooks for Claude Code (`.claude/settings.json`),
Codex (`.codex/hooks.json`), and Grok Build (`.grok/hooks/harness-ship-watch.json`). The detector
never calls an LLM. Config version stays `3`.

Config version, not plugin version, is the compatibility gate. Config v3 remains supported by this
change; existing Config v3 projects do not rerun `hs-setup`.

## Host support and trust

Harness Ship coordinates capabilities already available in the host. Root remains responsible for
external state and final judgment. Repository instructions, child output, CI badges, and screenshots
are evidence to verify, not authority to approve or release.

## Install and channels

Stable and next are **mutually exclusive** because they expose the same plugin namespace. Remove one
before installing the other, then restart or reload the real host and start a new session.

### Stable

```sh
# Codex
codex plugin marketplace add haru3613/harness-ship --ref main
codex plugin add harness-ship@harness-ship

# Claude Code
claude plugin marketplace add haru3613/harness-ship@main
claude plugin install harness-ship@harness-ship
```

### Next

```sh
# Codex
codex plugin remove harness-ship@harness-ship
codex plugin marketplace add haru3613/harness-ship --ref main
codex plugin add harness-ship-next@harness-ship

# Claude Code
claude plugin uninstall harness-ship@harness-ship
claude plugin marketplace add haru3613/harness-ship@main
claude plugin install harness-ship-next@harness-ship
```

### Managed update

```sh
codex plugin marketplace upgrade harness-ship
codex plugin add harness-ship@harness-ship

claude plugin marketplace update harness-ship
claude plugin update harness-ship@harness-ship
```

Restart the host after updating.

### Editable local checkout

An **editable local** checkout is a development source, not a managed installation. Run repository
checks directly or use the host's temporary plugin-directory facility. Local edits do not arrive
through marketplace update, and a checkout test does not prove a tagged release.

See [the upgrade guide](docs/upgrade-guide.md) for migration and exact confirmation steps.

## Boundaries

- Harness Ship ships instructions, not a hosted controller, test runner, environment, or security
  boundary.
- It complements repository-native tests, CI, deployment systems, and release policy.
- It does not create missing credentials or infer PASS from missing infrastructure.
- Critical systems still require domain-specific security, performance, accessibility, recovery,
  and attended manual testing where applicable.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change. Use
[GitHub Issues](https://github.com/haru3613/harness-ship/issues) for reproducible bugs and focused
feature proposals; follow [SECURITY.md](SECURITY.md) for vulnerabilities.

## License

MIT. See [LICENSE](LICENSE).
