# Bug diary

This short diary records observed defects and corrections. It is not a measured defect-rate series.

| Finding | What was corrected or decided | Source |
| --- | --- | --- |
| O2 trace link | TC-17 was mapped to the wrong failure requirement. B corrected the registry reference and revalidated the requirement file. | [PR #50](https://github.com/Caicys297/TradingAgents-CS5351/pull/50), [requirements](req/requirements.yaml) |
| O4 early publication risk | A checker-only result was insufficient because a CLI stream could expose the proposed rating before the effective gate result. Publication-boundary tests and shared integration addressed that path. | [PR #27](https://github.com/Caicys297/TradingAgents-CS5351/pull/27), [O4 integration mapping](ci/O4-Semantic-Integration-Mapping.md) |
| O5 S5 evidence gate | `test approval` and `ai-use log` failed on earlier #40 commits. The team supplied real evidence and checked the gate again on later commits before merge. | [PR #40](https://github.com/Caicys297/TradingAgents-CS5351/pull/40), [PR #42](https://github.com/Caicys297/TradingAgents-CS5351/pull/42) |
| O5 S6 threshold | A later p95 measurement was 114.376 ms against the 100 ms target. The team stopped S6 and did not merge #33. | [PR #33](https://github.com/Caicys297/TradingAgents-CS5351/pull/33), [Report](../Report.md) |
| C handoff prose | #49 initially described an interactive command as unattended and used historical commit wording for a replacement PR. Both descriptions were corrected without changing the export. | [PR #49](https://github.com/Caicys297/TradingAgents-CS5351/pull/49) |

The deliberately broken Schema on [trial PR #41](https://github.com/Caicys297/TradingAgents-CS5351/pull/41) was a controlled gate experiment, not a product defect.
