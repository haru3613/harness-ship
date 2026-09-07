# Optional execution detail — <candidate>

Use for a long or multi-person run when a short summary is insufficient. Preserve attempts in the
chosen location; neither this file nor a contract revision is required for testing.

| Candidate / environment | Behaviour | Command / steps | Attempt / result | Evidence |
|---|---|---|---|---|
| <source/build and safe surface> | <expected/forbidden outcome> | <method> | <PASS/FAIL/FLAKY/BLOCKED/NOT TESTED> | <link/output> |

Record source/environment changes before retesting. Preserve failures; retry-green under unchanged
conditions is flaky. Missing infrastructure or unexecuted checks never count as PASS.
