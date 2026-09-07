<!-- harness-ship:testing:<candidate-key> -->
# Testing — <feature / release>

**<Passed | Failed | Incomplete>** — <one user-facing reason>

Optional outline for one PR/issue or session summary. Omit sections that do not help this task.
No separate handoff, ledger, report, or contract is required.

- **What changed:** <user-visible behaviour and current scope>
- **Candidate/environment:** <source SHA or actual external build ID, artifact and safe surface>
- **How to reach it:** <entry point and safe fixtures, if someone else must test>
- **Checks planned:** <expected outcomes, negative/permission cases, relevant risks>

| Behaviour | Command / steps | Result | Evidence |
|---|---|---|---|
| <journey or risk> | <automated/manual/exploratory method> | <PASS/FAIL/FLAKY/BLOCKED/NOT TESTED> | <link or concise output> |

- **Reused evidence:** <original identity, equivalence rationale, limits>
- **Remaining risks / not tested:** <user impact and reason>
- **Next action:** <repair, focused check, release assessment, or human decision>

Preserve failed attempts and distinguish a repaired retest from a flaky rerun. Keep secrets,
credentials, raw tokens, fixture PII, and full logs out of public comments.
