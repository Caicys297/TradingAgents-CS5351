"""Offline tests for the corrected CI gate checkers (scripts/*.py).

Deterministic: no real mypy/pip-audit network scan. They prove the checkers fail
closed and enforce the corrected policies (trusted-base baselines, per-diagnostic
multiplicity, structural dependency-report validation, genuine new AI-use entry).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _run(script: str, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    import os

    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / f"{script}.py"), *args],
        capture_output=True, text=True, cwd=ROOT, env=e,
    )


# ============================================================ Schema gate
SCHEMA = ROOT / "docs/req/req-schema.json"
REGISTRY = ROOT / "docs/req/requirements.yaml"


@pytest.mark.unit
def test_schema_valid_registry_passes():
    assert _run("validate_requirements", "--registry", str(REGISTRY), "--schema", str(SCHEMA)).returncode == 0


@pytest.mark.unit
@pytest.mark.parametrize("content,needle", [
    ("registry_version: x\n  broken: [\n", "malformed YAML"),
    ('registry_version: "a"\nregistry_version: "b"\n', "duplicate key"),
])
def test_schema_bad_yaml_fails(tmp_path, content, needle):
    bad = tmp_path / "bad.yaml"
    bad.write_text(content)
    r = _run("validate_requirements", "--registry", str(bad), "--schema", str(SCHEMA))
    assert r.returncode == 1 and needle.lower() in r.stderr.lower()


@pytest.mark.unit
def test_schema_missing_file_fails(tmp_path):
    r = _run("validate_requirements", "--registry", str(tmp_path / "nope.yaml"), "--schema", str(SCHEMA))
    assert r.returncode == 1 and "not found" in r.stderr


@pytest.mark.unit
def test_schema_violation_and_dup_ids_fail(tmp_path):
    import copy

    import yaml

    reg = yaml.safe_load(REGISTRY.read_text())
    reg["requirements"][0]["priority"] = "Critical"
    bad = tmp_path / "v.yaml"
    bad.write_text(yaml.safe_dump(reg, sort_keys=False, allow_unicode=True))
    assert _run("validate_requirements", "--registry", str(bad), "--schema", str(SCHEMA)).returncode == 1

    reg2 = copy.deepcopy(yaml.safe_load(REGISTRY.read_text()))
    reg2["requirements"].append(copy.deepcopy(reg2["requirements"][0]))
    bad2 = tmp_path / "d.yaml"
    bad2.write_text(yaml.safe_dump(reg2, sort_keys=False, allow_unicode=True))
    r2 = _run("validate_requirements", "--registry", str(bad2), "--schema", str(SCHEMA))
    assert r2.returncode == 1 and "duplicate requirement id" in r2.stderr


# ============================================================ Type checker
def _mk_baseline(tmp: Path, identities: list[str]) -> Path:
    b = tmp / "mypy-baseline.txt"
    b.write_text("# baseline\n" + "\n".join(identities) + "\n")
    return b


@pytest.mark.unit
def test_typecheck_identity_distinct_for_same_code_different_message():
    mod = _load("typecheck")
    lines = [
        "cli/run.py:10: error: Cannot assign to method A  [method-assign]",
        "cli/run.py:20: error: Cannot assign to method B  [method-assign]",
    ]
    ids = mod.identities(lines) if hasattr(mod, "identities") else list(mod.parse(lines))
    assert len(ids) == 2 and len(set(ids)) == 2


@pytest.mark.unit
def test_typecheck_multiplicity_two_identical_need_two_in_baseline(monkeypatch, tmp_path):
    """Two identical diagnostics require a baseline count of 2; one is not enough."""
    mod = _load("typecheck")
    line = "cli/run.py:188: error: Cannot assign to a method  [method-assign]"
    ident = list(mod.parse([line]))[0]
    # baseline has only ONE occurrence; mypy yields TWO -> one new (blocking)
    b = _mk_baseline(tmp_path, [ident])
    monkeypatch.setattr(mod, "BASELINE", b)
    monkeypatch.setattr(mod, "_load_baseline_text", lambda ref: None)  # force working-tree path
    monkeypatch.setattr(mod, "run_mypy", lambda: [line, line])
    # no PR env => uses working-tree baseline
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    assert mod.main([]) == 1


@pytest.mark.unit
def test_typecheck_removal_does_not_offset_new(monkeypatch, tmp_path):
    mod = _load("typecheck")
    old = list(mod.parse(["old.py:1: error: Old issue  [arg-type]"]))[0]
    b = _mk_baseline(tmp_path, [old])
    monkeypatch.setattr(mod, "BASELINE", b)
    monkeypatch.setattr(mod, "_load_baseline_text", lambda ref: None)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setattr(mod, "run_mypy", lambda: ["new.py:1: error: New issue  [return-value]"])
    assert mod.main([]) == 1


@pytest.mark.unit
def test_typecheck_trusted_base_ignores_pr_widening(monkeypatch, tmp_path):
    """A PR that widens its own baseline cannot authorize a new diagnostic."""
    mod = _load("typecheck")
    newline = "x.py:1: error: Brand new  [return-value]"
    ident = list(mod.parse([newline]))[0]
    # PR working-tree baseline WIDENED to include the new identity:
    b = _mk_baseline(tmp_path, [ident])
    monkeypatch.setattr(mod, "BASELINE", b)
    # ...but the trusted base revision has an EMPTY baseline:
    monkeypatch.setattr(mod, "_load_baseline_text", lambda ref: "# empty\n")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    monkeypatch.setattr(mod, "run_mypy", lambda: [newline])
    assert mod.main([]) == 1  # trusted base wins; new diagnostic blocks


@pytest.mark.unit
def test_typecheck_mypy_exit1_without_diagnostics_is_execution_failure(monkeypatch):
    mod = _load("typecheck")

    class _P:
        returncode = 1
        stdout = "mypy: internal error, no parseable diagnostics"
        stderr = ""

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _P())
    with pytest.raises(SystemExit) as exc:
        mod.run_mypy()
    assert exc.value.code == 2  # never treated as success


# ============================================================ Dep audit
@pytest.mark.unit
def test_dep_audit_empty_json_report_is_scanner_failure(monkeypatch):
    mod = _load("dep_audit")

    class _P:
        returncode = 0
        stdout = "{}"
        stderr = ""

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _P())
    with pytest.raises(mod.ScannerError):
        mod.run_pip_audit()


@pytest.mark.unit
def test_dep_audit_scanner_exit2_is_failure(monkeypatch):
    mod = _load("dep_audit")

    class _P:
        returncode = 2
        stdout = ""
        stderr = "network error"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _P())
    with pytest.raises(mod.ScannerError):
        mod.run_pip_audit()


@pytest.mark.unit
def test_dep_audit_new_finding_blocks_main(monkeypatch, tmp_path):
    mod = _load("dep_audit")
    report = {"dependencies": [{"name": "foo", "version": "1.0",
                                "vulns": [{"id": "GHSA-x", "fix_versions": ["1.2"]}]}]}
    monkeypatch.setattr(mod, "run_pip_audit", lambda: report)
    base = tmp_path / "b.json"
    base.write_text(json.dumps({"findings": []}))
    monkeypatch.setattr(mod, "BASELINE", base)
    monkeypatch.setattr(mod, "_load_baseline", lambda: ({"findings": []}, "test"))
    assert mod.main([]) == 1


@pytest.mark.unit
def test_dep_audit_allowance_is_version_specific(monkeypatch):
    """A baseline allowance for v1.0 must not cover a future affected version 2.0."""
    mod = _load("dep_audit")
    base = {"findings": [{"package": "foo", "id": "GHSA-x", "affected_version": "1.0"}]}
    keys = mod.baseline_keys(base)
    found = [("foo", "2.0", "GHSA-x", "no fix")]  # same id, different version
    new = [(p, v, vid, f) for (p, v, vid, f) in found if (p, vid, v) not in keys]
    assert new  # blocks: version differs


@pytest.mark.unit
def test_dep_audit_pending_baseline_metadata_rejected():
    mod = _load("dep_audit")
    base = {"findings": [{"package": "foo", "id": "GHSA-x", "affected_version": "1.0",
                          "owner": "PENDING", "status": "PENDING"}]}
    assert mod.validate_baseline(base)  # non-empty => invalid


# ============================================================ AI-use gate
@pytest.mark.unit
def test_ai_use_no_log_change_fails(tmp_path):
    mod = _load("check_ai_use_log")
    (tmp_path / "tradingagents").mkdir()
    errs = mod.check(["tradingagents/x.py"], tmp_path, base_ref="")
    assert errs and "no AI-use log change" in errs[0]


@pytest.mark.unit
def test_ai_use_not_applicable_for_docs_only(tmp_path):
    mod = _load("check_ai_use_log")
    assert mod.check(["docs/readme.md"], tmp_path, base_ref="") == []


@pytest.mark.unit
def test_ai_use_bare_pr_url_is_not_session(tmp_path):
    mod = _load("check_ai_use_log")
    (tmp_path / "transcripts").mkdir()
    log = tmp_path / "transcripts/O5-AI-Use-Log.md"
    log.write_text("Task: t. Scope: s. Commit: abc1234.\n"
                   "See https://github.com/Caicys297/TradingAgents-CS5351/pull/29\n")
    errs = mod.check(["scripts/x.py", "transcripts/O5-AI-Use-Log.md"], tmp_path, base_ref="")
    assert any("PR URL is not session evidence" in e for e in errs)


@pytest.mark.unit
def test_ai_use_absolute_path_rejected(tmp_path):
    mod = _load("check_ai_use_log")
    (tmp_path / "transcripts").mkdir()
    log = tmp_path / "transcripts/O5-AI-Use-Log.md"
    log.write_text("Task: t. Scope: s. Commit: abc1234.\n"
                   "Session: https://x/session/1\nLocal: /Users/me/secret\n")
    errs = mod.check(["scripts/x.py", "transcripts/O5-AI-Use-Log.md"], tmp_path, base_ref="")
    assert any("absolute path" in e for e in errs)


@pytest.mark.unit
def test_ai_use_whitespace_only_edit_fails(tmp_path):
    mod = _load("check_ai_use_log")
    (tmp_path / "transcripts").mkdir()
    log = tmp_path / "transcripts/O5-AI-Use-Log.md"
    log.write_text("   \n\n  \n")
    errs = mod.check(["scripts/x.py", "transcripts/O5-AI-Use-Log.md"], tmp_path, base_ref="")
    assert any("whitespace-only" in e.lower() for e in errs)


@pytest.mark.unit
def test_ai_use_missing_commit_association_fails(tmp_path):
    mod = _load("check_ai_use_log")
    (tmp_path / "transcripts").mkdir()
    log = tmp_path / "transcripts/O5-AI-Use-Log.md"
    log.write_text("Task: t. Scope: s.\nSession: https://x/session/1\n")
    errs = mod.check(["scripts/x.py", "transcripts/O5-AI-Use-Log.md"], tmp_path, base_ref="")
    assert any("commit" in e for e in errs)


@pytest.mark.unit
def test_ai_use_genuine_resolvable_export_passes(tmp_path):
    mod = _load("check_ai_use_log")
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts/O5-session-export.md").write_text("raw\nexport\n")
    log = tmp_path / "transcripts/O5-AI-Use-Log.md"
    log.write_text("Task: t. Usage scope: s. Implementation commit: abc1234.\n"
                   "Evidence: transcripts/O5-session-export.md\n")
    errs = mod.check(["scripts/x.py", "transcripts/O5-AI-Use-Log.md"], tmp_path, base_ref="")
    assert errs == []


@pytest.mark.unit
def test_ai_use_changed_from_file_handles_spaces(tmp_path):
    """--changed-from-file is NUL-separated so spaces in filenames are safe."""
    z = tmp_path / "changed.z"
    z.write_bytes(b"docs/a file.md\x00tradingagents/x.py\x00")
    mod = _load("check_ai_use_log")
    files = mod._changed_from_file(z)
    assert files == ["docs/a file.md", "tradingagents/x.py"]
