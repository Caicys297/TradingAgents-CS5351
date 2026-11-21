# O5 S5 acceptance evidence and pre-code review scope

Baseline commit `be51ff077cc3109d2bba19448c8d87317806ef8e`. The observations below were obtained on Windows with Python 3.13.9. Extract the evidence bundle outside the Git checkout. Run the commands from a checkout of the baseline or the candidate with the project dev dependencies installed.

## Reproduce the observations

```powershell
python -m pytest -q test/offline/test_o5_macro_news_filter.py test/offline/test_o5_invariants.py test/offline/test_o5_macro_news_integration.py test/offline/test_o5_evidence_builder.py test/offline/test_o5_regression.py
python "PATH-TO-EXTRACTED-BUNDLE/probe_cli.py"
```

The first command passed 252 cases on the baseline. Individual results are in `o5-main-regression.xml`.

The second command exits 1 on the baseline. It runs the existing offline O2 harness through the real CLI entry, reserves a fresh temporary O2 run directory and invokes a compiled LangGraph ToolNode with the real get_global_news tool, router and Yahoo adapter during the stream. The surrounding trading graph and model are offline substitutes. LIMIT_ZERO requires zero vendor queries. The tool returned the agreed sentence and the CLI produced its manifest, but the run directory had no O5 JSONL file. The control separately bound a memory sink, invoked the tool through the graph configuration context and observed one V-LIMIT-ZERO event. The two observations are recorded separately in `baseline-result.json`. The temporary directory is discarded after inspection.

## S5 pre-code review version

C and E have agreed the interface and lifecycle below. This section supersedes the open interface choice in the earlier v0.1 handoff draft. F's S5 test-design review and A's execution/file-scope confirmation on this version are pending. The baseline observations above cover directory reservation and tool propagation. JSONL persistence failed on that baseline.

| Owner | Proposed implementation and test files | Responsibility |
| --- | --- | --- |
| C | `cli/run.py`, `test/offline/test_o2_cli_manifest.py` | Enter the O5 scope after a successful reservation and before constructing the graph. Cover the whole run, including graph construction failure, stream failure and interruption. Verify normal and abnormal teardown and isolated consecutive CLI runs. |
| E | `tradingagents/dataflows/vendors/yahoo/news.py`, `test/offline/test_o5_macro_news_integration.py` | Implement private `o5_evidence_run(run_dir)`, append existing events to `run_dir/o5_evidence.jsonl`, reset the context and release resources. Cover append semantics, unbound calls, I5 and I5b. Preserve public signatures and result strings. |
| C + E | The two offline test files above | Exercise a real ToolNode, get_global_news, router and Yahoo adapter inside the CLI scope using offline input. Assert the persisted rows and public result, then run against the same delivery commit. |

| Case for F's pre-code review | Required observation on a candidate |
| --- | --- |
| Real tool path | Repeat the baseline probe. Exit 0, exact result, O2 manifest, one parseable V-LIMIT-ZERO row with zero queries in the same run directory. |
| Multiple events | Validate every JSONL line. Each emitted event appears once and earlier lines survive subsequent writes. |
| CLI lifetime | Verify binding before graph construction and restoration on success, exception and KeyboardInterrupt. The original exception or interrupt propagates. |
| Isolation | Two runs of the same ticker/date have separate directories and events. A later unbound tool call appends to neither. |
| I5b | Force real sink construction/open to fail at scope entry. Compare the complete public result with a working control on the same input. Observe independent SINK_FAILED, no success record and restored context. |
| I5 | Independently fail a write after successful construction. Check the public result against the working control, the diagnostic and the absence of a successful event for the failed write. |

The probe covers the first row. Completion requires the C/E implementation, remaining cases, a CI run at the same SHA, and F's implementation review. The test-design approval for the S2–S4 batch explicitly deferred real persistence and I5b. F can review these cases for S5 without reopening that earlier batch.

Sources for the baseline and earlier reviews: [A's execution scope](https://github.com/Caicys297/TradingAgents-CS5351/pull/3#issuecomment-6917171487), [F's S2–S4 review and I5b boundary](https://github.com/Caicys297/TradingAgents-CS5351/pull/3#pullrequestreview-5986202826), [C's CLI ownership](https://github.com/Caicys297/TradingAgents-CS5351/pull/23#issuecomment-7061542739).
