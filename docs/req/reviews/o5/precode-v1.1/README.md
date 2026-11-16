# O5 pre-code review package (v1.2)

**Owner:** E (O5). **Status:** Draft; **not approved for implementation**. Software tests and benchmarks have **not** been run.

**Revision:** v1.2 — replaces v1.1 in the same PR #3 directory. Responds to A's and F's review of commit `85ffc242b10ebd242501ef61e7c7b95deee0a9d2`. The two plan filenames keep `v1.1` so PR links stay stable; **v1.2 is the active document revision**.

---

## Baseline

- **Merged requirements baseline (PR #2, merged):** `4f87e29f7a52842dba8272071d2a4a1b527def10` — F's identified `4f87e29`, full SHA resolved here.
- **Current remote `main`:** the same SHA at inspection time. If it moves later it is a *different* revision; the baseline above is authoritative for this review.
- **Registry bytes** `docs/req/requirements.yaml` @ `4f87e29`: 88,122 bytes, SHA-256 `365dd2d8bf12b138b19ce8d90e1103f19a48eed8c1fce38be4c2287219d8d5f9`.
- **DEV20 fixture** @ `4f87e29`: SHA-256 `a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6` (matches `development_contract.o5.dev20_fixture_sha256`).
- **Offline collection is already configured on the merged baseline:** `pyproject.toml` has `testpaths = ["tests", "test/offline"]` and `test/offline/conftest.py` already blocks sockets and `curl_cffi`. The earlier claim that F must add initial collection is withdrawn; **O5's own tests/collection remain untested**.
- **Local checkout used for this package:** `970a9ea` on `main`. A **new base check is required before implementation**.

---

## Documents

- [Test plan (v1.2 active)](O5-Test-Plan-precode-v1.1-DRAFT.md) — **reviewer: F**.
- [OpenCode execution plan (v1.2 active)](O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md) — **reviewer: A**.
- [Detailed test cases — r2 historical reference](O5-Detailed-Test-Cases-Reference-r2.md) — subordinate to the v1.2 amendments.
- [Interface and runtime policy — r2 historical reference](O5-Interface-Reference-r2.md) — subordinate to the v1.2 amendments.

### T17 performance artifacts

| File | SHA-256 |
|---|---|
| [`O5-T17-Perf-Fixture-1000-v1-DRAFT.json`](O5-T17-Perf-Fixture-1000-v1-DRAFT.json) | `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0` |
| [`O5-T17-Expected-Results-v1-DRAFT.json`](O5-T17-Expected-Results-v1-DRAFT.json) | `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6` |
| [`O5-T17-F-Handoff-v1-DRAFT.md`](O5-T17-F-Handoff-v1-DRAFT.md) | `3294965982fbd1e306f232d6063f00053990e6046d026b914ca5e7c2f01ae783` |
| [`O5-T17-Manifest-v1-DRAFT.json`](O5-T17-Manifest-v1-DRAFT.json) | **`2d40cdfd6afb98ad7abcca53616e39f39c9b5963fe224e08a33c29f1b34f1c23`** |

**One-way integrity.** The manifest records the handoff's digest; the handoff references the manifest **by filename only**; this README records the manifest's final digest, and the manifest does not hash the README. No cycle. The stale digest `53bd45f7…` cited by an older handoff is removed.

Fixture and expected-result bytes are **unchanged**; only the manifest and the handoff's hash table were edited.

---

## Review state

- **F reviews the O5 test plan; A reviews the OpenCode execution plan.** Both remain **pending review**.
- Coding may begin only after **both** scoped approvals and project-governance readiness. An empty `docs/test-approvals/TEMPLATE.md` is not approval.
- **All software tests and benchmarks: Not run.**
- Preserved F closures from r2 remain closed unless a v1.2 amendment changes that assertion (see the test plan's §11).
