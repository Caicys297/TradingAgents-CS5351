"""Offline integration tests for the Stage 2 CLI manifest contract."""

from __future__ import annotations

import builtins
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from cli import run as run_mod
from tradingagents.dataflows.symbols import safe_ticker_component
from tradingagents.repro import manifest as manifest_module

TICKER = "NVDA"
TRADE_DATE = "2026-11-19"
STAMP = "20260101_000000"
COLLISION_ID = "0" * 32
COLLISION_IDS = ("a" * 32, "b" * 32, "c" * 32)
FIRST_RUN_ID = "1" * 32
SECOND_RUN_ID = "2" * 32
REQUIRED_HOOKS = (
    "_reserve_run_directory",
    "_finalize_run_manifest",
    "_artifact_references",
    "RunDirectoryUnavailable",
)
MISSING_HOOKS = [name for name in REQUIRED_HOOKS if not hasattr(run_mod, name)]
if MISSING_HOOKS:
    raise RuntimeError(
        "missing required C-owned Stage 2 CLI hooks: " + ", ".join(MISSING_HOOKS)
    )

pytestmark = pytest.mark.unit

SAVED_SECTIONS = (
    "1_analysts/market.md",
    "2_research/bull.md",
    "2_research/bear.md",
    "2_research/manager.md",
    "3_trading/trader.md",
    "4_risk/aggressive.md",
    "4_risk/conservative.md",
    "4_risk/neutral.md",
    "5_portfolio/decision.md",
)
LIVE_SECTIONS = (
    "investment_plan.md",
    "trader_investment_plan.md",
    "final_trade_decision.md",
)
FINAL_STATE = {
    "market_report": "Market report body.",
    "investment_debate_state": {
        "bull_history": "Bull case.",
        "bear_history": "Bear case.",
    },
    "investment_plan": "Research manager decision.",
    "trader_investment_plan": "Trader plan.",
    "risk_debate_state": {
        "aggressive_history": "Aggressive case.",
        "conservative_history": "Conservative case.",
        "neutral_history": "Neutral case.",
    },
    "final_trade_decision": "**Rating**: Hold\n\nPortfolio decision.",
}


class _FakePropagator:
    def get_graph_args(self, callbacks=None):
        return {}


class _FakePlan:
    def __init__(self):
        self.specs = [SimpleNamespace(key="market", agent_node="Market Analyst")]


class _FakeTracker:
    def __init__(self, plan):
        self.plan = plan

    def mark_started(self, key):
        return None

    def format_summary(self):
        return "elapsed"


class _FakeStats:
    def __init__(self, keys):
        self.keys = keys


class _FakeBuffer:
    def __init__(self):
        self.init_for_analysis(["market"])

    def init_for_analysis(self, keys):
        self.messages = []
        self.report_sections = {}
        self.agent_status = {}
        self._processed_message_ids = set()

    def add_message(self, message_type, content):
        self.messages.append(("now", message_type, content))

    def add_tool_call(self, tool_name, args):
        self.messages.append(("now", "Tool Call", f"{tool_name}({args})"))

    def update_report_section(self, section_name, content):
        self.report_sections[section_name] = content

    def update_agent_status(self, agent, status):
        self.agent_status[agent] = status


class _FakeConsole:
    def __init__(self):
        self.lines = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(arg) for arg in args))

    @property
    def text(self):
        return "\n".join(self.lines)


class _WriteFailingFile:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def write(self, data):
        raise OSError("state log write failed")


class _CloseFailingFile:
    def __init__(self, handle):
        self._handle = handle

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._handle.close()
        if exc_type is None:
            raise OSError("state log close failed")
        return False

    def __getattr__(self, name):
        return getattr(self._handle, name)


def _state_log_input(final_state, ticker, trade_date):
    return {
        **final_state,
        "company_of_interest": ticker,
        "trade_date": trade_date,
        "sentiment_report": final_state.get("sentiment_report", ""),
        "news_report": final_state.get("news_report", ""),
        "fundamentals_report": final_state.get("fundamentals_report", ""),
        "investment_debate_state": {
            **final_state["investment_debate_state"],
            "history": final_state["investment_debate_state"].get("history", ""),
            "current_response": final_state["investment_debate_state"].get(
                "current_response", ""
            ),
        },
        "risk_debate_state": {
            **final_state["risk_debate_state"],
            "history": final_state["risk_debate_state"].get("history", ""),
        },
    }


def _install_harness(
    monkeypatch,
    tmp_path,
    *,
    save=True,
    html=True,
    fail_save=False,
    state_log_failure=None,
    reserve_collision=False,
    external_save=False,
    fail_manifest_write=False,
    rating="Hold",
):
    results_root = tmp_path / "results"
    live_reports = results_root / TICKER / TRADE_DATE / "reports"
    state_dir = results_root / TICKER / "TradingAgentsStrategy_logs"
    state_log = state_dir / f"full_states_log_{TRADE_DATE}.json"
    saved_path = (
        tmp_path / "external_reports" / f"{TICKER}_{STAMP}"
        if external_save
        else results_root / "reports" / f"{TICKER}_{STAMP}"
    )
    live_reports.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    saved_path.mkdir(parents=True, exist_ok=True)
    (live_reports / "stale.md").write_text("old live file", encoding="utf-8")
    (saved_path / "stale.md").write_text("old saved file", encoding="utf-8")
    if state_log_failure:
        state_log.write_text("old state log", encoding="utf-8")

    harness = {
        "calls": [],
        "results_root": results_root,
        "run_base": results_root / TICKER / TRADE_DATE / "runs",
        "live_reports": live_reports,
        "state_log": state_log,
        "saved_path": saved_path,
        "save_calls": 0,
        "record_decision_calls": 0,
        "graph": None,
        "console": _FakeConsole(),
        "rated_state": None,
        "rating": rating,
    }

    config = {
        "results_dir": str(results_root),
        "llm_provider": "openai",
        "deep_think_llm": "deep-model",
        "quick_think_llm": "quick-model",
        "analysts": ["market"],
        "output_language": "English",
        "input_condensation_audit_note": "note-from-run",
        "api_key": "sk-secret",
        "password": "pw-secret",
        "unknown_field": "drop-me",
    }
    selections = {
        "ticker": TICKER,
        "analysis_date": TRADE_DATE,
        "asset_type": "stock",
        "analysts": [SimpleNamespace(value="market")],
    }

    if reserve_collision:
        collision = harness["run_base"] / COLLISION_ID
        collision.mkdir(parents=True, exist_ok=True)
        (collision / "keep.txt").write_text("keep", encoding="utf-8")
        monkeypatch.setattr(
            run_mod,
            "uuid",
            SimpleNamespace(uuid4=lambda: SimpleNamespace(hex=COLLISION_ID)),
        )

    if fail_manifest_write:
        def fail_write(*args, **kwargs):
            raise OSError("manifest write failed")

        monkeypatch.setattr(manifest_module, "write_manifest", fail_write)

    if state_log_failure:
        assert state_log_failure in {"write", "close"}
        real_open = builtins.open

        def failing_open(path, mode="r", *args, **kwargs):
            if "TradingAgentsStrategy_logs" in str(path) and "w" in mode:
                if state_log_failure == "write":
                    return _WriteFailingFile()
                return _CloseFailingFile(real_open(path, mode, *args, **kwargs))
            return real_open(path, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", failing_open)

    real_graph_class = run_mod.TradingAgentsGraph

    class FakeGraph:
        def __init__(self, analysts, *, config, debug):
            harness["calls"].append("graph_init")
            harness["graph"] = self
            self.config = config
            self.propagator = _FakePropagator()

        def create_run_state(self, ticker, trade_date, asset_type, portfolio):
            return {"ticker": ticker}

        def begin_checkpoint(self, ticker, trade_date, asset_type, portfolio):
            return None

        def checkpoint_input(self, state):
            return state

        def stream_run(self, state, **kwargs):
            yield [], FINAL_STATE

        def record_decision(self, ticker, trade_date, final_state):
            harness["calls"].append("record_decision")
            harness["record_decision_calls"] += 1
            if state_log_failure:
                real_graph_class._log_state(
                    self,
                    trade_date,
                    _state_log_input(final_state, ticker, trade_date),
                )
                return
            state_dir.mkdir(parents=True, exist_ok=True)
            state_log.write_text(json.dumps({"decision": "Hold"}), encoding="utf-8")

        def run_settings(self):
            return {}

        def clear_checkpoint_on_success(self, ticker, trade_date, asset_type, portfolio):
            return None

        def end_checkpoint(self):
            return None

        def default_report_path(self, ticker):
            return saved_path

        def save_reports(self, final_state, ticker, save_path, html=True):
            harness["calls"].append("save_reports")
            harness["save_calls"] += 1
            if fail_save:
                save_path = Path(save_path)
                save_path.mkdir(parents=True, exist_ok=True)
                (save_path / "partial.md").write_text("partial", encoding="utf-8")
                raise OSError("report save failed")
            from tradingagents.reporting import write_report_tree

            return write_report_tree(
                final_state, ticker, save_path, settings=None, html=html
            )

    def fake_rating(state):
        harness["rated_state"] = state
        return harness["rating"]

    monkeypatch.setattr(run_mod, "TradingAgentsGraph", FakeGraph)
    monkeypatch.setattr(run_mod, "get_user_selections", lambda flags=None: dict(selections))
    monkeypatch.setattr(run_mod, "unattended_gaps", lambda flags: [])
    monkeypatch.setattr(run_mod, "_build_run_config", lambda selections, checkpoint: dict(config))
    monkeypatch.setattr(run_mod, "build_analyst_execution_plan", lambda keys: _FakePlan())
    monkeypatch.setattr(run_mod, "AnalystWallTimeTracker", _FakeTracker)
    monkeypatch.setattr(run_mod, "StatsCallbackHandler", _FakeStats)
    monkeypatch.setattr(run_mod, "create_layout", lambda: SimpleNamespace())
    monkeypatch.setattr(run_mod, "Live", lambda *args, **kwargs: nullcontext())
    monkeypatch.setattr(run_mod, "update_display", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_mod, "update_analyst_statuses", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_mod, "update_research_team_status", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_mod, "display_agent_summary", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_mod, "display_complete_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_mod, "console", harness["console"])
    monkeypatch.setattr(run_mod, "is_review", lambda rating: rating == "REVIEW")
    monkeypatch.setattr(run_mod, "run_rating", fake_rating)
    monkeypatch.setattr(run_mod, "message_buffer", _FakeBuffer())
    return harness, save, html


def _invoke(harness, save, html):
    run_mod.run_analysis(
        checkpoint=False,
        flags={
            "ticker": TICKER,
            "date": TRADE_DATE,
            "analysts": ["market"],
            "save": save,
            "show": False,
            "html": html,
        },
    )
    return harness


def _run(monkeypatch, tmp_path, **options):
    harness, save, html = _install_harness(monkeypatch, tmp_path, **options)
    return _invoke(harness, save, html)


def _run_dir(harness):
    dirs = [path for path in harness["run_base"].iterdir() if path.is_dir()]
    assert len(dirs) == 1, dirs
    return dirs[0]


def _manifest(harness):
    path = _run_dir(harness) / "manifest.json"
    assert path.is_file()
    return path, json.loads(path.read_text(encoding="utf-8"))


def _artifact_paths(manifest):
    return [artifact["path"].replace("\\", "/") for artifact in manifest["artifacts"]]


def _saved_root(harness):
    return harness["saved_path"].relative_to(harness["results_root"]).as_posix()


def _expected_paths(harness, *, include_saved):
    expected = {
        f"{safe_ticker_component(TICKER)}/{TRADE_DATE}/message_tool.log",
        f"{safe_ticker_component(TICKER)}/TradingAgentsStrategy_logs/full_states_log_{TRADE_DATE}.json",
    }
    expected.update(
        f"{safe_ticker_component(TICKER)}/{TRADE_DATE}/reports/{name}"
        for name in LIVE_SECTIONS
    )
    if include_saved:
        root = _saved_root(harness)
        expected.update(f"{root}/{name}" for name in SAVED_SECTIONS)
        expected.add(f"{root}/complete_report.md")
        expected.add(f"{root}/complete_report.html")
    return expected


def _assert_exact_inventory(harness, *, include_saved):
    _, manifest = _manifest(harness)
    artifacts = manifest["artifacts"]
    paths = _artifact_paths(manifest)
    expected = _expected_paths(harness, include_saved=include_saved)

    assert set(paths) == expected
    assert len(paths) == len(set(paths))
    assert {artifact["stability"] for artifact in artifacts} == {"shared_mutable"}
    assert all(artifact["name"] for artifact in artifacts)
    return manifest


def test_real_cli_success_writes_manifest_exact_inventory_and_output(
    monkeypatch, tmp_path
):
    harness = _run(monkeypatch, tmp_path, save=True, html=True)
    manifest = _assert_exact_inventory(harness, include_saved=True)
    manifest_path, _ = _manifest(harness)

    assert "graph_init" in harness["calls"]
    assert harness["save_calls"] == 1
    assert manifest["identity"]["ticker"] == TICKER
    assert manifest_path.parent == _run_dir(harness)
    assert "Manifest written to:" in harness["console"].text
    assert str(manifest_path) in harness["console"].text
    assert "stale.md" not in harness["console"].text


def test_real_reservation_retries_and_isolates_two_runs(monkeypatch, tmp_path):
    harness, save, html = _install_harness(
        monkeypatch, tmp_path, save=False, html=False
    )
    run_base = harness["run_base"]
    run_base.mkdir(parents=True, exist_ok=True)
    for collision_id in COLLISION_IDS:
        collision = run_base / collision_id
        collision.mkdir()
        (collision / "keep.txt").write_text(collision_id, encoding="utf-8")

    sequence = [
        COLLISION_IDS[0],
        FIRST_RUN_ID,
        COLLISION_IDS[1],
        COLLISION_IDS[2],
        SECOND_RUN_ID,
    ]
    attempts = []

    def uuid4():
        value = sequence[len(attempts)]
        attempts.append(value)
        return SimpleNamespace(hex=value)

    monkeypatch.setattr(run_mod, "uuid", SimpleNamespace(uuid4=uuid4))
    _invoke(harness, save, html)
    _invoke(harness, save, html)

    assert attempts == sequence
    assert harness["calls"].count("graph_init") == 2
    assert harness["record_decision_calls"] == 2
    run_dirs = {
        path.name: path
        for path in run_base.iterdir()
        if path.name in {FIRST_RUN_ID, SECOND_RUN_ID}
    }
    assert set(run_dirs) == {FIRST_RUN_ID, SECOND_RUN_ID}
    manifests = [
        json.loads((run_dirs[run_id] / "manifest.json").read_text(encoding="utf-8"))
        for run_id in (FIRST_RUN_ID, SECOND_RUN_ID)
    ]
    assert len(manifests) == 2
    assert manifests[0]["identity"] == manifests[1]["identity"]
    for collision_id in COLLISION_IDS:
        assert (run_base / collision_id / "keep.txt").read_text(
            encoding="utf-8"
        ) == collision_id


def test_declined_save_excludes_only_optional_tree(monkeypatch, tmp_path):
    harness = _run(monkeypatch, tmp_path, save=False, html=True)

    assert harness["save_calls"] == 0
    _assert_exact_inventory(harness, include_saved=False)


def test_whole_save_failure_excludes_partial_leftover(monkeypatch, tmp_path):
    harness = _run(monkeypatch, tmp_path, save=True, html=True, fail_save=True)

    assert (harness["saved_path"] / "partial.md").is_file()
    _assert_exact_inventory(harness, include_saved=False)


def test_external_save_is_written_but_omitted_from_manifest(monkeypatch, tmp_path):
    harness = _run(monkeypatch, tmp_path, save=True, html=True, external_save=True)
    _, manifest = _manifest(harness)
    paths = _artifact_paths(manifest)

    assert harness["save_calls"] == 1
    assert (harness["saved_path"] / "complete_report.md").is_file()
    assert all("external_reports" not in path for path in paths)
    expected = _expected_paths(harness, include_saved=False)
    assert set(paths) == expected


def test_state_log_write_failure_propagates_without_manifest(monkeypatch, tmp_path):
    harness, save, html = _install_harness(
        monkeypatch, tmp_path, state_log_failure="write"
    )

    with pytest.raises(OSError, match="state log write failed"):
        _invoke(harness, save, html)

    assert harness["state_log"].read_text(encoding="utf-8") == "old state log"
    assert not (_run_dir(harness) / "manifest.json").exists()
    assert harness["rated_state"] is None


def test_state_log_close_failure_propagates_without_manifest(monkeypatch, tmp_path):
    harness, save, html = _install_harness(
        monkeypatch, tmp_path, state_log_failure="close"
    )

    with pytest.raises(OSError, match="state log close failed"):
        _invoke(harness, save, html)

    assert harness["state_log"].is_file()
    assert harness["state_log"].read_text(encoding="utf-8") != "old state log"
    assert not (_run_dir(harness) / "manifest.json").exists()
    assert harness["rated_state"] is None


@pytest.mark.parametrize("rating", ["Hold", "REVIEW"])
def test_manifest_write_failure_is_fail_soft_with_effective_rating(
    monkeypatch, tmp_path, rating
):
    harness = _run(
        monkeypatch,
        tmp_path,
        save=True,
        html=True,
        fail_manifest_write=True,
        rating=rating,
    )
    run_dir = _run_dir(harness)

    assert harness["record_decision_calls"] == 1
    assert harness["rated_state"] == FINAL_STATE
    assert (harness["saved_path"] / "complete_report.md").is_file()
    assert not (run_dir / "manifest.json").exists()
    assert "Manifest not saved" in harness["console"].text
    assert "analysis result above stands" in harness["console"].text
    assert "Manifest written to:" not in harness["console"].text
    if rating == "REVIEW":
        assert "recorded for review" in harness["console"].text
    else:
        assert "recorded for review" not in harness["console"].text


def test_tc23_effective_config_allowlist_and_secret_exclusion(monkeypatch, tmp_path):
    harness = _run(monkeypatch, tmp_path, save=False, html=False)
    _, manifest = _manifest(harness)

    assert set(manifest["config"]) == set(manifest_module.CONFIG_ALLOWLIST)
    assert manifest["config"]["input_condensation_audit_note"] == "note-from-run"
    serialized = json.dumps(manifest, ensure_ascii=False)
    assert "sk-secret" not in serialized
    assert "pw-secret" not in serialized
    assert "unknown_field" not in serialized


def test_reservation_collision_exits_before_graph_and_preserves_existing_files(
    monkeypatch, tmp_path
):
    harness, save, html = _install_harness(
        monkeypatch, tmp_path, reserve_collision=True
    )
    keep = harness["run_base"] / COLLISION_ID / "keep.txt"

    with pytest.raises(run_mod.typer.Exit):
        run_mod.run_analysis(
            checkpoint=False,
            flags={
                "ticker": TICKER,
                "date": TRADE_DATE,
                "analysts": ["market"],
                "save": save,
                "show": False,
                "html": html,
            },
        )

    assert "graph_init" not in harness["calls"]
    assert keep.read_text(encoding="utf-8") == "keep"
    assert not (_run_dir(harness) / "manifest.json").exists()
