# Debt register

These are accepted limits at closeout, not promises of completed work.

| Item | Current limit | Follow-up trigger and source |
| --- | --- | --- |
| O3 model usage | Bounded character context was tested; lower provider token usage or better advice was not established. | Measure with provider usage on fixed inputs if O3 is extended. [Architecture trace matrix](architecture/trace-matrix.md), [PR #14](https://github.com/Caicys297/TradingAgents-CS5351/pull/14) |
| O5 branch coverage | The reported real CLI probe covered the `V-LIMIT-ZERO` path, not every provider/news path. | Add separately scoped probes before claiming wider live behavior. [PR #40](https://github.com/Caicys297/TradingAgents-CS5351/pull/40) |
| Protection trial E3 | E3 was not executed in the final six-gate handoff. | Run a separate trial only if this behavior becomes an acceptance requirement. [F's CI summary](ci/F-Final-Test-and-CI-Summary.md), [PR #41](https://github.com/Caicys297/TradingAgents-CS5351/pull/41) |
| O5 S6 performance | The later measured p95 exceeded the 100 ms target; S6 was stopped and its PR was closed unmerged. | A new reviewed scope and passing measurement would be needed to restart. [PR #33](https://github.com/Caicys297/TradingAgents-CS5351/pull/33), [Report](../Report.md) |
| Local agent permissions | The permission matrix documents approved scopes; it is not proof of operating-system or OpenCode enforcement. | Verify a runtime enforcement mechanism before claiming one. [Permission model](architecture/permission-model.md), [verification constraints](code-governance/verification-constraints.md) |
