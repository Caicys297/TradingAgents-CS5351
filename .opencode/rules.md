# Project rules for OpenCode

This file is maintained by human team members. The coding agent may read it and suggest changes in a plan, but must not edit it during a feature task.

1. Start with `AGENTS.md` and `Prompt.md`. Follow the selected requirement registry and the approved task-specific plan; historical drafts are not a replacement.
2. Plan before code. Human approval must bind the actual plan version, test IDs, file scope, and time before the first implementation edit. Record later clarifications as later events.
3. Read and write only files named by the approved task scope. Default for any unlisted path is no read and no write. Ask a human to widen scope before accessing it.
4. Never access secrets, personal files, private transcripts, or credentials. Never send repository content to an unapproved external tool or service.
5. Preserve public interfaces and safety boundaries. On uncertainty or an unsafe failure, stop and report the issue; do not silently claim success.
6. Report actual commands, results, and commit SHA. Keep the raw session and human interventions; redact only genuine secrets or private data for publication and disclose any redaction.

These instructions are a human process rule. Repository files alone do not install an OpenCode filesystem sandbox.
