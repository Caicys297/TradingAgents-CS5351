"""Offline tests for the standalone O2 provenance manifest writer."""

from __future__ import annotations

import json
import math

import pytest

from tradingagents.repro import manifest as manifest_module

pytestmark = pytest.mark.unit

IDENTITY = {
    "ticker": "NVDA",
    "asset_type": "stock",
    "analysis_date": "2026-11-14",
    "analysts": ["market", "news"],
}
CONFIG = {
    "llm_provider": "openai",
    "deep_think_llm": "deep-model",
    "quick_think_llm": "quick-model",
    "analysts": ["market", "news"],
    "output_language": "English",
    "data_vendors": {"core_stock_apis": "yfinance"},
}


def _manifest(**overrides):
    values = {**IDENTITY, "config": CONFIG}
    values.update(overrides)
    return manifest_module.build_manifest(**values)


def test_o2_tc_01_manifest_has_required_fields_and_is_writable(tmp_path):
    manifest = _manifest()
    assert manifest["schema_version"] == "1.0.0"
    assert set(manifest) == {
        "schema_version",
        "identity",
        "config",
        "runtime",
        "actual_input_data_provenance",
        "fingerprint",
        "artifacts",
    }

    path = manifest_module.write_manifest(tmp_path / "manifest.json", manifest)

    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == manifest


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
def test_o2_tc_02_nan_and_infinity_are_rejected(bad_value):
    with pytest.raises(ValueError):
        _manifest(config={**CONFIG, "input_near_dup_jaccard": bad_value})


def test_o2_tc_02_reordered_config_has_identical_fingerprint():
    first = _manifest(config={"output_language": "English", "llm_provider": "openai"})
    second = _manifest(config={"llm_provider": "openai", "output_language": "English"})
    assert first["fingerprint"] == second["fingerprint"]


def test_o2_tc_03_included_fields_change_fingerprint_but_excluded_fields_do_not():
    base = _manifest()
    changed = _manifest(config={**CONFIG, "deep_think_llm": "other-model"})
    assert base["fingerprint"]["value"] != changed["fingerprint"]["value"]

    artifact = manifest_module.make_artifact_reference(
        "message_log", "message_tool.log", "shared_mutable"
    )
    with_artifact = _manifest(artifacts=[artifact])
    with_runtime = _manifest(
        runtime=manifest_module.collect_runtime_metadata(
            package_version="9.9.9",
            python_version="3.99",
            platform_name="test-platform",
        )
    )
    assert with_artifact["fingerprint"] == base["fingerprint"]
    assert with_runtime["fingerprint"] == base["fingerprint"]


def test_o2_tc_05_artifact_stability_labels_and_relative_paths(tmp_path):
    absolute = tmp_path / "reports" / "complete_report.md"
    report = manifest_module.make_artifact_reference(
        "report", absolute, "shared_mutable", base=tmp_path
    )
    log = manifest_module.make_artifact_reference(
        "message_log", "message_tool.log", "shared_mutable"
    )
    manifest = manifest_module.make_artifact_reference(
        "manifest", "manifest.json", "run_unique"
    )
    snapshot = manifest_module.make_artifact_reference(
        "market_snapshot", None, "not_persisted"
    )

    assert report == {
        "name": "report",
        "path": "reports/complete_report.md",
        "stability": "shared_mutable",
    }
    assert log["stability"] == "shared_mutable"
    assert manifest["stability"] == "run_unique"
    assert snapshot["path"] is None and snapshot["stability"] == "not_persisted"

    with pytest.raises(ValueError):
        manifest_module.make_artifact_reference("bad", "x", "immutable")
    with pytest.raises(ValueError):
        manifest_module.make_artifact_reference(
            "escape", tmp_path / "outside.md", "shared_mutable", base=tmp_path / "base"
        )


def test_o2_tc_06_secret_fields_and_unapproved_keys_are_excluded():
    manifest = _manifest(
        config={
            **CONFIG,
            "api_key": "sk-should-not-appear",
            "token": "tok-should-not-appear",
            "password": "pw-should-not-appear",
            "backend_url": "https://user:secret@relay.example/v1",
            "input_condensation_audit_note": "unmerged-field",
            "unknown_field": "unapproved",
        }
    )
    serialized = json.dumps(manifest, ensure_ascii=False)

    assert "sk-should-not-appear" not in serialized
    assert "tok-should-not-appear" not in serialized
    assert "pw-should-not-appear" not in serialized
    assert "user:secret" not in serialized
    assert "input_condensation_audit_note" not in serialized
    assert "unknown_field" not in serialized
    assert manifest["config"]["deep_think_llm"] == "deep-model"


def test_o2_tc_07_data_provenance_is_not_captured_and_fingerprint_is_not_data():
    manifest = _manifest()
    assert manifest["actual_input_data_provenance"] == "not_captured"
    assert manifest["fingerprint"]["scope"] == (
        "normalized_identity_and_allowlisted_config_only"
    )
    assert "data" not in manifest["fingerprint"]["scope"].lower()


def test_o2_tc_08_git_unavailable_is_explicit():
    runtime = manifest_module.collect_runtime_metadata(git_metadata=None)
    manifest = _manifest(runtime=runtime)
    assert manifest["runtime"]["git"] == {
        "status": "unavailable",
        "commit": None,
        "dirty": None,
    }


def test_o2_tc_09_missing_model_and_provider_are_explicit():
    manifest = _manifest(config={"output_language": "English"})
    assert manifest["config"]["llm_provider"] is None
    assert manifest["config"]["deep_think_llm"] is None
    assert manifest["config"]["quick_think_llm"] is None


def test_o2_tc_10_empty_optional_fields_unicode_and_nan_rejection(tmp_path):
    first = _manifest(config={"output_language": "中文"})
    second = _manifest(config={"output_language": "中文"})
    assert first["fingerprint"] == second["fingerprint"]

    path = manifest_module.write_manifest(tmp_path / "manifest.json", first)
    assert json.loads(path.read_text(encoding="utf-8"))["config"]["output_language"] == "中文"

    with pytest.raises(ValueError):
        _manifest(config={"output_language": "中文", "input_budget_chars": math.nan})


def test_o2_tc_12_raw_ticker_variants_normalize_identically():
    short_hk = _manifest(ticker="700.HK")
    padded_hk = _manifest(ticker="0700.HK")
    assert short_hk["identity"]["ticker"] == "0700.HK"
    assert short_hk["identity"] == padded_hk["identity"]
    assert short_hk["fingerprint"] == padded_hk["fingerprint"]


def test_o2_tc_12_selected_analysts_use_canonical_order_for_identity_and_config():
    first = _manifest(
        analysts=["news", "market"],
        config={**CONFIG, "analysts": ["news", "market"]},
    )
    second = _manifest(
        analysts=["market", "news"],
        config={**CONFIG, "analysts": ["market", "news"]},
    )
    different = _manifest(
        analysts=["market"],
        config={**CONFIG, "analysts": ["market"]},
    )

    assert first["identity"]["analysts"] == ["market", "news"]
    assert first["config"]["analysts"] == ["market", "news"]
    assert first["identity"] == second["identity"]
    assert first["config"]["analysts"] == second["config"]["analysts"]
    assert first["fingerprint"] == second["fingerprint"]
    assert different["identity"]["analysts"] == ["market"]
    assert different["fingerprint"]["value"] != first["fingerprint"]["value"]


def test_o2_tc_16_nested_secret_and_credential_url_are_redacted():
    manifest = _manifest(
        config={
            **CONFIG,
            "data_vendors": {
                "core_stock_apis": "yfinance",
                "relay": "https://user:secret@example/v1",
                "api_key": "sk-nested-secret",
            },
        }
    )
    serialized = json.dumps(manifest, ensure_ascii=False)
    assert "user:secret" not in serialized
    assert "sk-nested-secret" not in serialized
    assert manifest["config"]["data_vendors"]["relay"] == "https://***@example/v1"
    assert manifest["config"]["data_vendors"]["api_key"] == "***"


def test_o2_tc_17_git_lookup_error_is_explicit():
    runtime = manifest_module.collect_runtime_metadata(
        git_metadata={"status": "error", "commit": None, "dirty": None}
    )
    manifest = _manifest(runtime=runtime)
    assert manifest["runtime"]["git"] == {
        "status": "error",
        "commit": None,
        "dirty": None,
    }


def test_o2_tc_19_manifest_writer_runs_offline(tmp_path):
    manifest = _manifest(
        runtime=manifest_module.collect_runtime_metadata(git_metadata=None)
    )
    path = manifest_module.write_manifest(tmp_path / "manifest.json", manifest)
    assert path.exists()


def test_o2_tc_22_identity_contains_only_approved_fields():
    manifest = _manifest(ticker="700.HK")
    assert set(manifest["identity"]) == {
        "ticker",
        "asset_type",
        "analysis_date",
        "analysts",
    }
    assert "raw_ticker" not in manifest["identity"]
    assert manifest["identity"]["ticker"] == "0700.HK"


def test_o2_tc_23_only_merged_allowlist_is_serialized():
    manifest = _manifest(
        config={
            **CONFIG,
            "input_condensation_audit_note": "unmerged",
            "api_key": "secret",
            "unknown": "unapproved",
        }
    )
    assert set(manifest["config"]) == set(manifest_module.CONFIG_ALLOWLIST)
    assert "input_condensation_audit_note" not in manifest["config"]
    assert "api_key" not in manifest["config"]
    assert "unknown" not in manifest["config"]


def test_o2_tc_24_runtime_metadata_is_recorded_or_explicitly_missing():
    runtime = manifest_module.collect_runtime_metadata(
        package_version="9.9.9",
        python_version="3.11.9",
        platform_name="Linux-test",
        git_metadata={"status": "available", "commit": "abc123", "dirty": False},
    )
    manifest = _manifest(runtime=runtime)
    assert manifest["runtime"]["package_version"] == "9.9.9"
    assert manifest["runtime"]["python_version"] == "3.11.9"
    assert manifest["runtime"]["platform"] == "Linux-test"
    assert manifest["runtime"]["git"]["commit"] == "abc123"

    missing = manifest_module.collect_runtime_metadata(
        package_version=None,
        python_version=None,
        platform_name=None,
        git_metadata=None,
    )
    missing_manifest = _manifest(runtime=missing)
    assert missing_manifest["runtime"]["package_version"] is None
    assert missing_manifest["runtime"]["python_version"] is None
    assert missing_manifest["runtime"]["platform"] is None


def test_o2_tc_25_schema_version_is_1_0_0():
    assert _manifest()["schema_version"] == "1.0.0"


def test_o2_tc_13_serialization_failure_leaves_no_partial_manifest(tmp_path):
    manifest = _manifest()
    manifest["config"]["data_vendors"] = {"bad": object()}
    target = tmp_path / "manifest.json"

    with pytest.raises((TypeError, ValueError)):
        manifest_module.write_manifest(target, manifest)

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


def test_o2_tc_14_promotion_failure_leaves_no_partial_manifest(tmp_path, monkeypatch):
    manifest = _manifest()
    target = tmp_path / "manifest.json"

    def fail_replace(source, destination):
        raise OSError("promotion failed")

    monkeypatch.setattr(manifest_module.os, "replace", fail_replace)

    with pytest.raises(OSError):
        manifest_module.write_manifest(target, manifest)

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
