# O5 pre-code review package (v1.3)

**Owner:** E (O5). **Status:** Draft; **not approved for implementation**. Software tests and benchmarks have **not** been run.

**Revision:** v1.3 — replaces v1.2 in the same PR #3 directory. Responds to A's review of commit `27c8e4be0f0e8b1af4611ae29a86ac106fd00967`. The two plan filenames keep `v1.1` so PR links stay stable; **v1.3 is the active document revision**.

---

## Baseline

- **Merged requirements baseline (PR #2, merged):** `4f87e29f7a52842dba8272071d2a4a1b527def10` — full SHA resolved; also `refs/heads/main` at inspection.
- **Registry bytes** `docs/req/requirements.yaml` @ `4f87e29`: 88,122 bytes, SHA-256 `365dd2d8bf12b138b19ce8d90e1103f19a48eed8c1fce38be4c2287219d8d5f9`.
- **DEV20 fixture** @ `4f87e29` and at PR head: SHA-256 `a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6` (matches `development_contract.o5.dev20_fixture_sha256`).
- **Offline collection already exists** on the merged baseline (`testpaths = ["tests", "test/offline"]`; `test/offline/conftest.py` blocks sockets and `curl_cffi`). O5's own collection/isolation remains **untested**.
- **Local checkout used for this package:** `970a9ea` on `main`. A **new base check is required before implementation**.

---

## BLOCKING decision (v1.3)

**A1 — canonical `rules_version` is unresolved (BLOCKING).** The registry says `o5-rules-v1.1` in `REQ-O5-01.statement` but `o5-rules-v1.1-draft` in `development_contract.o5.rules_version`, and the DEV20 fixture repeats `-draft`. **A/B must pick one literal and synchronize** the statement, the contract, the fixture metadata (which changes `dev20_fixture_sha256`), the `o5_rules_version` config value and every active plan, **before coding**. E proposes **`o5-rules-v1.1`**; it is **not approved** and no fixture byte was changed. `-draft` values in the plans are provisional/historical.

## Other v1.3 changes

- **Ownership (A2):** E implements the O5 private integration in `tradingagents/dataflows/vendors/yahoo/news.py`; **C** confirms only the O2 run-directory handoff and C-owned shared files. The v1.2 implication that C owned `news.py` is withdrawn.
- **Evidence lifecycle (A3):** terminal evidence is emitted **after** selection and invariant validation, or at the failure boundary — **never** from the retrieval loop's `finally`. See the Test Plan §4.6 path table and Execution Plan §3.4.
- **T17 digests (A4):** every active digest reference was recomputed from actual bytes; the Test Plan's stale manifest/handoff digests are replaced by a pointer to this README.

---

## Documents

- [Test plan (v1.3 active)](O5-Test-Plan-precode-v1.1-DRAFT.md) — **reviewer: F**.
- [OpenCode execution plan (v1.3 active)](O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md) — **reviewer: A**.
- [Detailed test cases — r2 historical reference](O5-Detailed-Test-Cases-Reference-r2.md) — subordinate to the active amendments.
- [Interface and runtime policy — r2 historical reference](O5-Interface-Reference-r2.md) — subordinate to the active amendments.

### T17 performance artifacts (digests computed from actual bytes)

| File | SHA-256 |
|---|---|
| [`O5-T17-Perf-Fixture-1000-v1-DRAFT.json`](O5-T17-Perf-Fixture-1000-v1-DRAFT.json) | `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0` |
| [`O5-T17-Expected-Results-v1-DRAFT.json`](O5-T17-Expected-Results-v1-DRAFT.json) | `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6` |
| [`O5-T17-F-Handoff-v1-DRAFT.md`](O5-T17-F-Handoff-v1-DRAFT.md) | `fb6d306f42be6fdad049613612f4ce5a525146e28b2130795d8ccc514756990a` |
| [`O5-T17-Manifest-v1-DRAFT.json`](O5-T17-Manifest-v1-DRAFT.json) | **`0b9f398ee7e1f3a7d4b7914fca41b8e8ef945a5c33a4426fb79b13442fc6ecd5`** |

**One-way integrity.** The manifest records the fixture, expected-results and handoff digests; the handoff references the manifest **by filename only**; this README records the manifest's final digest, and the manifest does not hash the README. No cycle: `manifest → {fixture, expected, handoff}` and `README/plans → manifest`.

Fixture and expected-result bytes are **unchanged** from v1.2; only the manifest, the handoff's header/wording, and this README changed.

---

## Review state

- **F reviews the O5 test plan; A reviews the OpenCode execution plan.** Both remain **pending review**.
- Coding may begin only after both scoped approvals and project-governance readiness, **and** after the A1 blocking decision lands.
- An empty `docs/test-approvals/TEMPLATE.md` is not approval.
- **All software tests and benchmarks: Not run.**
- Preserved F closures from r2 stay closed; only the lifecycle-affected cases (Test Plan §9b) need renewed review.
