# O3 OpenCode Execution Plan v0.1 — Input Condensation

Status: Draft for A review. Owner: C. Basis: merged PR #2 requirements at `4f87e29` and the companion O3 Test Plan v0.1.

1. **Prepare and obtain pre-code approvals.** Confirm the current target commit and record
   the requirements SHA. Submit the companion test plan for F's review. Ask OpenCode to
   inspect the repository in read-only mode and return its concrete execution plan with
   the affected files, requirement and test IDs, change sequence, verification commands,
   and human review checkpoints. Link the full OpenCode plan at a fixed GitHub commit or
   attach the exact version in the review thread for A. Record each approved plan version,
   scope, reviewer, approval link and actual time with time zone using
   `docs/test-approvals/TEMPLATE.md`. Obtain both approvals before code generation or edits.
   Coordinate the append-only configuration block with B.
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
   Run the targeted file and follow the companion plan’s T-R1 sequence for default
   collection, the default suite, and the explicit offline suite. Record observed results and report any discrepancy
   against the registry for review before altering the contract.
5. **Review evidence and submit.** Inspect the diff for scope, protected text, privacy,
   opt-out behavior and unchanged public signatures. Preserve the OpenCode transcript,
   human checkpoints, verification output and requirement-to-test mapping. Submit the
   reviewed implementation on the O3 branch after the pre-code approvals are recorded.
