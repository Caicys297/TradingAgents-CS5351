"""O5 S1 static evidence-contract cases (test plan v1.7, inventory section 5).

The single test-local entry ``_static_o5_contract_errors`` validates one event
dictionary against the Interface section 4 contract. It is a pure static
checker: it does not emit evidence, call the selector, read a clock, touch a
sink, or look up an expected answer by case ID. Valid controls and mutants use
that same entry; each row keeps its own independently specified expectation.

Scope note (inventory section 5, 6): these checks are schema shape only. They
do not prove production emission, builder stages or invariant enforcement.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from tradingagents.dataflows.vendors.yahoo import news

RULES = "o5-rules-v1.1-draft"
OCCURRED_AT = "2026-09-28T00:00:00Z"

VARIANTS = (
    "V-SELECTED",
    "V-FILTERED-EMPTY",
    "V-LIMIT-ZERO",
    "V-UPSTREAM-EMPTY",
    "V-VENDOR",
    "V-PARTIAL",
    "V-INVARIANT",
    "V-INVALID-REQUEST",
)

COMMON_KEYS = frozenset({"variant", "action", "trigger", "disposition", "rules_version",
                         "occurred_at"})

# Legal (variant, action, trigger, disposition) tuples -- Interface 4.3 M1-M11.
LEGAL_TUPLES = frozenset({
    ("V-SELECTED", "SERVE_SELECTED", "OK", "OK"),
    ("V-FILTERED-EMPTY", "SERVE_FILTERED_EMPTY", "NO_RELEVANT_NEWS", "FILTERED_TO_EMPTY"),
    ("V-LIMIT-ZERO", "SKIP_CLASSIFICATION", "LIMIT_ZERO", "LIMIT_ZERO"),
    ("V-UPSTREAM-EMPTY", "SERVE_UPSTREAM_EMPTY", "UPSTREAM_EMPTY", "UPSTREAM_UNAVAILABLE"),
    ("V-VENDOR", "VENDOR_UNAVAILABLE", "VENDOR_TIMEOUT", "UPSTREAM_UNAVAILABLE"),
    ("V-VENDOR", "VENDOR_UNAVAILABLE", "VENDOR_RATE_LIMIT", "UPSTREAM_UNAVAILABLE"),
    ("V-VENDOR", "VENDOR_UNAVAILABLE", "VENDOR_PAYLOAD_INVALID", "UPSTREAM_UNAVAILABLE"),
    ("V-VENDOR", "VENDOR_UNAVAILABLE", "VENDOR_UNAVAILABLE", "UPSTREAM_UNAVAILABLE"),
    ("V-PARTIAL", "PARTIAL_UPSTREAM", "PARTIAL_QUERY_FAILURE", "PARTIAL_UPSTREAM"),
    ("V-INVARIANT", "SUPPRESS_BATCH", "INVARIANT_VIOLATION", "INVARIANT_VIOLATION"),
    ("V-INVALID-REQUEST", "REJECT_REQUEST", "INVALID_REQUEST", "INVALID_REQUEST"),
})

VENDOR_TRIGGERS = frozenset({"VENDOR_TIMEOUT", "VENDOR_RATE_LIMIT", "VENDOR_PAYLOAD_INVALID",
                             "VENDOR_UNAVAILABLE"})
EMPTY_KINDS = frozenset({"ALL_IRRELEVANT", "ALL_INVALID", "ALL_OUT_OF_WINDOW",
                         "MIXED_NONE_RELEVANT"})
INVARIANT_NAMES = frozenset({"INV-O5-01", "INV-O5-02", "INV-O5-03", "INV-O5-04"})

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# Variant-specific required keys (non-null unless the variant's nullable set says so).
REQUIRED_KEYS = {
    "V-SELECTED": frozenset({"batch_id", "input_count", "selected_count", "reason_counts",
                             "executed_query_count", "pre_filter_candidate_count"}),
    "V-FILTERED-EMPTY": frozenset({"batch_id", "input_count", "selected_count", "reason_counts",
                                   "executed_query_count", "pre_filter_candidate_count",
                                   "empty_kind"}),
    "V-LIMIT-ZERO": frozenset({"input_count", "executed_query_count", "pre_filter_candidate_count"}),
    "V-UPSTREAM-EMPTY": frozenset({"executed_query_count", "pre_filter_candidate_count"}),
    "V-VENDOR": frozenset({"vendor", "method"}),
    "V-PARTIAL": frozenset({"executed_query_count", "queries_failed", "pre_filter_candidate_count"}),
    "V-INVARIANT": frozenset({"violated_invariant", "batch_id", "pre_suppression_selected_count",
                              "published_selected_count"}),
    "V-INVALID-REQUEST": frozenset({"field", "reason"}),
}

OPTIONAL_KEYS = {
    "V-SELECTED": frozenset({"matched_topic_counts"}),
    "V-FILTERED-EMPTY": frozenset({"matched_topic_counts"}),
    "V-LIMIT-ZERO": frozenset(),
    "V-UPSTREAM-EMPTY": frozenset(),
    "V-VENDOR": frozenset({"executed_query_count"}),
    "V-PARTIAL": frozenset(),
    "V-INVARIANT": frozenset({"input_count", "reason_counts"}),
    "V-INVALID-REQUEST": frozenset(),
}

# Keys required to be present but whose value must be None.
REQUIRED_NULL = {
    "V-SELECTED": frozenset(),
    "V-FILTERED-EMPTY": frozenset(),
    "V-LIMIT-ZERO": frozenset({"batch_id"}),
    "V-UPSTREAM-EMPTY": frozenset({"batch_id", "input_count", "selected_count", "reason_counts"}),
    "V-VENDOR": frozenset({"batch_id", "input_count", "selected_count", "reason_counts",
                           "pre_filter_candidate_count"}),
    "V-PARTIAL": frozenset({"batch_id", "input_count", "reason_counts"}),
    "V-INVARIANT": frozenset(),
    "V-INVALID-REQUEST": frozenset({"rules_version"}),
}

# Integer-valued keys (must be int, excluding bool).
INT_KEYS = frozenset({"input_count", "selected_count", "executed_query_count",
                      "pre_filter_candidate_count", "queries_failed",
                      "pre_suppression_selected_count", "published_selected_count"})
STR_KEYS = frozenset({"batch_id", "vendor", "method", "field", "reason", "empty_kind",
                      "violated_invariant"})


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_timestamp(value) -> bool:
    if not isinstance(value, str) or not _TIMESTAMP_RE.match(value):
        return False
    day = value[8:10]
    month = value[5:7]
    hour = value[11:13]
    minute = value[14:16]
    second = value[17:19]
    if not (1 <= int(month) <= 12 and 1 <= int(day) <= 31):
        return False
    return int(hour) <= 23 and int(minute) <= 59 and int(second) <= 59


def _static_o5_contract_errors(event: object) -> tuple[str, ...]:
    """Return a sorted tuple of deterministic diagnostics; empty means accepted."""

    errors: list[str] = []
    if not isinstance(event, Mapping):
        return ("type:root",)

    variant = event.get("variant")
    if variant not in VARIANTS:
        return ("enum:variant",)

    required = REQUIRED_KEYS[variant] | REQUIRED_NULL[variant]
    permitted = COMMON_KEYS | required | OPTIONAL_KEYS[variant]
    for key in sorted(COMMON_KEYS | required):
        if key not in event:
            errors.append(f"missing:{key}")
    for key in sorted(set(event) - permitted):
        errors.append(f"prohibited:{key}")

    if errors:
        return tuple(sorted(errors))

    rules_version = event.get("rules_version")
    if variant in ("V-INVALID-REQUEST",):
        if rules_version is not None:
            errors.append("nullability:rules_version")
    elif variant == "V-VENDOR":
        if not (rules_version is None or isinstance(rules_version, str)):
            errors.append("type:rules_version")
    else:
        if not isinstance(rules_version, str):
            errors.append("nullability:rules_version")

    if not _valid_timestamp(event.get("occurred_at")):
        errors.append("type:occurred_at")

    for key in sorted(required):
        if key in REQUIRED_NULL[variant]:
            if event.get(key) is not None:
                errors.append(f"nullability:{key}")
            continue
        value = event.get(key)
        if key in STR_KEYS and not (isinstance(value, str) and value):
            errors.append(f"type:{key}")
        if key in INT_KEYS and not _is_int(value):
            errors.append(f"type:{key}")
        if key == "reason_counts" and not isinstance(value, Mapping):
            errors.append(f"type:{key}")
        if key == "batch_id" and not (isinstance(value, str) and value):
            errors.append(f"type:{key}")

    for key in sorted(OPTIONAL_KEYS[variant]):
        if key in event:
            value = event[key]
            if key in INT_KEYS and not _is_int(value):
                errors.append(f"type:{key}")
            if key in ("reason_counts", "matched_topic_counts") and not isinstance(value, Mapping):
                errors.append(f"type:{key}")

    if variant == "V-FILTERED-EMPTY":
        kind = event.get("empty_kind")
        if kind is not None and kind not in EMPTY_KINDS:
            errors.append("enum:empty_kind")
        if _is_int(event.get("selected_count")) and event.get("selected_count") != 0:
            errors.append("range:selected_count")
        if _is_int(event.get("input_count")) and event.get("input_count") < 1:
            errors.append("range:input_count")

    if variant == "V-SELECTED":
        if _is_int(event.get("selected_count")) and event.get("selected_count") < 1:
            errors.append("range:selected_count")
        if _is_int(event.get("pre_filter_candidate_count")) and event.get("pre_filter_candidate_count") < 1:
            errors.append("range:pre_filter_candidate_count")
        for key in ("executed_query_count", "input_count"):
            if _is_int(event.get(key)) and event[key] < 0:
                errors.append(f"range:{key}")

    if variant == "V-LIMIT-ZERO":
        for key in ("input_count", "executed_query_count", "pre_filter_candidate_count"):
            if _is_int(event.get(key)) and event[key] < 0:
                errors.append(f"range:{key}")

    if variant == "V-UPSTREAM-EMPTY":
        if _is_int(event.get("executed_query_count")) and event["executed_query_count"] < 0:
            errors.append("range:executed_query_count")
        if _is_int(event.get("pre_filter_candidate_count")) and event["pre_filter_candidate_count"] != 0:
            errors.append("range:pre_filter_candidate_count")

    if variant == "V-VENDOR":
        if event.get("vendor") == "":
            errors.append("type:vendor")
        if event.get("method") == "":
            errors.append("type:method")
        if "executed_query_count" in event and _is_int(event["executed_query_count"]) and event[
                "executed_query_count"] < 0:
            errors.append("range:executed_query_count")

    if variant == "V-PARTIAL":
        executed = event.get("executed_query_count")
        failed = event.get("queries_failed")
        candidates = event.get("pre_filter_candidate_count")
        if _is_int(executed) and executed < 1:
            errors.append("range:executed_query_count")
        if _is_int(failed) and failed < 1:
            errors.append("range:queries_failed")
        if _is_int(executed) and _is_int(failed) and not (1 <= failed <= executed):
            errors.append("relation:queries_failed")
        if _is_int(candidates) and candidates < 0:
            errors.append("range:pre_filter_candidate_count")

    if variant == "V-INVARIANT":
        if event.get("violated_invariant") not in INVARIANT_NAMES:
            errors.append("enum:violated_invariant")
        if _is_int(event.get("published_selected_count")) and event["published_selected_count"] != 0:
            errors.append("range:published_selected_count")
        if _is_int(event.get("pre_suppression_selected_count")) and event[
                "pre_suppression_selected_count"] < 0:
            errors.append("range:pre_suppression_selected_count")


    combination = (variant, event.get("action"), event.get("trigger"), event.get("disposition"))
    if tuple(combination) not in LEGAL_TUPLES:
        if variant == "V-VENDOR" and event.get("trigger") not in VENDOR_TRIGGERS:
            errors.append("enum:trigger")
        else:
            errors.append("combination:variant_action_trigger_disposition")

    return tuple(sorted(set(errors)))


# --------------------------------------------------------------------------- controls


def _selected(**overrides):
    control = {
        "variant": "V-SELECTED", "action": "SERVE_SELECTED", "trigger": "OK", "disposition": "OK",
        "rules_version": RULES, "occurred_at": OCCURRED_AT, "batch_id": "b:abc",
        "input_count": 4, "selected_count": 1,
        "reason_counts": {"SELECTED": 1, "NO_MACRO_EVIDENCE": 3},
        "executed_query_count": 2, "pre_filter_candidate_count": 4,
    }
    control.update(overrides)
    return control


def _filtered_empty(**overrides):
    control = {
        "variant": "V-FILTERED-EMPTY", "action": "SERVE_FILTERED_EMPTY",
        "trigger": "NO_RELEVANT_NEWS", "disposition": "FILTERED_TO_EMPTY",
        "rules_version": RULES, "occurred_at": OCCURRED_AT, "batch_id": "b:def",
        "input_count": 2, "selected_count": 0, "reason_counts": {"INVALID_TITLE": 2},
        "executed_query_count": 2, "pre_filter_candidate_count": 2, "empty_kind": "ALL_INVALID",
    }
    control.update(overrides)
    return control


def _limit_zero(**overrides):
    control = {
        "variant": "V-LIMIT-ZERO", "action": "SKIP_CLASSIFICATION", "trigger": "LIMIT_ZERO",
        "disposition": "LIMIT_ZERO", "rules_version": RULES, "occurred_at": OCCURRED_AT,
        "batch_id": None, "input_count": 0, "executed_query_count": 0,
        "pre_filter_candidate_count": 0,
    }
    control.update(overrides)
    return control


def _upstream_empty(**overrides):
    control = {
        "variant": "V-UPSTREAM-EMPTY", "action": "SERVE_UPSTREAM_EMPTY", "trigger": "UPSTREAM_EMPTY",
        "disposition": "UPSTREAM_UNAVAILABLE", "rules_version": RULES, "occurred_at": OCCURRED_AT,
        "batch_id": None, "input_count": None, "selected_count": None, "reason_counts": None,
        "executed_query_count": 1, "pre_filter_candidate_count": 0,
    }
    control.update(overrides)
    return control


def _vendor(trigger="VENDOR_TIMEOUT", **overrides):
    control = {
        "variant": "V-VENDOR", "action": "VENDOR_UNAVAILABLE", "trigger": trigger,
        "disposition": "UPSTREAM_UNAVAILABLE", "rules_version": RULES, "occurred_at": OCCURRED_AT,
        "vendor": "yfinance", "method": "get_global_news", "batch_id": None, "input_count": None,
        "selected_count": None, "reason_counts": None, "pre_filter_candidate_count": None,
    }
    control.update(overrides)
    return control


def _partial(executed=1, failed=1, candidates=1, **overrides):
    control = {
        "variant": "V-PARTIAL", "action": "PARTIAL_UPSTREAM", "trigger": "PARTIAL_QUERY_FAILURE",
        "disposition": "PARTIAL_UPSTREAM", "rules_version": RULES, "occurred_at": OCCURRED_AT,
        "batch_id": None, "input_count": None, "reason_counts": None,
        "executed_query_count": executed, "queries_failed": failed,
        "pre_filter_candidate_count": candidates,
    }
    control.update(overrides)
    return control


def _invariant(**overrides):
    control = {
        "variant": "V-INVARIANT", "action": "SUPPRESS_BATCH", "trigger": "INVARIANT_VIOLATION",
        "disposition": "INVARIANT_VIOLATION", "rules_version": RULES, "occurred_at": OCCURRED_AT,
        "violated_invariant": "INV-O5-02", "batch_id": "b:ghi",
        "pre_suppression_selected_count": 1, "published_selected_count": 0,
    }
    control.update(overrides)
    return control


def _invalid_request(**overrides):
    control = {
        "variant": "V-INVALID-REQUEST", "action": "REJECT_REQUEST", "trigger": "INVALID_REQUEST",
        "disposition": "INVALID_REQUEST", "rules_version": None, "occurred_at": OCCURRED_AT,
        "field": "limit", "reason": "must be non-negative",
    }
    control.update(overrides)
    return control


CONTROLS = {
    "V-SELECTED": _selected,
    "V-FILTERED-EMPTY": _filtered_empty,
    "V-LIMIT-ZERO": _limit_zero,
    "V-UPSTREAM-EMPTY": _upstream_empty,
    "V-VENDOR": _vendor,
    "V-PARTIAL": _partial,
    "V-INVARIANT": _invariant,
    "V-INVALID-REQUEST": _invalid_request,
}


def _run(control_factory, mutation):
    """Copy the control, assert it is accepted, then apply one mutation and re-check."""

    control = control_factory()
    assert _static_o5_contract_errors(control) == ()
    candidate = copy.deepcopy(control)
    mutation(candidate)
    snapshot = copy.deepcopy(candidate)
    errors = _static_o5_contract_errors(candidate)
    assert candidate == snapshot
    return errors


# --------------------------------------------------------------------------- I6 deletion


I6_CASES = [
    ("I6-VS-1", "V-SELECTED", "batch_id"),
    ("I6-VS-2", "V-SELECTED", "input_count"),
    ("I6-VS-3", "V-SELECTED", "selected_count"),
    ("I6-VS-4", "V-SELECTED", "reason_counts"),
    ("I6-VS-5", "V-SELECTED", "executed_query_count"),
    ("I6-VS-6", "V-SELECTED", "pre_filter_candidate_count"),
    ("I6-FE-1", "V-FILTERED-EMPTY", "batch_id"),
    ("I6-FE-2", "V-FILTERED-EMPTY", "input_count"),
    ("I6-FE-3", "V-FILTERED-EMPTY", "selected_count"),
    ("I6-FE-4", "V-FILTERED-EMPTY", "reason_counts"),
    ("I6-FE-5", "V-FILTERED-EMPTY", "executed_query_count"),
    ("I6-FE-6", "V-FILTERED-EMPTY", "pre_filter_candidate_count"),
    ("I6-FE-7", "V-FILTERED-EMPTY", "empty_kind"),
    ("I6-LZ-1", "V-LIMIT-ZERO", "batch_id"),
    ("I6-LZ-2", "V-LIMIT-ZERO", "input_count"),
    ("I6-LZ-3", "V-LIMIT-ZERO", "executed_query_count"),
    ("I6-LZ-4", "V-LIMIT-ZERO", "pre_filter_candidate_count"),
    ("I6-UE-1", "V-UPSTREAM-EMPTY", "batch_id"),
    ("I6-UE-2", "V-UPSTREAM-EMPTY", "input_count"),
    ("I6-UE-3", "V-UPSTREAM-EMPTY", "selected_count"),
    ("I6-UE-4", "V-UPSTREAM-EMPTY", "reason_counts"),
    ("I6-UE-5", "V-UPSTREAM-EMPTY", "executed_query_count"),
    ("I6-UE-6", "V-UPSTREAM-EMPTY", "pre_filter_candidate_count"),
    ("I6-VV-1", "V-VENDOR", "vendor"),
    ("I6-VV-2", "V-VENDOR", "method"),
    ("I6-VV-3", "V-VENDOR", "batch_id"),
    ("I6-VV-4", "V-VENDOR", "input_count"),
    ("I6-VV-5", "V-VENDOR", "selected_count"),
    ("I6-VV-6", "V-VENDOR", "reason_counts"),
    ("I6-VV-7", "V-VENDOR", "pre_filter_candidate_count"),
    ("I6-IV-1", "V-INVARIANT", "violated_invariant"),
    ("I6-IV-2", "V-INVARIANT", "batch_id"),
    ("I6-IV-3", "V-INVARIANT", "pre_suppression_selected_count"),
    ("I6-IV-4", "V-INVARIANT", "published_selected_count"),
    ("I6-IR-1", "V-INVALID-REQUEST", "field"),
    ("I6-IR-2", "V-INVALID-REQUEST", "reason"),
    ("I6-IR-3", "V-INVALID-REQUEST", "rules_version"),
]

I6_RULES_VERSION_CASES = [
    ("I6-RV-1", "V-SELECTED"),
    ("I6-RV-2", "V-FILTERED-EMPTY"),
    ("I6-RV-3", "V-LIMIT-ZERO"),
    ("I6-RV-4", "V-UPSTREAM-EMPTY"),
    ("I6-RV-5", "V-VENDOR"),
    ("I6-RV-6", "V-PARTIAL"),
    ("I6-RV-7", "V-INVARIANT"),
    ("I6-RV-8", "V-INVALID-REQUEST"),
]


@pytest.mark.unit
@pytest.mark.parametrize("case_id,variant,key", I6_CASES, ids=[c[0] for c in I6_CASES])
def test_i6_missing_required_key(case_id, variant, key):
    errors = _run(CONTROLS[variant], lambda event: event.pop(key))
    if key == "variant":
        # Without a variant the root check cannot classify; deterministic enum diagnostic.
        assert errors == ("enum:variant",)
    else:
        assert f"missing:{key}" in errors


@pytest.mark.unit
@pytest.mark.parametrize("case_id,variant", I6_RULES_VERSION_CASES,
                         ids=[c[0] for c in I6_RULES_VERSION_CASES])
def test_i6_rules_version_is_always_required(case_id, variant):
    errors = _run(CONTROLS[variant], lambda event: event.pop("rules_version"))
    assert "missing:rules_version" in errors


@pytest.mark.unit
@pytest.mark.parametrize("branch,candidates", [("A", 1), ("B", 0)])
@pytest.mark.parametrize("key", ["queries_failed", "executed_query_count",
                                 "pre_filter_candidate_count", "batch_id", "input_count",
                                 "reason_counts"])
def test_i6_partial_required_keys(branch, candidates, key):
    errors = _run(lambda: _partial(candidates=candidates), lambda event: event.pop(key))
    assert f"missing:{key}" in errors


@pytest.mark.unit
@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("key", sorted(COMMON_KEYS))
def test_i6_common_keys_required(variant, key):
    errors = _run(CONTROLS[variant], lambda event: event.pop(key))
    if key == "variant":
        # Without variant the root check cannot classify; deterministic enum diagnostic.
        assert errors == ("enum:variant",)
    else:
        assert f"missing:{key}" in errors


# --------------------------------------------------------------------------- I7 extra key


@pytest.mark.unit
@pytest.mark.parametrize(
    "case_id,variant,key",
    [
        ("I7-1", "V-SELECTED", "vendor"),
        ("I7-2", "V-INVALID-REQUEST", "input_count"),
        ("I7-3", "V-PARTIAL", "selected_count"),
        ("I7-4", "V-LIMIT-ZERO", "reason_counts"),
        ("I7-5", "V-UPSTREAM-EMPTY", "empty_kind"),
    ],
)
def test_i7_prohibited_key_rejected(case_id, variant, key):
    errors = _run(CONTROLS[variant], lambda event: event.__setitem__(key, 1))
    assert f"prohibited:{key}" in errors


# --------------------------------------------------------------------------- I8 triples


@pytest.mark.unit
@pytest.mark.parametrize("variant", VARIANTS)
def test_i8_legal_controls_accepted(variant):
    assert _static_o5_contract_errors(CONTROLS[variant]()) == ()


@pytest.mark.unit
@pytest.mark.parametrize("trigger", sorted(VENDOR_TRIGGERS))
def test_i8_vendor_triggers_accepted(trigger):
    assert _static_o5_contract_errors(_vendor(trigger=trigger)) == ()


@pytest.mark.unit
def test_i8_unknown_trigger_rejected():
    errors = _run(_vendor, lambda event: event.__setitem__("trigger", "VENDOR_OTHER"))
    assert "enum:trigger" in errors


@pytest.mark.unit
@pytest.mark.parametrize(
    "case_id,factory,overrides",
    [
        ("X2", _vendor, {"action": "SERVE_SELECTED"}),
        ("X3", _selected, {"disposition": "FILTERED_TO_EMPTY"}),
        ("X4", _partial, {"disposition": "OK"}),
        ("X5", _invalid_request, {"disposition": "INVARIANT_VIOLATION"}),
        ("X6", _limit_zero, {"disposition": "UPSTREAM_UNAVAILABLE"}),
    ],
)
def test_i8_illegal_combinations_rejected(case_id, factory, overrides):
    # The control is deliberately illegal, so the shared "valid control first"
    # precondition in _run does not apply; call the same entry directly.
    event = factory(**overrides)
    errors = _static_o5_contract_errors(copy.deepcopy(event))
    assert "combination:variant_action_trigger_disposition" in errors


# --------------------------------------------------------------------------- I10 partial branches


FIELD_STATES = [("bi", "batch_id"), ("ic", "input_count"), ("rc", "reason_counts")]


@pytest.mark.unit
@pytest.mark.parametrize("branch,candidates,tag", [("A", 1, "A"), ("B", 0, "B")])
@pytest.mark.parametrize("short,key", FIELD_STATES, ids=[s for s, _ in FIELD_STATES])
def test_i10_present_null_accepted(branch, candidates, tag, short, key):
    assert _static_o5_contract_errors(_partial(candidates=candidates)) == ()


@pytest.mark.unit
@pytest.mark.parametrize("branch,candidates,tag", [("A", 1, "A"), ("B", 0, "B")])
@pytest.mark.parametrize("short,key", FIELD_STATES, ids=[s for s, _ in FIELD_STATES])
def test_i10_missing_rejected(branch, candidates, tag, short, key):
    errors = _run(lambda: _partial(candidates=candidates), lambda event: event.pop(key))
    assert f"missing:{key}" in errors


@pytest.mark.unit
@pytest.mark.parametrize("branch,candidates,tag", [("A", 1, "A"), ("B", 0, "B")])
@pytest.mark.parametrize("short,key", FIELD_STATES, ids=[s for s, _ in FIELD_STATES])
def test_i10_present_non_null_rejected(branch, candidates, tag, short, key):
    errors = _run(lambda: _partial(candidates=candidates),
                  lambda event: event.__setitem__(key, "x" if key != "input_count" else 3))
    assert f"nullability:{key}" in errors


@pytest.mark.unit
@pytest.mark.parametrize(
    "case_id,executed,failed,candidates",
    [
        ("I10-A-11", 1, 1, 1),
        ("I10-A-33", 3, 3, 2),
        ("I10-B-11", 1, 1, 0),
        ("I10-B-33", 3, 3, 0),
    ],
)
def test_i10_valid_count_controls(case_id, executed, failed, candidates):
    assert _static_o5_contract_errors(_partial(executed=executed, failed=failed,
                                               candidates=candidates)) == ()


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation,expected",
    [
        ({"queries_failed": 0}, "range:queries_failed"),
        ({"queries_failed": 4, "executed_query_count": 3}, "relation:queries_failed"),
        ({"pre_filter_candidate_count": -1}, "range:pre_filter_candidate_count"),
        ({"executed_query_count": 3.0}, "type:executed_query_count"),
        ({"queries_failed": "1"}, "type:queries_failed"),
        ({"queries_failed": True}, "type:queries_failed"),
    ],
)
def test_i10_count_mutations_rejected(mutation, expected):
    errors = _run(lambda: _partial(executed=3, failed=1, candidates=1),
                  lambda event: event.update(mutation))
    assert expected in errors


@pytest.mark.unit
def test_branch_discriminator_comes_from_candidate_count():
    # Branch A control differs from B only by pre_filter_candidate_count.
    assert _static_o5_contract_errors(_partial(candidates=1)) == ()
    assert _static_o5_contract_errors(_partial(candidates=0)) == ()


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("foreign_id", "INV-O5-02"),
        ("duplicate_output", "INV-O5-02"),
        ("changed_time", "INV-O5-01"),
        ("changed_title", "INV-O5-01"),
        ("original_out_of_window", "INV-O5-03"),
    ],
)
def test_s4_runtime_invariant_checks(mutation, expected):
    request = news._build_o5_request("2026-09-28", 2, 2)
    original = news._map_news_dict_to_candidate({
        "title": "Fed holds rates", "summary": "Policy unchanged",
        "publisher": "FixtureWire", "link": "https://example.test/fed",
        "pub_date": datetime(2026, 9, 27, tzinfo=UTC),
    })
    result = news.select_macro_news([original], request)
    news._check_o5_invariants([original], request, result)
    selected = result.selected[0]
    if mutation == "foreign_id":
        changed = [replace(selected, candidate_id="o5:foreign")]
    elif mutation == "duplicate_output":
        changed = [selected, selected]
    elif mutation == "changed_time":
        changed = [replace(selected, published_at=datetime(2026, 9, 30, tzinfo=UTC))]
    elif mutation == "original_out_of_window":
        original = replace(original, published_at=datetime(2026, 9, 30, tzinfo=UTC))
        changed = [replace(selected, published_at=original.published_at)]
    else:
        changed = [replace(selected, title="Tampered title")]
    with pytest.raises(news.O5InvariantError) as error:
        news._check_o5_invariants([original], request, replace(result, selected=changed))
    assert error.value.invariant == expected
