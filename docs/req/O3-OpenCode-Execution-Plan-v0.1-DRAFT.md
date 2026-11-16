# O3 OpenCode Execution Plan v0.1 — Input Condensation

Status: Draft for A review. Owner: C. Basis: merged PR #2 requirements and the companion O3 Test Plan v0.1.

1. **Establish the baseline.** Confirm the current target commit, read the O3 registry entries,
   inspect the three source shapes and the Sentiment Analyst prompt construction, and record
   the checkout SHA. Coordinate the append-only config block with B. Record F's test-plan
   approval and A's execution-plan approval using the team template before editing code.
2. **Implement the pure condenser through OpenCode.** Add
   `tradingagents/agents/analysts/condensation.py`. Implement source parsing and one-item
   fallback, first-occurrence deduplication, stable ranking, protected placeholders,
   per-source budgets, and a safe audit. Implement the optional tokenizer interface without
   a core dependency. Ask OpenCode to show the diff and trace the normal and exception paths.
3. **Wire the Sentiment Analyst.** Edit
   `tradingagents/agents/analysts/sentiment_analyst.py` and the coordinated O3 block in
   `tradingagents/default_config.py`. Condense before interpolation, preserve the outer prompt,
   record budget exceptions, and preserve the baseline prompt when disabled. The scoped change
   covers these files, the new condenser, and `test/offline/test_input_condensation.py`.
   Shared graph/CLI integration and O4/O6 changes are separately scoped.
4. **Verify.** Have OpenCode add the approved offline cases, including T-R4, T-E7 and T-E8.
   Run the targeted file and the full explicit offline command in the companion test plan.
   Confirm default collection with F. Record observed results and report any discrepancy
   against the registry for review before altering the contract.
5. **Review evidence and submit.** Inspect the diff for scope, protected text, privacy,
   opt-out behavior and unchanged public signatures. Preserve the OpenCode transcript,
   human checkpoints, verification output and requirement-to-test mapping. Submit the
   reviewed implementation on the O3 branch after the pre-code approvals are recorded.
