# Contributing to Harness Ship

Thanks for helping improve Harness Ship. Small, evidence-backed changes are easiest to review.

## Before opening a pull request

1. Search existing issues and pull requests.
2. Open an issue before a large behaviour change. Describe the user-visible outcome, acceptance
   boundary, and what is explicitly out of scope.
3. Do not include credentials, private URLs, user data, proprietary fixtures, or generated plugin
   caches.

The repository's maintainer claim receipts and local `AGENTS.md` bindings govern trusted maintainer
automation. External contributors do not impersonate that owner or copy those bindings. Consumer
projects should run Harness Ship `setup` to generate their own `AGENTS.md` or `CLAUDE.md` config.

## Development

Create a feature branch from the current `main`. Maintainer-created worktrees live at
`.worktrees/<task-slug>`; contributors working in forks may use their normal Git workflow.

The project has no dependency-install step. It requires Python 3 and `jq` for the configured
contract and manifest checks.

Every normal release-sensitive source change also needs exactly one strict JSON declaration under `.changes/`.
Declare the changed paths, `patch`/`minor`/`breaking` classification, migration impact, and a short
summary. Duplicate, malformed, uncovered, unchanged, or underclassified declarations fail closed.
Normal change PRs do not bump versions or edit generated release state. A separate version PR
consumes every pending declaration, generates the exact maximum implied bump, catalogs, changelog,
and `release/policy.json` ledger entry. Consumed declaration IDs can never become pending again.

Run the contract suite:

```sh
python3 -m unittest discover -s tests -v
```

Check a change PR against its base:

```sh
python3 scripts/check_release_contract.py pr HEAD^ HEAD
python3 scripts/check_release_contract.py version-state check --ref HEAD
```

To prepare a version PR from a base that has pending declarations:

```sh
python3 scripts/check_release_contract.py version-state generate --base-ref HEAD
python3 scripts/check_release_contract.py version-pr HEAD <generated-commit>
```

Validate the plugin manifests:

```sh
jq empty \
  .codex-plugin/plugin.json \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  .agents/plugins/marketplace.json
```

Validate the current plugin lifecycle against the previous revision:

```sh
bash scripts/validate_plugin_lifecycle.sh HEAD^ HEAD
```

Also run `git diff --check`. The GitHub Actions workflow repeats the contract, manifest, lifecycle,
and whitespace checks.

## Change expectations

- Keep each pull request focused on one issue or acceptance boundary.
- Update tests when observable workflow behaviour changes.
- Keep `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` versions aligned.
- Update marketplace descriptions, README commands, migration notes, and lifecycle fixtures when a
  plugin surface changes.
- Preserve root-owned orchestration, exact-SHA evidence, human judgment gates, and fail-closed
  handling of missing capabilities.
- Explain commands run, results, risks, and any checks that were not available.

Pull requests are reviewed but merged by a maintainer. A green check does not authorize an
automatic merge, tag, GitHub release, or repository visibility change. Publication is a separate,
attended `workflow_dispatch` action against the intended full merged `main` SHA. The publication
preflight selects the highest reachable earlier strict-semver stable tag whose Codex and Claude
manifests match that tag, records its exact SHA, and runs the upgrade lifecycle from that release.
It does not infer the upgrade base from the candidate's immediate parent, so squash, merge-commit,
and rebase histories do not change the release evidence.
