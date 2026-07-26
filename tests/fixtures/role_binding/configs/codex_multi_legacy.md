# Realistic project instructions

## harness-ship

- **Config version:** `1`
- **Agent role bindings — Codex:**

  | Work nature | Host / profile ID | Definition source | Definition digest | Mode / sandbox | Model | Effort | Write scope | Effective tools/capabilities | MCP/plugins | Fresh context | May spawn | Boundary digest |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | narrow lookup | `Codex/scout` | Codex built-in role registry + active project instructions | unsupported | read-only | `gpt-5.6-luna` | low | none | unsupported | none | true | false | unsupported |
  | `independent verification` | `Codex/verifier` | `host-registry://codex/verifier` | `sha256:bc2126dbce38e448091db5405f2a3657e310dab2f32e7b0193dcf960afa48f65` | `read-only` | `gpt-5.6-sol` | `high` | `no source edits` | `Glob, Grep, Read` | `none` | `true` | `false` | `sha256:e0fbcbb406270950bcd0a8cac58b1137241d8ce777cbc17fb5574ddb0b27325d` |
  | security review | `Codex/security_reviewer` | Codex built-in role registry + active project instructions | unsupported | read-only trust-boundary analysis | `gpt-5.6-sol` | xhigh | none | unsupported | none | true | false | unsupported |

- **Agent role bindings — Claude Code:** `not-configured`
- **Tail:** preserve exactly
