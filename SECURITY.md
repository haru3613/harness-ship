# Security policy

## Reporting a vulnerability

Do not disclose vulnerability details in a public issue, pull request, discussion, or chat.

After this repository becomes public, use GitHub's
[private vulnerability reporting](https://github.com/haru3613/harness-ship/security/advisories/new).
Public visibility is blocked until the maintainer has enabled that feature and verified the
`Report a vulnerability` path from a non-maintainer account.

While the repository remains private, current collaborators may create a private draft repository
security advisory. Anyone without access should open an issue that asks for a private contact
channel without including technical details.

Include the affected version or commit, impact, reproduction conditions, and suggested mitigation
when known. Do not include live credentials or private user data.

## Scope and response

Security-sensitive areas include plugin installation and upgrade, role/profile binding,
permissions, repository or tracker mutation, secret handling, and trust of child-agent or command
output.

Only the latest release and current `main` are assessed for fixes. This is a response target, not a
guaranteed support window. The maintainer will acknowledge receipt through the private GitHub
advisory, validate impact, coordinate a fix and disclosure when appropriate, and credit the
reporter unless anonymity is requested.
