"""Standalone provenance manifest construction and atomic writing for O2."""

from __future__ import annotations

import hashlib
import json
import os
import platform as platform_module
import re
import uuid
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

import tradingagents
from tradingagents.dataflows.symbols import normalize_symbol, safe_ticker_component

SCHEMA_VERSION = "1.0.0"
ACTUAL_INPUT_DATA_PROVENANCE = "not_captured"
FINGERPRINT_SCOPE = "normalized_identity_and_allowlisted_config_only"
ARTIFACT_STABILITIES = frozenset({"run_unique", "shared_mutable", "not_persisted"})
GIT_STATUSES = frozenset({"available", "unavailable", "error"})

CANONICAL_ANALYST_ORDER = ("market", "social", "news", "fundamentals")
_CANONICAL_ANALYST_INDEX = {
    name: index for index, name in enumerate(CANONICAL_ANALYST_ORDER)
}

CONFIG_ALLOWLIST = (
    "llm_provider",
    "deep_think_provider",
    "deep_think_llm",
    "quick_think_provider",
    "quick_think_llm",
    "analysts",
    "max_debate_rounds",
    "max_risk_discuss_rounds",
    "max_tool_rounds",
    "output_language",
    "data_vendors",
    "tool_vendors",
    "news_article_limit",
    "global_news_article_limit",
    "global_news_lookback_days",
    "input_condensation_enabled",
    "input_budget_chars",
    "input_news_cap_chars",
    "input_stocktwits_cap_chars",
    "input_reddit_cap_chars",
    "input_near_dup_jaccard",
    "input_condensation_audit_note",
    "o5_rules_version",
    "o5_requested_topics",
    "o5_limit",
    "o4_gate_policy_version",
)

_IDENTITY_KEYS = frozenset({"ticker", "asset_type", "analysis_date", "analysts"})
_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "identity",
        "config",
        "runtime",
        "actual_input_data_provenance",
        "fingerprint",
        "artifacts",
    }
)
_RUNTIME_KEYS = frozenset({"package_version", "python_version", "platform", "git"})
_GIT_KEYS = frozenset({"status", "commit", "dirty"})
_FINGERPRINT_KEYS = frozenset({"algorithm", "scope", "value"})
_ARTIFACT_KEYS = frozenset({"name", "path", "stability"})
_SECRET_NAME_PATTERN = (
    r"(?:api[_-]?key|access[_-]?token|token|secret|password|passwd|authorization|credential)"
)
_SECRET_KEY_RE = re.compile(rf"({_SECRET_NAME_PATTERN})", re.IGNORECASE)
_SECRET_QUERY_RE = re.compile(
    rf"([?&]{_SECRET_NAME_PATTERN}=)([^&#]*)",
    re.IGNORECASE,
)
_CREDENTIAL_URL_RE = re.compile(r"(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*://)[^/@\s]+@")
_UNSET = object()


class ManifestError(ValueError):
    """Raised when manifest data cannot be represented safely."""


def canonical_json(value: Any) -> str:
    """Serialize a value with O2 canonical JSON rules."""
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"value is not canonical JSON: {exc}") from exc


def _sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned = {}
        for key, item in value.items():
            text_key = str(key)
            if _SECRET_KEY_RE.search(text_key):
                cleaned[text_key] = "***"
            else:
                cleaned[text_key] = _sanitize(item)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    if isinstance(value, str):
        redacted = _CREDENTIAL_URL_RE.sub(r"\g<scheme>***@", value)
        return _SECRET_QUERY_RE.sub(r"\1***", redacted)
    return value


def canonicalize_analysts(analysts: Sequence[str]) -> list[str]:
    """Return selected analysts in the repository's canonical Analyst order."""
    if isinstance(analysts, str) or not isinstance(analysts, Sequence):
        raise ManifestError("analysts must be a sequence of non-empty strings")
    selected = set()
    for analyst in analysts:
        if not isinstance(analyst, str) or not analyst.strip():
            raise ManifestError("analysts must contain only non-empty strings")
        key = analyst.strip().lower()
        if key not in _CANONICAL_ANALYST_INDEX:
            raise ManifestError(f"unknown analyst: {analyst!r}")
        if key in selected:
            raise ManifestError(f"duplicate analyst: {analyst!r}")
        selected.add(key)
    if not selected:
        raise ManifestError("analysts must not be empty")
    return [name for name in CANONICAL_ANALYST_ORDER if name in selected]


def normalize_identity(
    *,
    ticker: str,
    asset_type: str,
    analysis_date: str,
    analysts: Sequence[str],
) -> dict[str, Any]:
    """Return the approved normalized identity fields."""
    if not isinstance(ticker, str) or not ticker.strip():
        raise ManifestError("ticker must be a non-empty string")
    if not isinstance(asset_type, str) or not asset_type.strip():
        raise ManifestError("asset_type must be a non-empty string")
    try:
        parsed_date = date.fromisoformat(str(analysis_date))
    except (TypeError, ValueError) as exc:
        raise ManifestError("analysis_date must be an ISO date") from exc
    cleaned_analysts = canonicalize_analysts(analysts)
    normalized_ticker = safe_ticker_component(normalize_symbol(ticker))
    return {
        "ticker": normalized_ticker,
        "asset_type": asset_type.strip().lower(),
        "analysis_date": parsed_date.isoformat(),
        "analysts": cleaned_analysts,
    }


def select_allowed_config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return only the merged allowlist, with explicit nulls for absent fields."""
    source = config or {}
    if not isinstance(source, Mapping):
        raise ManifestError("config must be a mapping")
    allowed = {key: _sanitize(source.get(key)) for key in CONFIG_ALLOWLIST}
    if allowed["analysts"] is not None:
        allowed["analysts"] = canonicalize_analysts(allowed["analysts"])
    return allowed


def _normalize_git(git_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if git_metadata is None:
        return {"status": "unavailable", "commit": None, "dirty": None}
    if not isinstance(git_metadata, Mapping):
        raise ManifestError("git_metadata must be a mapping or None")
    status = git_metadata.get("status")
    commit = git_metadata.get("commit")
    dirty = git_metadata.get("dirty")
    if status is None:
        status = "available" if commit is not None else "unavailable"
    if status not in GIT_STATUSES:
        raise ManifestError("git status must be available, unavailable, or error")
    if commit is not None and not isinstance(commit, str):
        raise ManifestError("git commit must be a string or None")
    if dirty is not None and not isinstance(dirty, bool):
        raise ManifestError("git dirty must be a boolean or None")
    return {"status": status, "commit": commit, "dirty": dirty}


def collect_runtime_metadata(
    *,
    package_version: Any = _UNSET,
    python_version: Any = _UNSET,
    platform_name: Any = _UNSET,
    git_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect available runtime identity; explicit None stays missing."""
    return {
        "package_version": (
            getattr(tradingagents, "__version__", None)
            if package_version is _UNSET
            else package_version
        ),
        "python_version": (
            platform_module.python_version()
            if python_version is _UNSET
            else python_version
        ),
        "platform": (
            platform_module.platform() if platform_name is _UNSET else platform_name
        ),
        "git": _normalize_git(git_metadata),
    }


def _relative_posix_path(path: str | Path, base: str | Path | None) -> str:
    candidate = Path(path)
    if base is not None:
        base_path = Path(base).resolve()
        resolved = (candidate if candidate.is_absolute() else base_path / candidate).resolve()
        try:
            relative = resolved.relative_to(base_path)
        except ValueError as exc:
            raise ManifestError("artifact path escapes the provided base") from exc
        return relative.as_posix()
    if candidate.is_absolute() or candidate.drive or candidate.root:
        raise ManifestError("artifact path must be relative when no base is provided")
    if any(part == ".." for part in candidate.parts):
        raise ManifestError("artifact path must not contain '..'")
    return candidate.as_posix()


def make_artifact_reference(
    name: str,
    path: str | Path | None,
    stability: str,
    *,
    base: str | Path | None = None,
) -> dict[str, Any]:
    """Build one validated artifact reference."""
    if not isinstance(name, str) or not name.strip():
        raise ManifestError("artifact name must be a non-empty string")
    if stability not in ARTIFACT_STABILITIES:
        raise ManifestError("artifact stability must be run_unique, shared_mutable, or not_persisted")
    if stability == "not_persisted":
        if path not in (None, ""):
            raise ManifestError("not_persisted artifacts must not have a path")
        relative_path = None
    else:
        if path is None or not str(path).strip():
            raise ManifestError("persisted artifacts must have a path")
        relative_path = _relative_posix_path(path, base)
    return {"name": name.strip(), "path": relative_path, "stability": stability}


def fingerprint_inputs(identity: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    """Hash normalized identity plus allowlisted config, not market/news data."""
    payload = {"identity": dict(identity), "config": dict(config)}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the standalone manifest before writing it."""
    if not isinstance(manifest, Mapping):
        raise ManifestError("manifest must be a mapping")
    if set(manifest) != _MANIFEST_KEYS:
        raise ManifestError("manifest has missing or unknown fields")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestError(f"schema_version must be {SCHEMA_VERSION}")

    identity = manifest["identity"]
    if not isinstance(identity, Mapping) or set(identity) != _IDENTITY_KEYS:
        raise ManifestError("identity has missing or unknown fields")
    if not isinstance(identity["analysts"], list) or not identity["analysts"]:
        raise ManifestError("identity.analysts must be a non-empty list")
    try:
        canonical_identity_analysts = canonicalize_analysts(identity["analysts"])
    except ManifestError as exc:
        raise ManifestError("identity.analysts are invalid") from exc
    if identity["analysts"] != canonical_identity_analysts:
        raise ManifestError("identity.analysts are not in canonical order")

    config = manifest["config"]
    if not isinstance(config, Mapping) or set(config) != set(CONFIG_ALLOWLIST):
        raise ManifestError("config must contain exactly the merged allowlist")
    if config["analysts"] is not None:
        try:
            canonical_config_analysts = canonicalize_analysts(config["analysts"])
        except ManifestError as exc:
            raise ManifestError("config.analysts are invalid") from exc
        if config["analysts"] != canonical_config_analysts:
            raise ManifestError("config.analysts are not in canonical order")

    runtime = manifest["runtime"]
    if not isinstance(runtime, Mapping) or set(runtime) != _RUNTIME_KEYS:
        raise ManifestError("runtime has missing or unknown fields")
    git = runtime["git"]
    if not isinstance(git, Mapping) or set(git) != _GIT_KEYS:
        raise ManifestError("runtime.git has missing or unknown fields")
    if git["status"] not in GIT_STATUSES:
        raise ManifestError("runtime.git.status is invalid")

    if manifest["actual_input_data_provenance"] != ACTUAL_INPUT_DATA_PROVENANCE:
        raise ManifestError("actual_input_data_provenance must be not_captured")

    fingerprint = manifest["fingerprint"]
    if not isinstance(fingerprint, Mapping) or set(fingerprint) != _FINGERPRINT_KEYS:
        raise ManifestError("fingerprint has missing or unknown fields")
    if fingerprint["algorithm"] != "sha256":
        raise ManifestError("fingerprint algorithm must be sha256")
    if fingerprint["scope"] != FINGERPRINT_SCOPE:
        raise ManifestError("fingerprint scope is invalid")
    if not isinstance(fingerprint["value"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", fingerprint["value"]
    ):
        raise ManifestError("fingerprint value must be a 64-character lowercase hex digest")

    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list):
        raise ManifestError("artifacts must be a list")
    for artifact in artifacts:
        if not isinstance(artifact, Mapping) or set(artifact) != _ARTIFACT_KEYS:
            raise ManifestError("artifact has missing or unknown fields")
        if artifact["stability"] not in ARTIFACT_STABILITIES:
            raise ManifestError("artifact stability is invalid")
        if artifact["stability"] == "not_persisted":
            if artifact["path"] is not None:
                raise ManifestError("not_persisted artifact must not have a path")
        elif not isinstance(artifact["path"], str) or not artifact["path"]:
            raise ManifestError("persisted artifact must have a path")
        elif Path(artifact["path"]).is_absolute() or any(
            part == ".." for part in Path(artifact["path"]).parts
        ):
            raise ManifestError("artifact path must be relative and must not contain '..'")


def build_manifest(
    *,
    ticker: str,
    asset_type: str,
    analysis_date: str,
    analysts: Sequence[str],
    config: Mapping[str, Any] | None,
    runtime: Mapping[str, Any] | None = None,
    artifacts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build and validate one standalone O2 manifest."""
    identity = normalize_identity(
        ticker=ticker,
        asset_type=asset_type,
        analysis_date=analysis_date,
        analysts=analysts,
    )
    allowed_config = select_allowed_config(config)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "identity": identity,
        "config": allowed_config,
        "runtime": dict(runtime) if runtime is not None else collect_runtime_metadata(),
        "actual_input_data_provenance": ACTUAL_INPUT_DATA_PROVENANCE,
        "fingerprint": {
            "algorithm": "sha256",
            "scope": FINGERPRINT_SCOPE,
            "value": fingerprint_inputs(identity, allowed_config),
        },
        "artifacts": [dict(artifact) for artifact in artifacts],
    }
    validate_manifest(manifest)
    return manifest


def write_manifest(path: str | Path, manifest: Mapping[str, Any]) -> Path:
    """Write one manifest atomically, leaving no partial target on failure."""
    target = Path(path)
    validate_manifest(manifest)
    payload = json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
    ) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return target
