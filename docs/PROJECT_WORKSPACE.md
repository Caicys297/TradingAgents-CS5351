# CS5351 Project Workspace

This repository starts from the official [TradingAgents](https://github.com/tauricresearch/TradingAgents) code at commit `9fa1196fffbcfd9de5146d2dd2869df84ab99838`. The baseline is third-party code; our team contributions must be identifiable in later commits and pull requests.

## Where team work goes

- `docs/req/`: requirement analysis and acceptance criteria.
- `docs/architecture/adr/`: architecture decisions and rationale.
- `docs/code-governance/`: code review and contribution records.
- `prompts/`: reusable prompts for the team's agent-assisted work.
- `transcripts/`: required session evidence, with secrets and personal data removed.
- `src/`: team-owned additions that do not belong in the existing package.
- `test/offline/`: deterministic tests that do not call paid or live services.
- `test/live/`: tests that require external services, with no credentials committed.
- `.opencode/` and `.agent/`: local agent project guidance when the team adds it.

## Team workflow

Create a branch for each change, commit the agent-generated implementation and its tests, then open a pull request for review. Keep the existing TradingAgents README and license. Record which code was inherited and which code the team added. Do not commit API keys, `.env` files, local data, or unredacted chat transcripts.
