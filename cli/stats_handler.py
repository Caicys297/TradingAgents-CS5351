import threading
import time
from collections.abc import Callable
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult

_SCOPE_KEY = "scope"
_AGENT_KEY = "agent_key"


class _AnalystTotals:
    """Mutable per-Analyst accumulator for one selected call scope."""

    __slots__ = ("calls", "input_tokens", "output_tokens", "input_known", "output_known", "duration")

    def __init__(self) -> None:
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.input_known = 0
        self.output_known = 0
        self.duration = 0.0


class StatsCallbackHandler(BaseCallbackHandler):
    """Callback handler that tracks LLM calls, tool calls, and token usage.

    The legacy run-level counters (``get_stats``) are unchanged. O6 adds
    per-Analyst statistics (``get_agent_stats``) for calls whose callback
    metadata carries ``scope="analyst"`` and an ``agent_key`` belonging to the
    caller-supplied set of validated ``spec.key`` values for the current run.

    The set of valid analyst keys is supplied by the caller. The no-argument
    constructor stays valid and simply attributes no calls to named Analysts.
    """

    def __init__(
        self,
        selected_analyst_keys: set[str] | None = None,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self.llm_calls = 0
        self.tool_calls = 0
        self.tokens_in = 0
        self.tokens_out = 0

        self._valid_keys: set[str] = set(selected_analyst_keys or ())
        self._clock: Callable[[], float] = clock or time.monotonic
        self._analysts: dict[str, _AnalystTotals] = {}
        self._pending: dict[str, dict[str, Any]] = {}
        self._finalized: set[str] = set()
        self.unattributed_calls = 0

    # -- invocation identity -------------------------------------------------
    def _begin_invocation(self, run_id: Any, metadata: dict[str, Any]) -> None:
        """Count a distinct invocation when its start is first observed.

        Replay of a start for a ``run_id`` already seen or finalized is ignored.
        """
        rid = str(run_id)
        if rid in self._pending or rid in self._finalized:
            # A repeated start for an invocation already seen or completed.
            return
        scope = metadata.get(_SCOPE_KEY) if metadata else None
        agent_key = metadata.get(_AGENT_KEY) if metadata else None
        started = self._clock()

        if scope is None:
            # No explicit scope: outside the attribution contract; exclude.
            return
        if scope != "analyst":
            # Known out-of-scope call: excluded from named rows and unattributed.
            return
        if not isinstance(agent_key, str) or not agent_key or agent_key not in self._valid_keys:
            # In-scope call with missing or invalid identity (non-string keys are
            # invalid before set membership). Record the run_id so a replayed
            # start cannot increment the counter again for the same invocation.
            self.unattributed_calls += 1
            self._finalized.add(rid)
            return

        row = self._analysts.get(agent_key)
        if row is None:
            row = _AnalystTotals()
            self._analysts[agent_key] = row
        row.calls += 1
        self._pending[rid] = {"agent_key": agent_key, "started": started}

    def _finalize(self, run_id: Any, usage: dict[str, Any] | None) -> None:
        """Accrue duration and usage on a terminal event once per ``run_id``."""
        rid = str(run_id)
        pending = self._pending.pop(rid, None)
        if pending is None:
            # No matching counted start, or a replay of a finalized invocation.
            return
        # Remember the terminal event so later replays stay deduplicated even
        # if a stray start arrives again afterwards.
        self._finalized.add(rid)

        row = self._analysts[pending["agent_key"]]
        row.duration += self._clock() - pending["started"]

        if usage is not None:
            if "input_tokens" in usage:
                row.input_tokens += usage["input_tokens"]
                row.input_known += 1
            if "output_tokens" in usage:
                row.output_tokens += usage["output_tokens"]
                row.output_known += 1

    @staticmethod
    def _usage_of(response: LLMResult) -> dict[str, Any] | None:
        try:
            generation = response.generations[0][0]
        except (IndexError, TypeError):
            return None
        if not hasattr(generation, "message"):
            return None
        message = generation.message
        if not isinstance(message, AIMessage):
            return None
        return getattr(message, "usage_metadata", None)

    # -- legacy callbacks ----------------------------------------------------
    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """Increment LLM call counter when an LLM starts."""
        with self._lock:
            self.llm_calls += 1
            self._begin_invocation(kwargs.get("run_id"), kwargs.get("metadata") or {})

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        **kwargs: Any,
    ) -> None:
        """Increment LLM call counter when a chat model starts."""
        with self._lock:
            self.llm_calls += 1
            self._begin_invocation(kwargs.get("run_id"), kwargs.get("metadata") or {})

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Extract token usage from LLM response."""
        usage_metadata = self._usage_of(response)
        with self._lock:
            if usage_metadata:
                self.tokens_in += usage_metadata.get("input_tokens", 0)
                self.tokens_out += usage_metadata.get("output_tokens", 0)
            self._finalize(kwargs.get("run_id"), usage_metadata)

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Finalize an invocation that ended in error (no usage reported)."""
        with self._lock:
            self._finalize(kwargs.get("run_id"), None)

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Increment tool call counter when a tool starts."""
        with self._lock:
            self.tool_calls += 1

    def get_stats(self) -> dict[str, Any]:
        """Return current statistics."""
        with self._lock:
            return {
                "llm_calls": self.llm_calls,
                "tool_calls": self.tool_calls,
                "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out,
            }

    # -- O6 additive accessor ------------------------------------------------
    @staticmethod
    def _field(total: int, known: int, calls: int) -> dict[str, Any]:
        if calls == 0 or known == 0:
            return {"value": None, "status": "unknown"}
        status = "complete" if known == calls else "partial"
        return {"value": total, "status": status}

    def get_agent_stats(self) -> dict[str, Any]:
        """Return per-Analyst statistics plus the unattributed in-scope count.

        Each named row reports distinct calls, cumulative duration in seconds,
        and input/output token value with independent completeness status
        (``complete``, ``partial`` or ``unknown``).
        """
        with self._lock:
            analysts: dict[str, dict[str, Any]] = {}
            for key, row in self._analysts.items():
                analysts[key] = {
                    "calls": row.calls,
                    "duration": row.duration,
                    "input_tokens": self._field(row.input_tokens, row.input_known, row.calls),
                    "output_tokens": self._field(row.output_tokens, row.output_known, row.calls),
                }
            return {
                "analysts": analysts,
                "unattributed_calls": self.unattributed_calls,
            }
