## What changed

Describe the user-visible outcome and link the issue or acceptance contract.

## Evidence

- [ ] Focused checks:
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] Plugin manifest and lifecycle checks, when applicable
- [ ] Release-sensitive paths have exactly one valid `.changes/*.json` declaration
- [ ] Version-state and post-merge dry-run checks, when applicable
- [ ] Normal changes leave generated release state unchanged, or this is a declaration-consuming
      version PR whose generated files match `release/policy.json`
- [ ] `git diff --check`

List exact commands, results, and any check that was not available.

## Review boundary

- [ ] The change is focused and its out-of-scope boundary is explicit.
- [ ] Behaviour, installation, migration, and manifest documentation are updated when affected.
- [ ] No credentials, private URLs, user data, generated caches, or unapproved third-party material
      are included.
- [ ] GitHub visibility, history rewrites, releases, and security-setting changes are not implied by
      this pull request.
- [ ] Stable and next channel changes preserve their mutual-exclusion and immutable-ref contracts.
