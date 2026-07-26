# Changelog

## 0.7.0

- Migrates generated project configuration from Config v1 to Config v2 through an explicit
  review-first sequence: generate the proposed plan, review the exact diff, confirm, and only then
  apply it.
- Introduces mutually exclusive managed channels: stable `harness-ship` is bound to the attended
  release tag and `harness-ship-next` is an explicit opt-in bound to `main`.
- Adds repository-native change declarations, deterministic version-state checks, and an attended
  exact-SHA publication contract with immutable-tag mismatch protection, merge-strategy-independent
  previous-stable upgrade evidence, and provenance receipts.
