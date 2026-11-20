"""Offline tests for the hardened CI gate checkers (scripts/*.py).

Deterministic: no real mypy/pip-audit network scan. They prove the checkers fail
closed and enforce the corrected policies: trusted-base baselines with a real
bootstrap-vs-resolution distinction, symbol-aware per-diagnostic multiplicity,
structural dependency-report validation, and genuine-new-entry AI-use checks.
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


def _use_local_baseline(monkeypatch, mod, baseline: Path):
    """Force the checker to use a working-tree baseline (no PR base resolution)."""
    monkeypatch.setattr(mod, "BASELINE", baseline)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)


@pytest.mark.unit
def test_typecheck_symbol_in_identity_distinct_functions():
    mod = _load("typecheck")
    a = ['cli/run.py: note: In function "funcA":',
         "cli/run.py:10: error: Cannot assign to a method  [method-assign]"]
    b = ['cli/run.py: note: In function "funcB":',
         "cli/run.py:20: error: Cannot assign to a method  [method-assign]"]
    assert list(mod.parse(a)) != list(mod.parse(b))
    assert list(mod.parse(a))[0].split(":")[1] == "funcA"


@pytest.mark.unit
def test_typecheck_same_total_move_between_functions_blocks(monkeypatch, tmp_path):
    """Old identical diag in funcA removed; identical in funcB added; total equal -> blocks."""
    mod = _load("typecheck")
    base = ['cli/run.py: note: In function "funcA":', "cli/run.py:10: error: X  [method-assign]"]
    cur = ['cli/run.py: note: In function "funcB":', "cli/run.py:20: error: X  [method-assign]"]
    b = _mk_baseline(tmp_path, list(mod.parse(base)))
    _use_local_baseline(monkeypatch, mod, b)
    monkeypatch.setattr(mod, "run_mypy", lambda: cur)
    assert mod.main([]) == 1


@pytest.mark.unit
def test_typecheck_multiplicity_two_identical_need_two_in_baseline(monkeypatch, tmp_path):
    mod = _load("typecheck")
    one = ['cli/run.py: note: In function "f":', "cli/run.py:188: error: X  [method-assign]"]
    ident = list(mod.parse(one))[0]
    b = _mk_baseline(tmp_path, [ident])  # baseline count 1
    _use_local_baseline(monkeypatch, mod, b)
    # mypy yields the same line TWICE -> count 2 -> one new occurrence blocks
    monkeypatch.setattr(mod, "run_mypy", lambda: [one[0], one[1], one[1]])
    assert mod.main([]) == 1


@pytest.mark.unit
def test_typecheck_removal_does_not_offset_new(monkeypatch, tmp_path):
    mod = _load("typecheck")
    old = list(mod.parse(["old.py:1: error: Old issue  [arg-type]"]))[0]
    b = _mk_baseline(tmp_path, [old])
    _use_local_baseline(monkeypatch, mod, b)
    monkeypatch.setattr(mod, "run_mypy", lambda: ["new.py:1: error: New issue  [return-value]"])
    assert mod.main([]) == 1


@pytest.mark.unit
def test_typecheck_trusted_base_ignores_pr_widening(monkeypatch, tmp_path):
    mod = _load("typecheck")
    newline = "x.py:1: error: Brand new  [return-value]"
    ident = list(mod.parse([newline]))[0]
    b = _mk_baseline(tmp_path, [ident])  # PR tree WIDENED to include the new identity
    monkeypatch.setattr(mod, "BASELINE", b)
    # trusted base has an EMPTY baseline:
    monkeypatch.setattr(mod, "_baseline_state", lambda ref: ("# empty\n", "abc123"))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    monkeypatch.setattr(mod, "run_mypy", lambda: [newline])
    assert mod.main([]) == 1  # trusted base wins


@pytest.mark.unit
def test_typecheck_base_resolution_failure_is_exit2(monkeypatch):
    mod = _load("typecheck")

    class _P:
        returncode = 128
        stdout = ""
        stderr = "could not resolve"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _P())
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    with pytest.raises(SystemExit) as exc:
        mod.load_baseline()
    assert exc.value.code == 2


@pytest.mark.unit
def test_typecheck_genuine_absence_bootstraps(monkeypatch, tmp_path):
    mod = _load("typecheck")

    class _P:
        def __init__(self, rc, out=""):
            self.returncode = rc
            self.stdout = out
            self.stderr = ""

    def fake_run(cmd, *a, **k):
        joined = " ".join(cmd)
        if "rev-parse" in joined:
            return _P(0, "deadbeefdeadbeef\n")
        if "cat-file" in joined:
            return _P(1)  # path genuinely absent on base
        return _P(0, "")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    local = tmp_path / "mypy-baseline.txt"
    local.write_text("# baseline\n")
    monkeypatch.setattr(mod, "BASELINE", local)
    _, source = mod.load_baseline()
    assert "working tree" in source
    # distinguish from a resolution failure handled in the other test


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
    assert exc.value.code == 2


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
def test_dep_audit_new_finding_blocks(monkeypatch, tmp_path):
    mod = _load("dep_audit")
    report = {"dependencies": [{"name": "foo", "version": "1.0",
                                "vulns": [{"id": "GHSA-x", "fix_versions": ["1.2"]}]}]}
    monkeypatch.setattr(mod, "run_pip_audit", lambda: report)
    monkeypatch.setattr(mod, "_load_baseline", lambda: ({"findings": []}, "test"))
    assert mod.main([]) == 1


@pytest.mark.unit
def test_dep_audit_allowance_version_specific():
    mod = _load("dep_audit")
    base = {"findings": [{"package": "foo", "id": "GHSA-x", "affected_version": "1.0"}]}
    keys = mod.baseline_keys(base)
    found = [("foo", "2.0", "GHSA-x", "no fix")]
    new = [(p, v, vid, f) for (p, v, vid, f) in found if (p, vid, v) not in keys]
    assert new


@pytest.mark.unit
def test_dep_audit_pending_metadata_rejected():
    mod = _load("dep_audit")
    base = {"findings": [{"package": "foo", "id": "GHSA-x", "affected_version": "1.0",
                          "owner": "PENDING", "status": "PENDING"}]}
    assert mod.validate_baseline(base)


@pytest.mark.unit
def test_dep_audit_base_resolution_failure_is_exit2(monkeypatch):
    mod = _load("dep_audit")

    class _P:
        returncode = 128
        stdout = ""
        stderr = "bad ref"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _P())
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    with pytest.raises(SystemExit) as exc:
        mod._load_baseline()
    assert exc.value.code == 2


# ============================================================ AI-use gate
# Unit-test the pure entry validation (no git); integration-level diff behaviour
# is covered by the DiffError / no-base tests below.


def _v(lines: list[str], root: Path, base_ref: str = "main", check_commits: bool = False) -> list[str]:
    mod = _load("check_ai_use_log")
    return mod._validate_entry(lines, root, base_ref, check_commits=check_commits)


@pytest.mark.unit
def test_ai_use_not_applicable_for_docs_only(tmp_path):
    mod = _load("check_ai_use_log")
    assert mod.check(["docs/readme.md"], tmp_path, base_ref="main") == []


@pytest.mark.unit
def test_ai_use_no_log_change_fails(tmp_path):
    mod = _load("check_ai_use_log")
    errs = mod.check(["tradingagents/x.py"], tmp_path, base_ref="main")
    assert errs and "no AI-use log change" in errs[0]


@pytest.mark.unit
def test_ai_use_whitespace_only_fails(tmp_path):
    assert any("whitespace-only" in e.lower() for e in _v(["   ", "  "], tmp_path))


@pytest.mark.unit
def test_ai_use_missing_field_label_fails(tmp_path):
    assert any("missing field label" in e for e in _v(["Session: https://x/y/session/1"], tmp_path))


@pytest.mark.unit
def test_ai_use_bare_pr_url_rejected(tmp_path):
    lines = ["Task: t. Scope: s. Commit: abc1234.",
             "See https://github.com/o/r/pull/29"]
    assert any("PR URL is not session evidence" in e for e in _v(lines, tmp_path))


@pytest.mark.unit
def test_ai_use_pr_url_with_session_query_rejected(tmp_path):
    lines = ["Task: t. Scope: s. Commit: abc1234.",
             "See https://github.com/o/r/pull/29?tab=session&export=1"]
    assert any("PR URL is not session evidence" in e for e in _v(lines, tmp_path))


@pytest.mark.unit
def test_ai_use_absolute_path_rejected(tmp_path):
    lines = ["Task: t. Scope: s. Commit: abc1234.",
             "Session: https://x.com/session/1", "Local: /Users/me/secret"]
    assert any("absolute path" in e for e in _v(lines, tmp_path))


@pytest.mark.unit
def test_ai_use_summary_file_is_not_export_evidence(tmp_path):
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts/CI-session-export.md").write_text(
        "# authored activity summary\nThis is NOT a raw export.\n"
    )
    lines = ["Task: t. Scope: s. Commit: abc1234.",
             "Evidence: transcripts/CI-session-export.md"]
    assert any("no genuine session/export" in e for e in _v(lines, tmp_path))


@pytest.mark.unit
def test_ai_use_json_export_reference_passes(tmp_path):
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts/session.json").write_text(
        '{"messages":[{"parts":[{"type":"text","text":"hello"}]}]}'
    )
    lines = ["Task: t. Usage scope: s. Implementation commit: abc1234.",
             "Evidence: transcripts/session.json"]
    assert _v(lines, tmp_path) == []


@pytest.mark.unit
def test_ai_use_diff_failure_raises(monkeypatch, tmp_path):
    mod = _load("check_ai_use_log")

    class _P:
        returncode = 128
        stdout = ""
        stderr = "no merge base"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _P())
    with pytest.raises(mod.DiffError):
        mod.added_lines(tmp_path / "x.md", "main")


@pytest.mark.unit
def test_ai_use_no_base_for_code_change_is_exit3(tmp_path, monkeypatch):
    mod = _load("check_ai_use_log")
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    (tmp_path / "scripts").mkdir()
    assert mod.main(["--changed-file", "scripts/x.py", "--root", str(tmp_path)]) == 3


@pytest.mark.unit
def test_ai_use_changed_from_file_handles_spaces(tmp_path):
    z = tmp_path / "changed.z"
    z.write_bytes(b"docs/a file.md\x00tradingagents/x.py\x00")
    mod = _load("check_ai_use_log")
    assert mod._changed_from_file(z) == ["docs/a file.md", "tradingagents/x.py"]


# ============================================================ Range + export hardening (final)

def _git(repo: Path, *args: str) -> str:
    import subprocess as _sp
    return _sp.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def _make_history(tmp: Path):
    """Create a genuine temp git history: base commit + PR commits, with an
    origin/main ref pointing at base (mirrors CI's verified base)."""
    import subprocess as _sp

    _sp.run(["git", "init", "-q", "-b", "main", str(tmp)], check=True)
    _git(tmp, "config", "user.email", "t@t")
    _git(tmp, "config", "user.name", "t")
    (tmp / "a.txt").write_text("base")
    _git(tmp, "add", "a.txt")
    _git(tmp, "commit", "-qm", "base")
    base = _git(tmp, "rev-parse", "HEAD")
    _sp.run(["git", "-C", str(tmp), "update-ref", "refs/remotes/origin/main", base], check=True)
    # PR implementation commit
    (tmp / "b.txt").write_text("impl")
    _git(tmp, "add", "b.txt")
    _git(tmp, "commit", "-qm", "impl")
    impl = _git(tmp, "rev-parse", "HEAD")
    # evidence-only follow-up commit
    (tmp / "c.txt").write_text("evidence")
    _git(tmp, "add", "c.txt")
    _git(tmp, "commit", "-qm", "evidence")
    follow = _git(tmp, "rev-parse", "HEAD")
    # unrelated: a commit on a detached orphan
    _sp.run(["git", "-C", str(tmp), "checkout", "-q", "--orphan", "orph"], check=True)
    (tmp / "z.txt").write_text("z")
    _git(tmp, "add", "z.txt")
    _git(tmp, "commit", "-qm", "unrelated")
    unrelated = _git(tmp, "rev-parse", "HEAD")
    _sp.run(["git", "-C", str(tmp), "checkout", "-q", "main"], check=True)
    return base, impl, follow, unrelated


@pytest.mark.unit
def test_commit_in_range_rejects_base_sha(tmp_path):
    mod = _load("check_ai_use_log")
    base, impl, follow, unrelated = _make_history(tmp_path)
    assert mod._commit_in_range(base, "main", tmp_path) is False


@pytest.mark.unit
def test_commit_in_range_rejects_unrelated_sha(tmp_path):
    mod = _load("check_ai_use_log")
    base, impl, follow, unrelated = _make_history(tmp_path)
    assert mod._commit_in_range(unrelated, "main", tmp_path) is False


@pytest.mark.unit
def test_commit_in_range_accepts_pr_impl_sha(tmp_path):
    mod = _load("check_ai_use_log")
    base, impl, follow, unrelated = _make_history(tmp_path)
    assert mod._commit_in_range(impl, "main", tmp_path) is True


@pytest.mark.unit
def test_commit_in_range_accepts_earlier_impl_from_followup(tmp_path):
    """An evidence-only follow-up may reference the earlier implementation commit."""
    mod = _load("check_ai_use_log")
    base, impl, follow, unrelated = _make_history(tmp_path)
    # HEAD is 'follow'; impl is reachable from HEAD and not from base -> accepted.
    assert mod._commit_in_range(impl, "main", tmp_path) is True


@pytest.mark.unit
def test_export_empty_json_rejected(tmp_path):
    mod = _load("check_ai_use_log")
    p = tmp_path / "e.json"
    p.write_text("{}")
    assert mod._is_genuine_export(p) is False


@pytest.mark.unit
def test_export_metadata_only_rejected(tmp_path):
    mod = _load("check_ai_use_log")
    p = tmp_path / "meta.json"
    p.write_text('{"note":"long provenance note "*3,"full_export_sha256":"abc","message_count":5}')
    assert mod._is_genuine_export(p) is False


@pytest.mark.unit
def test_export_messages_parts_accepted(tmp_path):
    mod = _load("check_ai_use_log")
    p = tmp_path / "real.json"
    p.write_text('{"messages":[{"parts":[{"type":"text","text":"hello"}]}]}')
    assert mod._is_genuine_export(p) is True


@pytest.mark.unit
def test_export_authored_summary_md_rejected(tmp_path):
    mod = _load("check_ai_use_log")
    p = tmp_path / "summary.md"
    p.write_text("# authored summary\nThis is NOT a raw export.")
    assert mod._is_genuine_export(p) is False

