"""O4 Decision Evidence Gate — pure, offline evidence-presence checker.

This module implements the approved **Stage 1** contract from
``docs/req/O4-Implementation-Plan-v0.1-DRAFT.md`` (O4-EXEC-v0.2-DRAFT) and
``docs/req/O4-Test-Plan.md`` (O4-TEST-v0.5). It is a *pure* function over the
analyst-report fields of an ``AgentState``-shaped mapping:

- deterministic (no clock, no randomness);
- offline (no network, no LLM, no external I/O);
- free of persistent I/O;
- independent of the Graph/CLI runtime — it neither imports nor drives them.

It does **not** mutate its inputs, does **not** apply the G1/S2/B1 runtime
integration, and does **not** touch ``final_trade_decision``. Stage 2 wires the
result into the Graph/CLI publication path; that is out of scope here.

Behaviour implemented (see the O4 requirements registry and test plan):

- A selected analyst's required report must be present and non-empty.
  Whitespace-only text counts as missing (O4-FR-03).
- Unselected analysts are ``not_required`` and can never downgrade (O4-FR-06).
- A structurally non-empty report that merely mentions ``N/A`` / unavailable
  source text stays ``present``; v1 has no whole-report sentinel recognition
  (O4-FR-04 is ``Won't``).
- Missing required evidence downgrades the effective rating to ``REVIEW``
  (O4-FR-03, O4-INV-01).
- An existing ``REVIEW`` is never upgraded (O4-FR-05, O4-INV-02).
- Original-rating precedence: ``final_rating`` first, else the rating parsed
  from the decision body; two clearly-present, disagreeing sources are a
  conflict that downgrades to ``REVIEW`` (O4-FR-16, O4-T-25).
- An unknown analyst key / unrecognisable configuration is a *contract error*
  and raises ``ValueError`` (O4-FR-15, O4-T-18); it is never silently
  ``not_required`` and never a normal ``REVIEW``.
- A recoverable internal evidence-processing failure is handled by this
  production logic and fails closed to ``REVIEW`` with a diagnostic reason
  (O4-FR-09, O4-INV-04, O4-T-07). Configuration errors are kept outside that
  handler so they still propagate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from tradingagents.agents.rating import RATING_REVIEW, extract_rating
from tradingagents.graph.analyst_execution import ANALYST_NODE_SPECS

# The four analyst report fields the gate inspects, in stable order. A selected
# analyst maps to exactly one of these (see ``ANALYST_NODE_SPECS``).
REQUIRED_REPORT_KEYS: tuple[str, ...] = (
    "market_report",
    "sentiment_report",
    "news_report",
    "fundamentals_report",
)

# Per-item status vocabulary.
STATUS_PRESENT = "present"
STATUS_MISSING = "missing"
STATUS_NOT_REQUIRED = "not_required"

# Verdict vocabulary.
VERDICT_VALID = "valid"
VERDICT_REVIEW = "review"

# ``error_kind`` vocabulary for the structured result.
ERROR_NONE = "none"
ERROR_EVIDENCE = "evidence"
ERROR_CHECKER_FAILURE = "checker_failure"
ERROR_RATING_CONFLICT = "rating_conflict"


@dataclass(frozen=True)
class EvidenceItem:
    """One required evidence field and its classification."""

    key: str
    status: str


@dataclass(frozen=True)
class GateResult:
    """Structured outcome of a single evidence check.

    ``effective_rating`` is the original rating when the verdict is ``valid``
    (or when a pre-existing ``REVIEW`` is preserved), otherwise ``REVIEW``.
    ``reason`` is empty on a clean ``valid`` result and a short diagnostic
    otherwise. ``items`` records one entry per inspected report field.
    """

    verdict: str
    effective_rating: str
    items: tuple[EvidenceItem, ...] = ()
    reason: str = ""
    error_kind: str = ERROR_NONE

    @property
    def failing(self) -> tuple[str, ...]:
        """The report keys classified ``missing`` (empty tuple when none)."""
        return tuple(item.key for item in self.items if item.status == STATUS_MISSING)

    @property
    def statuses(self) -> dict[str, str]:
        """Map of report key -> status, for all inspected fields."""
        return {item.key: item.status for item in self.items}


def _classify_report(value: object) -> str:
    """Classify one report value as present or missing.

    A report is ``present`` when it is a string with non-whitespace content.
    Everything else (``None``, empty string, whitespace-only, or a non-string)
    is ``missing``. This is the real production computation point that
    failure-injection tests patch; a raised exception here is treated as a
    recoverable evidence-processing failure by ``check_evidence``.
    """
    if not isinstance(value, str):
        return STATUS_MISSING
    if not value.strip():
        return STATUS_MISSING
    return STATUS_PRESENT


def _select_required_reports(
    selected_analysts: Sequence[str] | None,
) -> dict[str, bool]:
    """Map each of the four report fields to whether it is required.

    Resolution is via ``ANALYST_NODE_SPECS`` (the single source of analyst ->
    report mapping). An unknown analyst key is a contract error and raises
    ``ValueError``; this mirrors ``build_analyst_execution_plan`` and must not
    be swallowed by the recoverable-failure handler.
    """
    required = dict.fromkeys(REQUIRED_REPORT_KEYS, False)
    if selected_analysts is None:
        raise ValueError("selected_analysts is required for the evidence gate")

    seen = set()
    for analyst_key in selected_analysts:
        if not isinstance(analyst_key, str):
            raise ValueError(f"unknown analyst key: {analyst_key!r}")
        spec = ANALYST_NODE_SPECS.get(analyst_key)
        if spec is None:
            raise ValueError(f"unknown analyst key: {analyst_key!r}")
        seen.add(analyst_key)
        required[spec.report_key] = True

    if not seen:
        raise ValueError("at least one analyst must be selected")

    return required


def _resolve_original_rating(state: Mapping[str, object]) -> tuple[str, str, str]:
    """Resolve the original pre-gate rating and detect source conflict.

    Precedence (O4-FR-16, O4-T-25):
    - ``final_rating`` present -> that rating is the original;
    - else a rating parsed from ``final_trade_decision`` is the original;
    - if both are clearly present and disagree -> conflict (``REVIEW``).

    Returns ``(effective_rating, error_kind, reason)`` where ``error_kind`` is
    ``ERROR_RATING_CONFLICT`` on a disagreement or the original is already
    ``REVIEW`` (preserved), and ``ERROR_NONE`` otherwise. The returned rating
    is the original candidate; the caller decides whether evidence downgrades.
    """
    final_rating = state.get("final_rating")
    body = state.get("final_trade_decision", "")

    explicit = final_rating.strip() if isinstance(final_rating, str) else ""
    parsed = extract_rating(body if isinstance(body, str) else "")

    # A pre-existing REVIEW is preserved and never upgraded (O4-FR-05).
    if explicit == RATING_REVIEW:
        return RATING_REVIEW, ERROR_NONE, ""
    if parsed == RATING_REVIEW and not explicit:
        return RATING_REVIEW, ERROR_NONE, ""

    if explicit and parsed and explicit != parsed:
        return (
            RATING_REVIEW,
            ERROR_RATING_CONFLICT,
            f"rating conflict: final_rating={explicit!r} vs decision body={parsed!r}",
        )

    if explicit:
        return explicit, ERROR_NONE, ""
    if parsed:
        return parsed, ERROR_NONE, ""
    # No rating anywhere: this is the review sentinel, not a tradeable call.
    return RATING_REVIEW, ERROR_NONE, ""


def check_evidence(
    state: Mapping[str, object],
    selected_analysts: Sequence[str] | None,
) -> GateResult:
    """Check analyst evidence and return a structured gate result.

    Parameters
    ----------
    state:
        An ``AgentState``-shaped mapping. Only ``market_report``,
        ``sentiment_report``, ``news_report``, ``fundamentals_report``,
        ``final_rating`` and ``final_trade_decision`` are read.
    selected_analysts:
        The analyst keys selected for this run (``market``, ``social``,
        ``news``, ``fundamentals``). An unknown key raises ``ValueError``.

    The checker is pure: it does not mutate ``state``. ``final_trade_decision``
    is only read, never rewritten.

    Configuration / contract errors (unknown analyst key, missing selection)
    raise ``ValueError`` *before* the recoverable-failure handler, so they
    abort rather than being converted to ``REVIEW``. Any other unexpected
    failure while classifying evidence is treated as recoverable and fails
    closed to ``REVIEW`` with a diagnostic reason (O4-T-07).
    """
    # ---- Contract resolution: NOT wrapped in the recoverable handler. ----
    # Analyst configuration is validated here, *before* any recoverable-error
    # handling. An unknown analyst key / unrecognisable configuration raises
    # ValueError (O4-FR-15, O4-T-18); it is a contract error that must abort
    # rather than be converted to a normal REVIEW.
    required = _select_required_reports(selected_analysts)

    # ---- Recoverable internal computation: fail closed on internal failure. ----
    # Both the original-rating resolution and the evidence classification are
    # recoverable internal computations. Any unexpected error in either (a
    # recoverable internal computation failure, not a configuration error
    # already handled above) is caught here and fails closed to REVIEW with a
    # diagnostic reason (O4-FR-09, O4-INV-04, O4-T-07). ``final_trade_decision``
    # is only read via ``state.get`` and never mutated.
    try:
        original_rating, rating_error_kind, rating_reason = _resolve_original_rating(state)

        items: list[EvidenceItem] = []
        for key in REQUIRED_REPORT_KEYS:
            if not required[key]:
                items.append(EvidenceItem(key=key, status=STATUS_NOT_REQUIRED))
                continue
            status = _classify_report(state.get(key))
            items.append(EvidenceItem(key=key, status=status))
    except Exception as exc:  # noqa: BLE001 - recoverable by design (O4-FR-09)
        return GateResult(
            verdict=VERDICT_REVIEW,
            effective_rating=RATING_REVIEW,
            items=(),
            reason=f"checker recovered from internal computation failure: {exc}",
            error_kind=ERROR_CHECKER_FAILURE,
        )

    failing = tuple(i.key for i in items if i.status == STATUS_MISSING)

    # Rating conflict or preserved REVIEW dominates any evidence downgrade.
    if rating_error_kind == ERROR_RATING_CONFLICT:
        return GateResult(
            verdict=VERDICT_REVIEW,
            effective_rating=RATING_REVIEW,
            items=tuple(items),
            reason=rating_reason,
            error_kind=ERROR_RATING_CONFLICT,
        )

    if original_rating == RATING_REVIEW:
        # Existing REVIEW is never upgraded; missing evidence is still named.
        reason = (
            f"required evidence missing: {', '.join(failing)}"
            if failing
            else "original rating is REVIEW; preserved"
        )
        return GateResult(
            verdict=VERDICT_REVIEW,
            effective_rating=RATING_REVIEW,
            items=tuple(items),
            reason=reason,
            error_kind=ERROR_EVIDENCE if failing else ERROR_NONE,
        )

    if failing:
        return GateResult(
            verdict=VERDICT_REVIEW,
            effective_rating=RATING_REVIEW,
            items=tuple(items),
            reason=f"required evidence missing: {', '.join(failing)}",
            error_kind=ERROR_EVIDENCE,
        )

    return GateResult(
        verdict=VERDICT_VALID,
        effective_rating=original_rating,
        items=tuple(items),
        reason="",
        error_kind=ERROR_NONE,
    )


__all__ = [
    "EvidenceItem",
    "GateResult",
    "REQUIRED_REPORT_KEYS",
    "STATUS_PRESENT",
    "STATUS_MISSING",
    "STATUS_NOT_REQUIRED",
    "VERDICT_VALID",
    "VERDICT_REVIEW",
    "ERROR_NONE",
    "ERROR_EVIDENCE",
    "ERROR_CHECKER_FAILURE",
    "ERROR_RATING_CONFLICT",
    "check_evidence",
]
