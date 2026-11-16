# O5 pre-code review package (v1.4)

**Owner:** E (O5). **Status:** Draft; **not approved for implementation**. Software tests and benchmarks have **not** been run.

**Revision:** v1.4 — replaces v1.3 in the same PR #3 directory. Responds to F's and A's review of commit `2b85ec3fd2150176b8ed9aa929b8ddd7c5502aa0`. The two plan filenames keep `v1.1` so PR links stay stable; **v1.4 is the active document revision**. The v1.2/v1.3 notes inside the plans are historical.

---

## Baseline

- **Merged requirements baseline (PR #2, merged):** `4f87e29f7a52842dba8272071d2a4a1b527def10`.
- **Reviewed PR #3 commit:** `2b85ec3fd2150176b8ed9aa929b8ddd7c5502aa0` (its 9 files are byte-identical to the local v1.3 package).
- **Registry bytes** `docs/req/requirements.yaml` @ `4f87e29`: 88,122 bytes, SHA-256 `365dd2d8bf12b138b19ce8d90e1103f19a48eed8c1fce38be4c2287219d8d5f9`.
- **DEV20 fixture**: SHA-256 `a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6` (unchanged).
- **Offline collection already exists** on the merged baseline (`testpaths = ["tests", "test/offline"]`; `test/offline/conftest.py` blocks sockets and `curl_cffi`). O5's own collection/isolation remains **untested**.
- **Local checkout used for this package:** `970a9ea` on `main`. A new base check is required before implementation.

---

## BLOCKING decision (unchanged, updated)

**A1 — canonical `rules_version` is unresolved.** `requirements.yaml` says `o5-rules-v1.1` in `REQ-O5-01.statement` but `o5-rules-v1.1-draft` in `development_contract.o5.rules_version`; the DEV20 fixture repeats `-draft` (re-verified at `4f87e29` and PR head `2b85ec3`).

**A's latest proposal (recorded, not approved):** retain **`o5-rules-v1.1-draft`** to minimize fixture/hash churn, and ask **B** to reconcile the registry statement. **E's earlier active recommendation to adopt `o5-rules-v1.1` is withdrawn from the active text** (it survives only in the historical v1.3 file). No fixture byte and no registry file was changed.

---

## v1.4 changes

| Review | Change | Where |
|---|---|---|
| **F1** invariant mapping | One consistent mapping: **I1, I3 → INV-O5-02**; **I2 → INV-O5-03**; **I11 → INV-O5-01**; I4/T16 → INV-O5-04. Mutation/collision scenarios keep their own IDs | Test Plan §3 + §4.5 |
| **F2** T17 handoff | Handoff itself now states **ubuntu-latest / Python 3.11**, **p95 ≤ 100 ms**, **5 warmups + 30 measured calls**, and the **fail-overall** rule; digests refreshed through the one-way chain | Handoff §5, Manifest, README, Test Plan §7, Exec §9a |
| **F3** V-VENDOR vs V-PARTIAL | **I9-b restored** to the post-resolution `V-VENDOR` case; the v1.3 V-PARTIAL scenario renumbered to **I13** with a migration note. T13c-D/T13c-R keep one `V-PARTIAL` and no `V-VENDOR` | Test Plan §4.2, §4.3, §4.3a, §6 |
| **A1** proposal | A's retain-`-draft` proposal recorded; E's non-draft recommendation withdrawn from active text; blocker retained | Test Plan §0a, §8 D-02, §9 Q3; Exec §7 |
| **A2** ownership | Seam owners and step 10 reconciled: **E** implements the `news.py` integration; **C** confirms the O2 `run_dir` handoff and C-owned shared files | Exec §5, §6 step 10; Test Plan §0a |
| **A3** lint | Planned `ruff check` now includes `tradingagents/dataflows/vendors/yahoo/news.py`; status blocks say v1.4 | Exec §8, §11; Test Plan §4.4a |
| **A4** dependencies | Dependency-boundary table (S1–S6) with required decisions and separability, without granting permission to code | Exec §5a |

---

## Documents

- [Test plan (v1.4 active)](O5-Test-Plan-precode-v1.1-DRAFT.md) — **reviewer: F**.
- [OpenCode execution plan (v1.4 active)](O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md) — **reviewer: A**.
- [Detailed test cases — r2 historical reference](O5-Detailed-Test-Cases-Reference-r2.md) — subordinate to the active amendments.
- [Interface and runtime policy — r2 historical reference](O5-Interface-Reference-r2.md) — subordinate to the active amendments.

### T17 performance artifacts (digests computed from actual bytes)

| File | SHA-256 |
|---|---|
| [`O5-T17-Perf-Fixture-1000-v1-DRAFT.json`](O5-T17-Perf-Fixture-1000-v1-DRAFT.json) | `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0` |
| [`O5-T17-Expected-Results-v1-DRAFT.json`](O5-T17-Expected-Results-v1-DRAFT.json) | `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6` |
| [`O5-T17-F-Handoff-v1-DRAFT.md`](O5-T17-F-Handoff-v1-DRAFT.md) | `ab419ec5eb27970e32068b8bd94ec5d15e7e6ad82ee537410ab54103fd8fd805` |
| [`O5-T17-Manifest-v1-DRAFT.json`](O5-T17-Manifest-v1-DRAFT.json) | **`81dbfaeeec63a7a511364b3472bf59bb2ef42daaf82a625952b89a317a8e1fad`** |

**One-way integrity.** The manifest records the fixture, expected-results and handoff digests; the handoff references the manifest **by filename only**; this README records the manifest's final digest, and the manifest does not hash the README. **F confirmed the v1.3 hashes were consistent**; v1.4 changed the handoff and manifest, so those digests are new and need review — the confirmation is not a waiver.

Fixture and expected-result bytes are **unchanged** from v1.3.

---

## Review state

- **F reviews the O5 test plan; A reviews the OpenCode execution plan.** Both remain **pending review**.
- **A acknowledged** the v1.3 corrected evidence timing and the ownership direction; that is **not** whole-plan approval.
- Coding may begin only after both scoped approvals, project-governance readiness, **and** the A1 blocking decision.
- An empty `docs/test-approvals/TEMPLATE.md` is not approval.
- **All software tests and benchmarks: Not run.**
