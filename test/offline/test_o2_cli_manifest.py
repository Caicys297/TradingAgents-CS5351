"""Offline integration tests for the Stage 2 CLI manifest contract."""

from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from tradingagents.dataflows.symbols import safe_ticker_component
from tradingagents.repro import manifest as manifest_module

try:
    from cli import run as run_mod
except ModuleNotFoundError:
    run_mod = None


TICKER = "NVDA"
TRADE_DATE = "2026-11-19"
RUN_ID = "run1"
STAMP = "20260101_000000"
REQUIRED_HOOKS = (
    "_reserve_run_directory",
    "_finalize_run_manifest",
    "_artifact_references",
    "RunDirectoryUnavailable",
)
HOOKS_READY = run_mod is not None and all(
    hasattr(run_mod, name) for name in REQUIRED_HOOKS
)

pytestmark = [
    pytest.mark.unit,
    pytest.mark.skipif(
        not HOOKS_READY,
        reason="CLI runtime dependencies or C-owned Stage 2 hooks are unavailable",
    ),
]

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
    def print(self, *args, **kwargs):
        return None


def _install_harness(
    monkeypatch,
    tmp_path,
    *,
    save=True,
    html=True,
    fail_save=False,
    state_log_failure=False,
    reserve_failure=False,
    external_save=False,
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
        "live_reports": live_reports,
        "state_log": state_log,
        "saved_path": saved_path,
        "save_calls": 0,
        "save_return": None,
        "artifacts": None,
        "manifest": None,
        "manifest_path": None,
    }

    config = {
        "results_dir": str(results_root),
        "llm_provider": "openai",
        "deep_think_llm": "deep-model",
        "quick_think_llm": "quick-model",
        "analysts": ["market"],
        "output_language": "English",
    }
    selections = {
        "ticker": TICKER,
        "analysis_date": TRADE_DATE,
        "asset_type": "stock",
        "analysts": [SimpleNamespace(value="market")],
    }

    def fake_reserve(results_dir, ticker, trade_date):
        harness["calls"].append("reserve")
        if reserve_failure:
            raise run_mod.RunDirectoryUnavailable("no run directory")
        run_dir = (
            Path(results_dir) / safe_ticker_component(ticker) / trade_date / "runs" / RUN_ID
        )
        run_dir.mkdir(parents=True, exist_ok=False)
        return SimpleNamespace(run_id=RUN_ID, run_dir=run_dir)

    def fake_finalize(run_context, *, config, artifacts):
        harness["calls"].append("finalize")
        manifest = manifest_module.build_manifest(
            ticker=TICKER,
            asset_type="stock",
            analysis_date=TRADE_DATE,
            analysts=["market"],
            config=config,
            runtime=manifest_module.collect_runtime_metadata(git_metadata=None),
            artifacts=artifacts,
        )
        path = manifest_module.write_manifest(
            Path(run_context.run_dir) / "manifest.json", manifest
        )
        harness["artifacts"] = list(artifacts)
        harness["manifest"] = manifest
        harness["manifest_path"] = path
        return SimpleNamespace(
            success=True,
            manifest_path=path,
            artifacts=list(artifacts),
            error=None,
        )

    class FakeGraph:
        def __init__(self, analysts, *, config, debug):
            harness["calls"].append("graph_init")
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
            if state_log_failure:
                raise OSError("state log write failed")
            state_dir.mkdir(parents=True, exist_ok=True)
            state_log.write_text(json.dumps({"decision": "Hold"}), encoding="utf-8")

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

            harness["save_return"] = write_report_tree(
                final_state, ticker, save_path, settings=None, html=html
            )
            return harness["save_return"]

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
    monkeypatch.setattr(run_mod, "console", _FakeConsole())
    monkeypatch.setattr(run_mod, "is_review", lambda rating: False)
    monkeypatch.setattr(run_mod, "run_rating", lambda state: "Hold")
    monkeypatch.setattr(run_mod, "message_buffer", _FakeBuffer())
    monkeypatch.setattr(run_mod, "_reserve_run_directory", fake_reserve, raising=False)
    monkeypatch.setattr(run_mod, "_finalize_run_manifest", fake_finalize, raising=False)
    return harness, config, save, html


def _run(monkeypatch, tmp_path, **options):
    harness, config, save, html = _install_harness(monkeypatch, tmp_path, **options)
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


def _artifacts_by_path(harness):
    return {
        artifact["path"].replace("\\", "/"): artifact
        for artifact in harness["artifacts"]
    }


def _assert_shared_artifact(paths, suffix):
    matches = [
        path
        for path in paths
        if path.endswith(suffix)
    ]
    assert len(matches) == 1, (suffix, paths)
    assert paths[matches[0]]["stability"] == "shared_mutable"


def test_success_registers_written_artifacts_and_excludes_stale_files(
    monkeypatch, tmp_path
):
    harness = _run(monkeypatch, tmp_path, save=True, html=True)
    paths = _artifacts_by_path(harness)
    saved_root = f"reports/{TICKER}_{STAMP}/"

    assert harness["calls"].index("reserve") < harness["calls"].index("graph_init")
    assert harness["calls"].index("save_reports") < harness["calls"].index("finalize")
    assert harness["save_calls"] == 1
    assert harness["save_return"] == harness["saved_path"] / "complete_report.md"

    assert saved_root + "complete_report.md" in paths
    assert saved_root + "complete_report.html" in paths
    assert saved_root + "1_analysts/market.md" in paths
    assert saved_root + "2_research/bull.md" in paths
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/reports/investment_plan.md")
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/reports/final_trade_decision.md")
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/message_tool.log")
    _assert_shared_artifact(
        paths, f"{TICKER}/TradingAgentsStrategy_logs/full_states_log_{TRADE_DATE}.json"
    )
    assert saved_root + "stale.md" not in paths
    assert f"{TICKER}/{TRADE_DATE}/reports/stale.md" not in paths


def test_declined_save_excludes_only_the_optional_save_tree(monkeypatch, tmp_path):
    harness = _run(monkeypatch, tmp_path, save=False, html=True)
    paths = _artifacts_by_path(harness)

    assert harness["save_calls"] == 0
    assert all(not path.startswith(f"reports/{TICKER}_{STAMP}/") for path in paths)
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/reports/investment_plan.md")
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/message_tool.log")
    _assert_shared_artifact(
        paths, f"{TICKER}/TradingAgentsStrategy_logs/full_states_log_{TRADE_DATE}.json"
    )


def test_whole_save_failure_registers_no_optional_files_even_with_partial_leftover(
    monkeypatch, tmp_path
):
    harness = _run(monkeypatch, tmp_path, save=True, html=True, fail_save=True)
    paths = _artifacts_by_path(harness)

    assert (harness["saved_path"] / "partial.md").is_file()
    assert all(not path.startswith(f"reports/{TICKER}_{STAMP}/") for path in paths)
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/reports/investment_plan.md")
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/message_tool.log")
    _assert_shared_artifact(
        paths, f"{TICKER}/TradingAgentsStrategy_logs/full_states_log_{TRADE_DATE}.json"
    )


def test_external_save_succeeds_but_is_omitted_from_the_manifest(monkeypatch, tmp_path):
    harness = _run(monkeypatch, tmp_path, save=True, html=True, external_save=True)
    paths = _artifacts_by_path(harness)

    assert harness["save_calls"] == 1
    assert (harness["saved_path"] / "complete_report.md").is_file()
    assert all("external_reports" not in path for path in paths)
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/reports/investment_plan.md")
    _assert_shared_artifact(paths, f"{TICKER}/{TRADE_DATE}/message_tool.log")
    _assert_shared_artifact(
        paths, f"{TICKER}/TradingAgentsStrategy_logs/full_states_log_{TRADE_DATE}.json"
    )


def test_state_log_failure_propagates_and_prevents_manifest_finalization(
    monkeypatch, tmp_path
):
    harness, _, _, _ = _install_harness(
        monkeypatch, tmp_path, state_log_failure=True
    )

    with pytest.raises(OSError, match="state log write failed"):
        run_mod.run_analysis(
            checkpoint=False,
            flags={
                "ticker": TICKER,
                "date": TRADE_DATE,
                "analysts": ["market"],
                "save": False,
                "show": False,
                "html": False,
            },
        )

    assert harness["state_log"].read_text(encoding="utf-8") == "old state log"
    assert "finalize" not in harness["calls"]
    assert harness["manifest_path"] is None


def test_reservation_failure_exits_before_graph_and_preserves_existing_files(
    monkeypatch, tmp_path
):
    harness, _, _, _ = _install_harness(
        monkeypatch, tmp_path, reserve_failure=True
    )
    existing = tmp_path / "results" / "keep.txt"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("keep", encoding="utf-8")

    with pytest.raises(run_mod.typer.Exit):
        run_mod.run_analysis(
            checkpoint=False,
            flags={
                "ticker": TICKER,
                "date": TRADE_DATE,
                "analysts": ["market"],
                "save": False,
                "show": False,
                "html": False,
            },
        )

    assert "graph_init" not in harness["calls"]
    assert existing.read_text(encoding="utf-8") == "keep"
