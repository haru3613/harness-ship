# Changelog

## 3.0.0

- [issue-65] Make setup a fast policy-only step and defer optional test-framework choices to the workflow that needs them. (classification: breaking; migration: required).

## 2.0.0

- [issue-60] Redesign the README around first-time positioning, activation, proof, and a legible delivery overview. (classification: patch; migration: none).
- [issue-62] Remove mandatory TDD commit receipts and assertion-ratio fake-green gates. (classification: breaking; migration: required).

## 1.1.0

- [issue-57] Resolve fresh reviewers from the running host instead of requiring a preconfigured verifier profile. (classification: minor; migration: none).
- [post-v1-0-0-pins] Point the stable channel documentation at the published v1.0.0 tag and describe the current fail-closed Config stop instead of the removed v1 to v2 migration. (classification: patch; migration: none).

## 1.0.0

- [issue-27-release-identity] Provide an explicit tagger identity to the attended release publisher. (classification: patch; migration: none).
- [issue-34] Replace the verifier binding fortress with a boundary gate and a one-line binding. (classification: breaking; migration: required).
- [issue-35] Bind the TDD receipt's RED claim to a committed failing state that root can verify. (classification: minor; migration: recommended).
- [issue-36] Recompute the anti-fake-green verdict from an enumerated assertion audit in the ledger. (classification: minor; migration: recommended).
- [issue-37] Defer later-tier config to its point of use and report planning/implementation/QA readiness separately. (classification: minor; migration: recommended).
- [issue-38] Gate on the Config version only; the plugin version becomes informational. (classification: breaking; migration: required).
- [issue-39] Move implement's multi-root claim machinery and defect-repair entry into opt-in references. (classification: minor; migration: none).
- [issue-47] An explained not-configured value is still unset in the readiness gate. (classification: patch; migration: none).
- [issue-50] Resolve the independent verifier from the running host and stop persisting it in project config. (classification: breaking; migration: recommended).
- [issue-52] Give the Standards axis a named smell baseline and bound each axis brief. (classification: minor; migration: none).
- [release-1-0-0-docs] Name the pending breaking release v1.0.0, mirror its migration note for Claude Code, and read the asserted version from the release policy ledger. (classification: patch; migration: none).

## 0.7.0

- Migrates generated project configuration from Config v1 to Config v2 through an explicit
  review-first sequence: generate the proposed plan, review the exact diff, confirm, and only then
  apply it.
- Introduces mutually exclusive managed channels: stable `harness-ship` is bound to the attended
  release tag and `harness-ship-next` is an explicit opt-in bound to `main`.
- Adds repository-native change declarations, deterministic version-state checks, and an attended
  exact-SHA publication contract with immutable-tag mismatch protection, merge-strategy-independent
  previous-stable upgrade evidence, and provenance receipts.
- Rejects untrusted marketplace origins, duplicate-key release JSON, writable Config targets,
  non-durable lock cleanup, and draft/prerelease state masquerading as a stable release.
