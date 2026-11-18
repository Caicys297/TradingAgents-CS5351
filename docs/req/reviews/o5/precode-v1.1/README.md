# O5 S1 formal review package v1.7

**Registry corrected and verified. F formal S1 approval pending. All software tests and benchmarks Not run.**

- [Active test plan](./O5-Test-Plan-precode-v1.1-DRAFT.md)
- [Exact S1 inventory](./O5-S1-Case-Inventory-v1.5-DRAFT.md): 48 selector row IDs plus I6/I7/I8/I10 schema families, parameter details, requirement mapping, negative controls, assertions and exclusions.
- [Course evidence matrix](./O5-S1-Course-Requirements-and-Evidence-v1.5-r2.md): stable filename, active v1.6; D1-D9 and six gates remain tracked.
- [A-approved execution plan](./O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md): v1.4 bytes unchanged.

Formal Registry merge and inspected main: `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. O5 delta from c861d03 is only REQ-O5-01.statement -> o5-rules-v1.1-draft. Contract, other O5 requirements/mappings, DEV20 and T17 data remain unchanged. B manual Schema validation has a record per A; not rerun here; Schema CI Gate is NOT connected.

A execution approval: https://github.com/Caicys297/TradingAgents-CS5351/pull/3#issuecomment-6917171487
A S1 clarification: https://github.com/Caicys297/TradingAgents-CS5351/pull/3#issuecomment-6943145906
F must approve this version's exact S1 subset before first functional/test edit. No new S2-S6 approval or execution-plan scope requested.

## T17 preserved hashes (outside S1)

- [O5-T17-Perf-Fixture-1000-v1-DRAFT.json](./O5-T17-Perf-Fixture-1000-v1-DRAFT.json): `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0`
- [O5-T17-Expected-Results-v1-DRAFT.json](./O5-T17-Expected-Results-v1-DRAFT.json): `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6`
- [O5-T17-F-Handoff-v1-DRAFT.md](./O5-T17-F-Handoff-v1-DRAFT.md): `ab419ec5eb27970e32068b8bd94ec5d15e7e6ad82ee537410ab54103fd8fd805`
- [O5-T17-Manifest-v1-DRAFT.json](./O5-T17-Manifest-v1-DRAFT.json): `81dbfaeeec63a7a511364b3472bf59bb2ef42daaf82a625952b89a317a8e1fad`

## PR delivery

Use existing PR #3, branch docs/o5-precode-review-v1.1, folder docs/req/reviews/o5/precode-v1.1/. Replace Test Plan/README and add the S1 inventory/course matrix. Seven existing supporting files remain unchanged. Local check reports and submission draft are not software test results. Do not upload to the repository root.

## v1.7 narrow review correction

F accepted the v1.6 selector row/parameter scope; those rows are unchanged. Inventory sections 5.1-5.2 specify the one test-local contract entry, independent rules, common control/mutant calls and intended-clause diagnostics. Section 1 corrects the old pending Registry statement. F's final pre-code approval is still pending. No executable tests, production validator/builder, dependency or CI changes. The course evidence matrix retains its v1.6 content unchanged.
