# Realistic project instructions

## harness-ship

- **Config version:** `1`
- **Agent role bindings — Codex:**

  | Work nature | Host / profile ID | Definition source | Definition digest | Mode / sandbox | Model | Effort | Write scope | Effective tools/capabilities | MCP/plugins | Fresh context | May spawn | Boundary digest |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | narrow lookup | `Codex/scout` | Codex built-in role registry + active project instructions | unsupported | read-only | `gpt-5.6-luna` | low | none | unsupported | none | true | false | unsupported |
  | `independent verification` | `Codex/verifier` | `host-registry://codex/verifier` | `sha256:d9e9aeb32de4f4009b3ac454a5f3debb5219c7020f5c779941e990a45f667cad` | `read-only` | `host-assigned-review-model` | `high` | `no source edits` | `Glob, Grep, Read` | `none` | `true` | `false` | `sha256:becd907e7cdbaa612a7dff70192df9cea2d7691158ec7c27a0517c864c195563` |
  | security review | `Codex/security_reviewer` | Codex built-in role registry + active project instructions | unsupported | read-only trust-boundary analysis | `gpt-5.6-sol` | xhigh | none | unsupported | none | true | false | unsupported |

- **Agent role bindings — Claude Code:** `not-configured`
- **Tail:** preserve exactly
