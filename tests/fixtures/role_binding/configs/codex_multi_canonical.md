# Realistic project instructions

## harness-ship

- **Config version:** `1`
- **Agent role bindings — Codex:**

  | Work nature | Host / profile ID | Definition source | Definition digest | Mode / sandbox | Model | Effort | Write scope | Effective tools/capabilities | MCP/plugins | Fresh context | May spawn | Boundary digest |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | narrow lookup | `Codex/scout` | Codex built-in role registry + active project instructions | unsupported | read-only | `gpt-5.6-luna` | low | none | unsupported | none | true | false | unsupported |
  | "independent verification" | "Codex/verifier" | "host-registry://codex/builtin/verifier" | "sha256:75d7ee412d999f577d028419c95b2f59bf14af7813a7bb2f108b4644cac9ae26" | "read-only" | {"declared":"host-assigned-review-model","effective":"gpt-5.6-sol"} | "high" | "no source edits" | ["Glob","Grep","Read"] | [] | true | false | "sha256:f003d68999812c3ae93e33dc7078e449822cd0aeb96b6520f791eb4db4818d70" |
  | security review | `Codex/security_reviewer` | Codex built-in role registry + active project instructions | unsupported | read-only trust-boundary analysis | `gpt-5.6-sol` | xhigh | none | unsupported | none | true | false | unsupported |

- **Agent role bindings — Claude Code:** `not-configured`
- **Tail:** preserve exactly
