# F — original native OpenCode session exports

Owner: F (`fancx777`). Export date: 2026-11-23. This documentation delivery is based on `main@2eb77a4188954f5f671f924dbebca7294738c13f` and adds only missing F session evidence and the test/CI summary. The already merged application, tests and workflows are unchanged.

## Original exports

Each JSON file was copied **byte-for-byte** from the local output of `opencode export <sessionID> --pure`. No redaction, formatting change, message selection, role/attribution rewriting or inline annotation was applied. Machine paths, email addresses, tool names, timestamps, tool inputs/outputs and native compaction records remain as exported. The owner explicitly requested the original files rather than publication-redacted copies. A known-credential-format scan found no matches; this is not a guarantee of absence of all sensitive information.

| File | Session ID | Messages | User / assistant |
| --- | --- | ---: | ---: |
| [CI_Gate.json](CI_Gate.json) | `ses_e27f33c94ffeOKeCXPrAQQW93Z` | 1997 | 156 / 1841 |
| [CI_Six_Gates.json](CI_Six_Gates.json) | `ses_e008a12afffeF1VypDhIPQYQBc` | 202 | 20 / 182 |
| [CI_Test_Approval.json](CI_Test_Approval.json) | `ses_e00d872f7ffe13z09Dg34QBWSc` | 163 | 7 / 156 |
| [CS5351_O6.json](CS5351_O6.json) | `ses_e2d9653d0ffeYFgcWPdRM7FFUZ` | 411 | 51 / 360 |
| [O6_batch1.json](O6_batch1.json) | `ses_e1b0938ceffekagmwTfRtJ6NhK` | 894 | 91 / 803 |

## Separate student notes

- [Intervention annotations](F_Intervention_Annotations.md): 14 actual user interventions, reasons, directions and observed results. Each links to the original user message ID and JSON line. Annotations are outside the native transcripts.
- [Supervised workflow index](F_Supervised_Workflow_Index.md): connects the five sessions to course stages and A/C's genuine records. It distinguishes historical decisions, closeout comparisons and evidence gaps.
- [SHA256 manifest](F_Transcript_Manifest.json): hashes of the submitted original bytes and actual message counts. File identity does not establish approval or complete requirement coverage.
- [Final test and CI summary](../../docs/ci/F-Final-Test-and-CI-Summary.md): existing results tied to their tested SHAs, not new runs.

The entire message arrays emitted by the native exporter are retained, including summaries/compaction records already stored by OpenCode. Missing or compacted-away earlier context is not reconstructed. The earlier supplied Markdown copies contain only stage portions of these sessions; they are not uploaded as full raw exports. These records document extensions to an inherited upstream application, not a claim of writing the entire upstream system from zero.

Large JSON files may need downloading for local viewing. Locate a message by its ID, or use the annotation's fixed line reference. Original local exports and existing user Markdown files remain unchanged. No runtime rules, approval history, tests or CI settings are changed by this PR.
