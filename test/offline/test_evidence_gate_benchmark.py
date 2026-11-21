"""O4 Stage 2 — T-16 pure-checker latency benchmark (D-owned, non-blocking).

Measures the incremental latency of the **pure** ``check_evidence()`` checker
only — not the Graph/CLI integration wrapper, and not any disk/memory/render
I/O. Follows the registry procedure: fixed four-report fixture, 5 warm-up calls,
30 measured calls, single process, nearest-rank p95 of ``added`` latency.

The ``p95 <= 10 ms`` target is **diagnostic / non-blocking** (O4-NFR-03 is
``Should``); it is recorded and reported, and is NOT a failing assertion unless
Members A and F separately approve CI enforcement. Blocking assertions here are
only correctness / fixed-count / no-network invariants.
"""

from __future__ import annotations

import math
import time

from o4_stage2_fixtures import ALL_ANALYSTS, complete_state

from tradingagents.agents.evidence_gate import VERDICT_VALID, check_evidence

WARMUPS = 5
MEASURED = 30
P95_TARGET_NS = 10_000_000  # 10 ms inclusive, diagnostic only


def _nearest_rank_p95(samples_ns: list[int]) -> int:
    """Nearest-rank p95: sorted, take the ceil(0.95 * n)-th item (1-indexed)."""
    ordered = sorted(samples_ns)
    rank = math.ceil(0.95 * len(ordered))
    return ordered[rank - 1]


def _baseline_ns() -> int:
    """Harness baseline that excludes BOTH fixture construction and the checker.

    The fixture is built OUTSIDE the timed window in the measured path, so the
    baseline must not time fixture construction either (the prior version did,
    which corrupted the added-latency delta). It measures only the empty
    timing harness overhead around the same (already-built) state value.
    """
    start = time.perf_counter_ns()
    # No work: this isolates the perf_counter overhead so the delta measures the
    # pure check_evidence() call added on top of it.
    return time.perf_counter_ns() - start


def _measured_ns(state) -> int:
    """Time ONLY the pure ``check_evidence()`` call on a pre-built fixture."""
    start = time.perf_counter_ns()
    result = check_evidence(state, ALL_ANALYSTS)
    delta = time.perf_counter_ns() - start
    assert result.verdict == VERDICT_VALID
    return delta


def test_t16_pure_checker_correctness_and_fixed_counts():
    """Correctness + one direct invocation per sample (blocking, no timing)."""
    state = complete_state("Buy")
    results = [check_evidence(state, ALL_ANALYSTS) for _ in range(10)]
    assert all(r.verdict == VERDICT_VALID for r in results)
    assert all(r.effective_rating == "Buy" for r in results)
    assert len(results) == 10


def test_t16_checker_is_pure_no_state_mutation():
    """The checker does not mutate its input (provenance stays readable)."""
    state = complete_state("Overweight", body="Rating: Overweight")
    before = dict(state)
    check_evidence(state, ALL_ANALYSTS)
    assert state == before


def test_t16_pure_checker_p95_diagnostic():
    """Registry-procedure p95; **diagnostic/non-blocking** (Should).

    Always records and reports the p95; never fails CI on latency unless A/F
    approve enforcement. Blocking checks are only the structural invariants.
    """
    fixed_state = complete_state("Buy")  # built ONCE, outside every timed window
    # warm-ups (not counted)
    for _ in range(WARMUPS):
        _measured_ns(fixed_state)

    deltas: list[int] = []
    for _ in range(MEASURED):
        base = _baseline_ns()
        measured = _measured_ns(fixed_state)
        deltas.append(measured - base)

    # Structural blocking invariants (not a latency pass/fail):
    assert len(deltas) == MEASURED
    assert all(isinstance(d, int) for d in deltas)

    p95 = _nearest_rank_p95(deltas)
    within = p95 <= P95_TARGET_NS
    # Non-blocking measurement evidence: raw samples + actual call counts + p95.
    assert len(deltas) == MEASURED and WARMUPS == 5 and MEASURED == 30
    print(
        f"\n[T-16] warmups={WARMUPS} measured={MEASURED} "
        f"raw_deltas_ns={deltas} p95_ns={p95} within_target={within}"
    )
    # Record the measurement for the run log / report (NEVER fail or skip on latency).
    import warnings

    warnings.warn(
        f"T-16 pure check_evidence p95 added latency = {p95} ns ({p95 / 1e6:.3f} ms); "
        f"target {P95_TARGET_NS / 1e6:.1f} ms (Should, diagnostic, non-blocking); "
        f"within_target={within}; samples={MEASURED} warmups={WARMUPS}",
        stacklevel=1,
    )
    print(
        f"\n[T-16] pure check_evidence p95 added latency = {p95} ns "
        f"({p95 / 1e6:.3f} ms); target {P95_TARGET_NS / 1e6:.1f} ms "
        f"(Should, diagnostic, non-blocking; within_target={within}); "
        f"samples={MEASURED} warmups={WARMUPS}"
    )
