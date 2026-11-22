# MCP tool manifest

This is the team's allowed-purpose list for coding sessions. It does not assert that every tool is installed or technically blocked when absent. Check the actual session/tool configuration before use.

| Tool or access | Roles allowed to request it | Allowed purpose and boundary |
| --- | --- | --- |
| Local file reader/editor | Scoped feature agent, after human plan approval | Only exact task-whitelisted repository paths; no secrets or personal files |
| Local terminal, Git | Scoped feature agent and verification agent | Inspect branch/diff and run approved checks; no force push or unapproved history changes |
| Local tests and static checks | Scoped feature agent and verification agent | Run approved tests; report exact command, result, and SHA |
| GitHub PR and CI view | Human reviewers; agent may inspect public PR evidence when scoped | Human owns approval and merge; no agent self-approval or bypass |
| OpenCode session export | Human operator | Preserve original transcript and mark interventions; disclose genuine publication redactions |
| External search, network APIs, MCP services | No default role | Require the task plan to name the service, data, and reason; never send secrets or private transcripts |

No project-specific MCP server is required by the selected feature registry. If one is used, add its actual server name, scope, credentials source (without values), and evidence to the approved plan before use.
