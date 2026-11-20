"""Offline tests for the CI gate checkers (scripts/*.py).

These tests exercise the checker *logic* deterministically: they do not run a
real mypy or pip-audit scan against the network. They prove that the checkers
(and their CI wiring contract) fail closed. Actual scans are separate jobs whose
results are reported by CI.
"""

from __future__ import annotations

import importlib.util
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


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / f"{script}.py"), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


# ---------------------------------------------------------------- Schema gate
SCHEMA = ROOT / "docs/req/req-schema.json"
REGISTRY = ROOT / "docs/req/requirements.yaml"


@pytest.mark.unit
def test_schema_valid_registry_passes():
    assert _run("validate_requirements", "--registry", str(REGISTRY), "--schema", str(SCHEMA)).returncode == 0


@pytest.mark.unit
def test_schema_missing_file_fails(tmp_path):
    r = _run("validate_requirements", "--registry", str(tmp_path / "nope.yaml"), "--schema", str(SCHEMA))
    assert r.returncode == 1
    assert "not found" in r.stderr


@pytest.mark.unit
def test_schema_malformed_yaml_fails(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("registry_version: x\n  broken: [\n")
    r = _run("validate_requirements", "--registry", str(bad), "--schema", str(SCHEMA))
    assert r.returncode == 1
    assert "malformed YAML" in r.stderr


@pytest.mark.unit
def test_schema_duplicate_key_fails(tmp_path):
    dup = tmp_path / "dup.yaml"
    dup.write_text('registry_version: "a"\nregistry_version: "b"\n')
    r = _run("validate_requirements", "--registry", str(dup), "--schema", str(SCHEMA))
    assert r.returncode == 1
    assert "duplicate key" in r.stderr.lower()


@pytest.mark.unit
def test_schema_violation_fails(tmp_path):
    import yaml

    reg = yaml.safe_load(REGISTRY.read_text())
    reg["requirements"][0]["priority"] = "Critical"  # not in MoSCoW enum
    bad = tmp_path / "viol.yaml"
    bad.write_text(yaml.safe_dump(reg, sort_keys=False, allow_unicode=True))
    r = _run("validate_requirements", "--registry", str(bad), "--schema", str(SCHEMA))
    assert r.returncode == 1
    assert "requirements/0" in r.stderr


@pytest.mark.unit
def test_schema_duplicate_ids_fail(tmp_path):
    import copy

    import yaml

    reg = yaml.safe_load(REGISTRY.read_text())
    reg["requirements"].append(copy.deepcopy(reg["requirements"][0]))  # duplicate first id
    bad = tmp_path / "dupid.yaml"
    bad.write_text(yaml.safe_dump(reg, sort_keys=False, allow_unicode=True))
    r = _run("validate_requirements", "--registry", str(bad), "--schema", str(SCHEMA))
    assert r.returncode == 1
    assert "duplicate requirement id" in r.stderr


# ---------------------------------------------------------------- AI-use gate
@pytest.mark.unit
def test_ai_use_no_log_change_fails():
    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as d:
        root = P(d)
        (root / "docs").mkdir()
        (root / "docs/x.py").write_text("x=1\n")
        mod = _load("check_ai_use_log")
        errs = mod.check(["docs/x.py"], root)
    assert errs and "no AI-use log change" in errs[0]


@pytest.mark.unit
def test_ai_use_bare_pr_url_insufficient():
    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as d:
        root = P(d)
        (root / "transcripts").mkdir()
        log = root / "transcripts/O5-AI-Use-Log.md"
        log.write_text(
            "# log\nTask: O5. Scope: selector. Commit: abc123.\n"
            "See https://github.com/Caicys297/TradingAgents-CS5351/pull/29\n"
        )
        mod = _load("check_ai_use_log")
        errs = mod.check(["transcripts/O5-AI-Use-Log.md"], root)
    assert errs and "no real session" in errs[0]


@pytest.mark.unit
def test_ai_use_absolute_path_rejected():
    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as d:
        root = P(d)
        (root / "transcripts").mkdir()
        log = root / "transcripts/O5-AI-Use-Log.md"
        log.write_text("Task: t. Scope: s. Commit: abc.\nSession: https://x/s/1\nLocal: /Users/me/secret\n")
        mod = _load("check_ai_use_log")
        errs = mod.check(["transcripts/O5-AI-Use-Log.md"], root)
    assert any("absolute path" in e for e in errs)


@pytest.mark.unit
def test_ai_use_valid_session_url_passes():
    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as d:
        root = P(d)
        (root / "transcripts").mkdir()
        log = root / "transcripts/O5-AI-Use-Log.md"
        log.write_text(
            "Task: O5. Usage scope: selector. Implementation commit: abc123.\n"
            "Session export: https://opencode.example/session/xyz\n"
        )
        mod = _load("check_ai_use_log")
        errs = mod.check(["transcripts/O5-AI-Use-Log.md"], root)
    assert errs == []


@pytest.mark.unit
def test_ai_use_missing_marker_fails():
    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as d:
        root = P(d)
        (root / "transcripts").mkdir()
        log = root / "transcripts/O5-AI-Use-Log.md"
        log.write_text("Session: https://x/s/1\n")  # no task/scope/commit
        mod = _load("check_ai_use_log")
        errs = mod.check(["transcripts/O5-AI-Use-Log.md"], root)
    assert any("association marker" in e for e in errs)


# ---------------------------------------------------------------- Type checker
@pytest.mark.unit
def test_typecheck_identity_is_per_diagnostic():
    mod = _load("typecheck")
    lines = [
        "cli/run.py:188: error: Cannot assign to a method  [method-assign]",
        "cli/run.py:200: error: Other thing  [method-assign]",
    ]
    ids = mod.identities(lines)
    assert len(ids) == 2 and ids[0] != ids[1]  # same file+code, distinct diagnostics


@pytest.mark.unit
def test_typecheck_blocks_new_diagnostic_via_baseline_diff(monkeypatch, tmp_path):
    """A new identity absent from the baseline is reported as blocking."""
    mod = _load("typecheck")
    baseline = tmp_path / "mypy-baseline.txt"
    monkeypatch.setattr(mod, "BASELINE", baseline)
    # Simulate mypy emitting one baseline diagnostic + one brand-new diagnostic.
    monkeypatch.setattr(
        mod,
        "run_mypy",
        lambda: [
            "cli/run.py:188: error: Cannot assign to a method  [method-assign]",
            "tradingagents/agents/new.py:9: error: Incompatible types  [assignment]",
        ],
    )
    # Force the baseline identity to match the first emitted line.
    first_id = mod.identities(
        ["cli/run.py:188: error: Cannot assign to a method  [method-assign]"]
    )[0]
    baseline.write_text(f"# baseline\n{first_id}\n")
    rc = mod.main([])
    assert rc == 1  # the second (new) diagnostic blocks


@pytest.mark.unit
def test_typecheck_removal_does_not_mask_new(monkeypatch, tmp_path):
    """Deleting baseline errors must not allow a different new error through."""
    mod = _load("typecheck")
    baseline = tmp_path / "mypy-baseline.txt"
    baseline.write_text("# baseline\nold.py:arg-type:deadbeef\n")
    monkeypatch.setattr(mod, "BASELINE", baseline)
    monkeypatch.setattr(
        mod,
        "run_mypy",
        lambda: ["new.py:5: error: Incompatible return value type  [return-value]"],
    )
    assert mod.main([]) == 1


# ---------------------------------------------------------------- Dep audit
@pytest.mark.unit
def test_dep_audit_new_vuln_blocks():
    mod = _load("dep_audit")
    report = {"dependencies": [{"name": "foo", "version": "1.0",
                                "vulns": [{"id": "GHSA-xxxx", "fix_versions": ["1.2"]}]}]}
    found = mod.findings(report)
    new = [(p, v, vid, f) for (p, v, vid, f) in found if (p, vid) not in mod.baseline_keys({})]
    assert new == [("foo", "1.0", "GHSA-xxxx", "1.2")]


@pytest.mark.unit
def test_dep_audit_scanner_failure_is_not_clean(monkeypatch):
    mod = _load("dep_audit")

    class _Proc:
        returncode = 2
        stdout = ""
        stderr = "network error"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _Proc())
    with pytest.raises(SystemExit) as exc:
        mod.run_pip_audit()
    assert exc.value.code == 2  # failure, never treated as clean


@pytest.mark.unit
def test_dep_audit_bad_json_is_scanner_failure(monkeypatch):
    mod = _load("dep_audit")

    class _Proc:
        returncode = 1
        stdout = "not json"
        stderr = ""

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _Proc())
    with pytest.raises(SystemExit) as exc:
        mod.run_pip_audit()
    assert exc.value.code == 2
