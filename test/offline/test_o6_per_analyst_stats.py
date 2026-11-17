"""Offline tests for O6 Batch 1 per-Analyst statistics (TC-O6-01..06, 08..10).

These tests exercise ``cli.stats_handler.StatsCallbackHandler`` with
synthetic callback events and a controlled monotonic clock. No live services,
credentials or network access are used; the offline ``_no_network`` guard in
``test/offline/conftest.py`` applies to every case here.

Scope: handler behavior only. Real subgraph attribution and shared CLI/Graph
wiring are intentionally out of this batch.
"""

import copy
import socket

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from cli.stats_handler import StatsCallbackHandler

MARKET = "market"
NEWS = "news"
SELECTED = {MARKET, NEWS}


class FakeClock:
    """Deterministic monotonic clock advanced by the test."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def set(self, value: float) -> None:
        self._now = value


def _handler():
    clock = FakeClock()
    return StatsCallbackHandler(SELECTED, clock=clock), clock


def _start(handler, clock, run_id, *, scope="analyst", agent_key=None, t=None):
    if t is not None:
        clock.set(t)
    metadata = {}
    if scope is not None:
        metadata["scope"] = scope
    if agent_key is not None:
        metadata["agent_key"] = agent_key
    handler.on_chat_model_start({}, [[]], run_id=run_id, metadata=metadata)


def _end(handler, clock, run_id, *, input_tokens=None, output_tokens=None, t=None):
    if t is not None:
        clock.set(t)
    message = AIMessage(content="ok")
    if input_tokens is not None or output_tokens is not None:
        usage = {}
        if input_tokens is not None:
            usage["input_tokens"] = input_tokens
        if output_tokens is not None:
            usage["output_tokens"] = output_tokens
        usage["total_tokens"] = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        message = AIMessage(content="ok", usage_metadata=usage)
    response = LLMResult(generations=[[ChatGeneration(message=message)]])
    handler.on_llm_end(response, run_id=run_id)


def _error(handler, clock, run_id, *, t=None):
    if t is not None:
        clock.set(t)
    handler.on_llm_error(RuntimeError("boom"), run_id=run_id)


def _row(stats, key):
    return stats["analysts"].get(key)


# -- TC-O6-01: named rows, ordinary + wrap_up (FR-01) -----------------------
def test_tc_o6_01_market_two_calls_news_one():
    handler, clock = _handler()
    # Market ordinary: 100/20 over 1.0 s.
    _start(handler, clock, "m1", agent_key=MARKET, t=0.0)
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)
    # Market wrap_up: 50/10 over 0.5 s.
    _start(handler, clock, "m2", agent_key=MARKET, t=1.0)
    _end(handler, clock, "m2", input_tokens=50, output_tokens=10, t=1.5)
    # News ordinary: 80/15 over 0.8 s.
    _start(handler, clock, "n1", agent_key=NEWS, t=0.0)
    _end(handler, clock, "n1", input_tokens=80, output_tokens=15, t=0.8)

    stats = handler.get_agent_stats()
    market = _row(stats, MARKET)
    news = _row(stats, NEWS)
    assert market["calls"] == 2
    assert market["input_tokens"] == {"value": 150, "status": "complete"}
    assert market["output_tokens"] == {"value": 30, "status": "complete"}
    assert market["duration"] == pytest.approx(1.5)
    assert news["calls"] == 1
    assert news["input_tokens"] == {"value": 80, "status": "complete"}
    assert news["output_tokens"] == {"value": 15, "status": "complete"}
    assert news["duration"] == pytest.approx(0.8)


# -- TC-O6-02: missing usage vs explicit 0/0 (FR-02) -----------------------
def test_tc_o6_02_missing_usage_vs_explicit_zero():
    handler, clock = _handler()
    # Completed call with missing usage -> both fields Unknown.
    _start(handler, clock, "a", agent_key=MARKET, t=0.0)
    _end(handler, clock, "a", t=1.0)
    # Completed call reporting explicit 0/0 -> two complete zero totals.
    _start(handler, clock, "b", agent_key=NEWS, t=1.0)
    _end(handler, clock, "b", input_tokens=0, output_tokens=0, t=2.0)

    stats = handler.get_agent_stats()
    market = _row(stats, MARKET)
    news = _row(stats, NEWS)
    assert market["input_tokens"] == {"value": None, "status": "unknown"}
    assert market["output_tokens"] == {"value": None, "status": "unknown"}
    assert news["input_tokens"] == {"value": 0, "status": "complete"}
    assert news["output_tokens"] == {"value": 0, "status": "complete"}


# -- TC-O6-03: independent token completeness (FR-02) ----------------------
def test_tc_o6_03_partial_output_metadata_omits_field():
    handler, clock = _handler()
    _start(handler, clock, "c1", agent_key=MARKET, t=0.0)
    _end(handler, clock, "c1", input_tokens=100, output_tokens=20, t=1.0)

    # Second call reports input but truly omits output usage in the payload.
    # The typed AIMessage schema requires all three keys, so build the payload
    # without validation to model a provider that omits the field.
    message = AIMessage.model_construct(
        content="ok",
        usage_metadata={"input_tokens": 50, "total_tokens": 50},
    )
    assert isinstance(message, AIMessage)
    assert "output_tokens" not in message.usage_metadata
    response = LLMResult(generations=[[ChatGeneration(message=message)]])
    _start(handler, clock, "c2", agent_key=MARKET, t=1.0)
    clock.set(2.0)
    handler.on_llm_end(response, run_id="c2")

    market = _row(handler.get_agent_stats(), MARKET)
    assert market["calls"] == 2
    assert market["input_tokens"] == {"value": 150, "status": "complete"}
    assert market["output_tokens"] == {"value": 20, "status": "partial"}


# -- TC-O6-04: interleaved, reverse-order completion (FR-01, NFR-01) -------
def test_tc_o6_04_interleaved_reverse_completion():
    handler, clock = _handler()
    _start(handler, clock, "m1", agent_key=MARKET, t=0.0)
    _start(handler, clock, "n1", agent_key=NEWS, t=0.2)
    # News finishes first at 1.0 s (0.8 s); Market finishes later at 1.5 s (1.5 s).
    _end(handler, clock, "n1", input_tokens=80, output_tokens=15, t=1.0)
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.5)

    stats = handler.get_agent_stats()
    market = _row(stats, MARKET)
    news = _row(stats, NEWS)
    assert market["calls"] == 1
    assert market["input_tokens"] == {"value": 100, "status": "complete"}
    assert market["output_tokens"] == {"value": 20, "status": "complete"}
    assert market["duration"] == pytest.approx(1.5)
    assert news["calls"] == 1
    assert news["input_tokens"] == {"value": 80, "status": "complete"}
    assert news["output_tokens"] == {"value": 15, "status": "complete"}
    assert news["duration"] == pytest.approx(0.8)


# -- TC-O6-05: replay dedup, error duration, start-only pending ------------
def test_tc_o6_05_replay_error_and_pending():
    handler, clock = _handler()
    # Baseline call.
    _start(handler, clock, "m1", agent_key=MARKET, t=0.0)
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)
    snapshot = handler.get_agent_stats()

    # Replay the same start/end; new stats must equal the pre-replay snapshot.
    _start(handler, clock, "m1", agent_key=MARKET, t=1.0)
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)
    assert handler.get_agent_stats() == snapshot

    # Errored call: start 1.0 -> error 1.75 accrues 0.75 s, counts once, Unknown usage.
    _start(handler, clock, "err", agent_key=NEWS, t=1.0)
    _error(handler, clock, "err", t=1.75)
    news = _row(handler.get_agent_stats(), NEWS)
    assert news["calls"] == 1
    assert news["duration"] == pytest.approx(0.75)
    assert news["input_tokens"] == {"value": None, "status": "unknown"}
    assert news["output_tokens"] == {"value": None, "status": "unknown"}

    # Start-only call: counts once with 0 s while pending.
    _start(handler, clock, "pending", agent_key=MARKET, t=2.0)
    market = _row(handler.get_agent_stats(), MARKET)
    assert market["calls"] == 2
    assert market["duration"] == pytest.approx(1.0)

    # Replay of the error terminal event must not double count.
    _error(handler, clock, "err", t=3.0)
    assert _row(handler.get_agent_stats(), NEWS)["calls"] == 1


# -- TC-O6-06: fresh handler has no prior-run leakage (NFR-01) -------------
def test_tc_o6_06_fresh_handler_isolated():
    first, clock = _handler()
    _start(first, clock, "m1", agent_key=MARKET, t=0.0)
    _end(first, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)
    assert _row(first.get_agent_stats(), MARKET)["calls"] == 1

    second, clock2 = _handler()
    _start(second, clock2, "n1", agent_key=NEWS, t=0.0)
    _end(second, clock2, "n1", input_tokens=80, output_tokens=15, t=0.8)

    stats = second.get_agent_stats()
    assert _row(stats, MARKET) is None
    assert _row(stats, NEWS)["calls"] == 1
    assert stats["unattributed_calls"] == 0


# -- TC-O6-08: in-scope missing identity -> unattributed (FR-01) ----------
def test_tc_o6_08_in_scope_missing_identity():
    handler, clock = _handler()
    _start(handler, clock, "m1", agent_key=MARKET, t=0.0)
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)
    before = _row(handler.get_agent_stats(), MARKET).copy()

    # Explicitly in-scope call with missing identity.
    _start(handler, clock, "u1", scope="analyst", agent_key=None, t=1.0)
    _end(handler, clock, "u1", input_tokens=10, output_tokens=5, t=2.0)

    stats = handler.get_agent_stats()
    assert stats["unattributed_calls"] == 1
    assert _row(stats, MARKET) == before

    # Replaying the same start must not count the invocation again.
    _start(handler, clock, "u1", scope="analyst", agent_key=None, t=2.0)
    _start(handler, clock, "u1", scope="analyst", agent_key=None, t=3.0)
    stats = handler.get_agent_stats()
    assert stats["unattributed_calls"] == 1
    assert _row(stats, MARKET) == before


# -- TC-O6-09: legacy get_stats preserved + replay semantics (NFR-02) ------
def test_tc_o6_09_legacy_get_stats_preserved():
    handler, clock = _handler()
    _start(handler, clock, "m1", agent_key=MARKET, t=0.0)
    handler.on_tool_start({}, "tool-input")
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)

    assert handler.get_stats() == {
        "llm_calls": 1,
        "tool_calls": 1,
        "tokens_in": 100,
        "tokens_out": 20,
    }

    # A replayed start still increments the legacy counter (baseline behavior),
    # while the new per-Analyst surface dedups the replay.
    _start(handler, clock, "m1", agent_key=MARKET, t=1.0)
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)
    assert handler.get_stats() == {
        "llm_calls": 2,
        "tool_calls": 1,
        "tokens_in": 200,
        "tokens_out": 40,
    }
    assert _row(handler.get_agent_stats(), MARKET)["calls"] == 1

    # No-argument handler remains valid and just reports empty named stats.
    bare = StatsCallbackHandler()
    assert bare.get_stats() == {
        "llm_calls": 0,
        "tool_calls": 0,
        "tokens_in": 0,
        "tokens_out": 0,
    }
    assert bare.get_agent_stats() == {"analysts": {}, "unattributed_calls": 0}


# -- TC-O6-10: empty, unknown and non-string keys -> unattributed (FR-01) --
def test_tc_o6_10_empty_and_unknown_keys():
    handler, clock = _handler()
    # Empty key.
    _start(handler, clock, "e1", scope="analyst", agent_key="", t=0.0)
    _end(handler, clock, "e1", input_tokens=10, output_tokens=5, t=1.0)
    # Unknown key not in the selected set.
    _start(handler, clock, "k1", scope="analyst", agent_key="fundamentals", t=1.0)
    _end(handler, clock, "k1", input_tokens=10, output_tokens=5, t=2.0)
    # Non-string, unhashable key must be invalid before set membership.
    _start(handler, clock, "b1", scope="analyst", agent_key=["market"], t=2.0)
    _end(handler, clock, "b1", input_tokens=10, output_tokens=5, t=3.0)

    stats = handler.get_agent_stats()
    assert stats["unattributed_calls"] == 3
    assert stats["analysts"] == {}

    # Replaying each distinct start increments at most once per run_id.
    _start(handler, clock, "e1", scope="analyst", agent_key="", t=3.0)
    _start(handler, clock, "k1", scope="analyst", agent_key="fundamentals", t=4.0)
    _start(handler, clock, "b1", scope="analyst", agent_key=["market"], t=5.0)
    stats = handler.get_agent_stats()
    assert stats["unattributed_calls"] == 3
    assert stats["analysts"] == {}


# -- TC-O6-10b: duplicate start before terminal (in-scope missing/invalid key)
@pytest.mark.parametrize(
    "agent_key",
    [None, "fundamentals"],
    ids=["missing-key", "unknown-key"],
)
def test_tc_o6_10b_duplicate_start_before_terminal_unattributed(agent_key):
    handler, clock = _handler()
    # Seed one completed, valid Market call so "unchanged" is meaningful.
    _start(handler, clock, "m1", agent_key=MARKET, t=0.0)
    _end(handler, clock, "m1", input_tokens=100, output_tokens=20, t=1.0)
    before = copy.deepcopy(handler.get_agent_stats()["analysts"])
    assert handler.get_agent_stats()["unattributed_calls"] == 0
    llm_baseline = handler.get_stats()["llm_calls"]

    # Two starts for the same run_id, before any terminal callback.
    _start(handler, clock, "u1", scope="analyst", agent_key=agent_key, t=1.0)
    _start(handler, clock, "u1", scope="analyst", agent_key=agent_key, t=1.5)

    # Before terminal: counted once, named rows unchanged, legacy counted both.
    before_terminal = handler.get_agent_stats()
    assert before_terminal["unattributed_calls"] == 1
    assert before_terminal["analysts"] == before
    assert handler.get_stats()["llm_calls"] == llm_baseline + 2

    # Terminal callback for the same run_id.
    _end(handler, clock, "u1", input_tokens=10, output_tokens=5, t=2.0)

    # After terminal: still exactly one, named rows still unchanged.
    after_terminal = handler.get_agent_stats()
    assert after_terminal["unattributed_calls"] == 1
    assert after_terminal["analysts"] == before
    assert handler.get_stats()["llm_calls"] == llm_baseline + 2


# -- Known out-of-scope calls are excluded from both new statistics --------
def test_out_of_scope_call_excluded_from_named_and_unattributed():
    handler, clock = _handler()
    _start(handler, clock, "oos", scope="research", agent_key=MARKET, t=0.0)
    _end(handler, clock, "oos", input_tokens=100, output_tokens=20, t=1.0)

    stats = handler.get_agent_stats()
    assert stats["analysts"] == {}
    assert stats["unattributed_calls"] == 0


# -- Offline guard evidence: network attempts are blocked ------------------
def test_offline_guard_blocks_network():
    with pytest.raises(OSError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("127.0.0.1", 9))
    with pytest.raises(OSError):
        socket.getaddrinfo("example.com", 80)
