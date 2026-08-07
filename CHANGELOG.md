# Changelog

## 5.1.0

- [external-release-surface] Name the repository that holds release criteria for a service another team builds and releases, give its contract fields for the release-surface owner, what this repository can see of that owner, and the candidate identifier, and route those through the interview. Make release-gate stop before evaluating with NO-GO whose reason is that the verdict belongs to the repository owning the candidate, list that reason in the verdict rules, and reconcile gate 1 so an external surface is not reported as contract drift. Generalize the candidate directory name to the contract-defined identifier while keeping per-candidate uniqueness, and forbid recording this repository's own HEAD as a candidate's source SHA when the owner exposes none. (classification: minor; migration: none).
- [mutation-sensitivity-evidence] Classify a P0 scenario automated only once something showed its test failing for the reason the row names: a RED watched fail already is that evidence, and where no honest RED exists — coverage for behaviour that already ships, or characterization for a refactor — tdd injects the row's forbidden state in one line against a local working copy, runs the new test and the nearest existing tests, and reverts with the revert confirmed. Existing tests reddening too means the risk was already covered; the new test surviving means it catches nothing. Until the receipt exists the row is not-configured on the accurate ground that the capability to prove it is unestablished, cited in Reason rather than in the per-candidate evidence column. exploratory-testing states it cannot produce this and routes to tdd. Binds on coverage added or changed from here, not retroactively. (classification: minor; migration: recommended).
- [pointer-contract-fidelity] Make a document qualify as the Test Contract only on scenario detail that resolves tracked in the repository, so an unresolvable delegation becomes a recorded gap instead of inherited coverage; give a pointer a Carried here field for operational criteria the document never held, sourced from the interview rather than inspection; judge qualification per document so an unaccepted sibling is named as excluded scope that release-gate reports rather than gates; and teach release-gate to read both fields and audit each named document's own check. Also clarify that the draft path governs the pointer form, that a structured question tool may batch questions that are each one topic, and that a first run has no prior Bug Cases to mine. (classification: minor; migration: none).
- [seam-runnability] Ask of every scenario whether a seam that would catch a failure the used one is structurally blind to was passed over because this environment cannot run it — better meaning reach, not realism, so a more faithful seam proving the same thing is not better. Record those in a Seam runnability table naming what the used seam cannot see, with an owner; a row whose used seam reaches nothing its forbidden clause names stays not-configured and blocks. release-gate reports the rows without moving the verdict, since approving the contract accepted them and a project should not become permanently ungateable for admitting where its evidence is thin. Also direct defect-history mining to check whether each fix landed everywhere its mechanism reaches, and give an untouched sibling path a scenario row rather than a prior-failure row. (classification: minor; migration: none).
- [testing-workflow-contract-inputs] Give the pointer Test Contract a stable ID and revision and state that the revision rule governs both forms, including that a pointer's revision moves when a document it names changes semantically. Teach testing-workflow that contract-derived handoff values come from the Project Test Baseline and Release Delta for a two-layer contract and from the named documents plus Carried here for a pointer, and that a value neither supplies is Not ready rather than a licence to infer an environment. Accept the contract's Candidate identifier wherever a full source SHA is required, and only where its Release surface owner is not this repository, across the handoff, ledger, report, Bug Case, exploratory session, the candidate directory name, and the provenance binding method; forbid substituting this repository's own HEAD. (classification: minor; migration: none).
- [unattended-test-plan] Give test-plan a defined terminal state when the session has no user to ask. One round of real answers is unsatisfiable and drafting from inspection alone is forbidden, and between those two rules there was no exit, so the reachable behaviour was to abandon the workflow and write tests with the inspection thrown away. It now stops without writing when a draft already exists, so a scheduled run cannot overwrite an attended revision awaiting approval; otherwise it does the work that needs no answer, writes the DRAFT with an empty scenario table, and records each unasked interview topic, how it established there was nobody to ask, and any scenario it could propose but not complete. That draft is never presented for approval — approval replaces the approved contract wholesale, so approving a scenario-less draft would delete every scenario the project agreed to — and is finished by a later session that runs the interview in the same file. (classification: minor; migration: none).

## 5.0.0

- [contract-audit] Make release-gate re-resolve what each required and P0 automated row cites as its seam at the candidate SHA before trusting the contract, so a citation that no longer exists makes the row unevaluated instead of silently passing, and require automated seams to be written as resolvable citations rather than a layer name so that check has something to resolve. (classification: minor; migration: none).
- [existing-contract-pointer] Let a project whose release criteria already live in an accepted document keep that document as its Test Contract, with .harness-ship/test-contract.md as a pointer that must name what the two-layer model carries and the document does not, so a mature project is not made to restate working criteria into a weaker parallel copy that immediately drifts. (classification: minor; migration: none).
- [record-paths] Give every Harness Ship record a fixed home under .harness-ship/ instead of leaving it a portable template with no address, so release-gate can locate an approved contract, a provenance receipt, and an append-only ledger from a cold start rather than requiring the user to paste them into the session. (classification: breaking; migration: required).
- [scenario-craft] Teach the craft the contract's shape assumes: how to cut journeys so their IDs outlive the UI, and how to write the forbidden half as one of the four ways a system goes wrong while still appearing to work, plus a readiness check that rejects a row whose seam cannot reach its own forbidden clause. Also connect exploratory-testing to the behaviour-first test and dependency-replacement references, which were reachable only through the user-invoked tdd workflow even though exploratory-testing is the skill that writes the tests. (classification: minor; migration: none).
- [test-plan-interview] Require test-plan to complete a round of real user answers before drafting any scenario table, naming what inspection cannot reach — P0 priority, what counts as money or irreversible state, forbidden behaviour, whether an existing red or skipped test is accepted or forgotten, acceptable deferrals, and the release target — instead of generating a full baseline from inspection and asking for one blanket approval. (classification: minor; migration: none).

## 4.2.0

- [issue-74-75] Direct test-plan to mine prior failure evidence when auditing an existing project, and add a portable Test Contract template. (classification: minor; migration: none).
- [issue-76] Require a diagnosed root cause to establish its reach across every caller, and carry that reach into the bug-workflow repair handoff. (classification: minor; migration: none).

## 4.1.0

- [dev-helpers-command-only] Make the seven development helpers user-invoked only in both harnesses so no agent selects them over the repository's own development stack; type /harness-ship:<name> (Codex $harness-ship:<name>) to run them. (classification: minor; migration: recommended).

## 4.0.0

- [issue-68] Replace mandatory development orchestration with test planning, exploratory automation, exact-candidate testing, and a read-only release gate. (classification: breaking; migration: required).

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
