# O5 T17 Performance Review - Handoff to Member F (DRAFT)

**Owner:** Member E (O5). **Status:** PROPOSED review artifact. Not implementation approval. No benchmark run performed. All software tests remain Not run.
**Revision:** v1.3 package. Evidence/ownership/`rules_version` changes are in the two plans; this handoff's only v1.3 change is the provisional `rules_version` wording above and the digest-authority note below.
**Digest authority (A4):** this handoff contains no manifest digest (one-way integrity); the manifest records this file's digest. Authoritative final digests live in `README.md`.
**Files in this directory:**

| File | SHA-256 |
|---|---|
| `O5-T17-Perf-Fixture-1000-v1-DRAFT.json` | `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0` |
| `O5-T17-Expected-Results-v1-DRAFT.json` | `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6` |
| `O5-T17-Manifest-v1-DRAFT.json` | **referenced by filename; its digest is recorded in `README.md`** |
| `O5-T17-F-Handoff-v1-DRAFT.md` | *(this file; its digest is recorded in the manifest)* |

**Integrity relationship is one-way.** The manifest records this handoff's digest; this handoff therefore **must not** record the manifest's digest, or the pair would be circular. The stale digest that an earlier handoff cited (beginning `53bd45f7`) is **superseded and removed** — it described a manifest revision that no longer exists. The final manifest digest lives in `README.md`, which the manifest does not hash.

---

## 1. Implementation status (verified)

**No O5 selector implementation exists in the repository.**
- `tradingagents/dataflows/macro_news_filter.py` - **absent** (checked).
- `src/` contains only `.gitkeep` (checked).
- Therefore **there is no runnable entry point**, and **no working benchmark command can be given**.

Any module or function named below is **unimplemented and pending Member C's confirmation**. Proposed (not existing):
- module: `tradingagents/dataflows/macro_news_filter.py`;
- function: `select_macro_news(request) -> result` (name/shape Pending C).

**Do not run any command expecting an entry point until C confirms it and an implementation exists.**

---

## 2. Proposed selector input/output contract (from the v0.5.3-corrected-r2 Interface)

**Input (in-memory selector record):** `candidate_id:str`, `title:str`, `summary:str`(->""), `published_at: datetime(aware UTC)|None`, `source:str|None`, `url:str|None`; request: `topics` (ordered subset), `start_at`/`end_at` (aware UTC), `limit:int>=0` (not bool), `rules_version:str`. `title_norm` is derived internally, not supplied.

**Output:** `selected[]` (copies + `matched_topics` request-ordered + `primary_topic` + `matched_rule_ids`), `decisions[]` (one per input position), `counts` (8 canonical keys), `status` (`OK`/`NO_RELEVANT_NEWS`/`LIMIT_ZERO`), `metadata` (`rules_version`, window, `topic_order`).

The fixture is serialized (RFC3339 strings); the loader converts to the in-memory form.

---

## 3. Loader steps (outside the timing boundary)

1. Read `O5-T17-Perf-Fixture-1000-v1-DRAFT.json` (UTF-8).
2. Parse `published_at` RFC3339 -> aware UTC `datetime`.
3. Apply defaults for absent/null `summary`/`source`/`url`.
4. Build request: `topics = ["MONETARY_POLICY","INFLATION","ECONOMIC_ACTIVITY"]`, `start_at`/`end_at` from the fixture window, `limit = 30`, and `rules_version` set to the **canonical literal once A/B resolve it** (currently `"o5-rules-v1.1-draft"`, a **provisional/historical** value; E proposes `o5-rules-v1.1`). Do not hard-code the provisional value in any approved measurement.
5. Verify the fixture SHA-256 matches the manifest before measuring.

---

## 4. Timing boundary

- **Outside measurement:** file load, JSON deserialization, RFC3339 parsing, datetime conversion, default application, and contract-required input construction (steps 1-5).
- **Inside measurement:** everything owned by the selector - request validation, structure/field validation, ID registration/duplicate handling, classification, bucket sort, round-robin allocation, and complete result construction.
- **Outside again:** correctness assertions and output persistence.
- **Mutated input:** if the selector mutates the input structure, that is a **correctness failure** (INV-O5-02), not a reason to reset and continue.

---

## 5. Measurement procedure (proposed, pending F/E agreement)

- 5 warmup calls (discarded).
- 30 measured calls.
- Nearest-rank **p95 = 29th smallest** sample.
- **100 ms** is a **proposed** threshold (team proposal, not a teacher mandate).
- **Correctness gate first:** every measured call's result must equal `O5-T17-Expected-Results-v1-DRAFT.json` (selected ID order, primary topics, status, all counts). Any error or mismatch makes that measurement **invalid**, not a passing performance result.
- Runner specification remains **pending F**; final threshold remains **pending F/E agreement**.

---

## 6. Expected result summary (proposed)

- `status = OK`; `selected_count = 30` (10 MP / 10 IN / 10 EA); buckets MP 400 / IN 260 / EA 260; total relevant 920.
- Counts: input 1000, selected 30, not_selected_limit 890, irrelevant 60, invalid 0, out_of_window 0, duplicate 20, skipped_zero_limit 0 (conserves).
- Title lengths 55-71 chars; summary lengths 68-102 chars; both within the 300/2000 limits.

**These are proposed expectations derived from the frozen rules, pending review - not implementation output.**
