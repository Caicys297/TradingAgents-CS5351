"""Running one analysis from the CLI: build the graph, stream it into the live view, save the report."""

import os
import sys
import time
import uuid
import webbrowser
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

import typer
from rich.live import Live

from cli.display import (
    ANALYST_ORDER,
    AnalystWallTimeTracker,
    classify_message_type,
    console,
    create_layout,
    display_agent_summary,
    display_complete_report,
    message_buffer,
    update_analyst_statuses,
    update_display,
    update_research_team_status,
)
from cli.selections import depth_from_env, get_user_selections, unattended_gaps
from cli.stats_handler import StatsCallbackHandler
from tradingagents.agents.rating import is_review, run_rating
from tradingagents.dataflows.symbols import safe_ticker_component
from tradingagents.dataflows.vendors.yahoo.news import o5_evidence_run
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.analyst_execution import (
    build_analyst_execution_plan,
)
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.reporting import _report_parts as report_parts
from tradingagents.repro import manifest as manifest_module


def _is_pm_message(message) -> bool:
    """Whether a streamed message is the Portfolio Manager's own output.

    Read from the message metadata production attaches (``langgraph_node``), so
    the decision is made from the real event rather than from the text.
    """
    meta = getattr(message, "response_metadata", None) or {}
    node = meta.get("langgraph_node")
    if isinstance(node, str):
        return "portfolio" in node.lower() or "portfolio manager" in node.lower()
    additional = getattr(message, "additional_kwargs", None) or {}
    node = additional.get("langgraph_node")
    return isinstance(node, str) and (
        "portfolio" in node.lower() or "portfolio manager" in node.lower()
    )


def _run_directory(config: dict, ticker: str, trade_date: str) -> Path:
    """Where this run writes, with the ticker validated as a path component.

    Every other path that interpolates a ticker checks it first; a value of
    ".." here would place the run outside the results directory.
    """
    return Path(config["results_dir"]) / safe_ticker_component(ticker) / trade_date


class RunDirectoryUnavailable(RuntimeError):
    """No per-run directory could be reserved for this run."""


def _state_log_path(config: dict, ticker: str, trade_date: str) -> Path:
    """Where the graph writes this run's state log.

    Reconstructed with the same config root, ticker safety and date the writer
    uses, so a normal return means the file is exactly here.
    """
    return (
        Path(config["results_dir"])
        / safe_ticker_component(ticker)
        / "TradingAgentsStrategy_logs"
        / f"full_states_log_{trade_date}.json"
    )


def _artifact_name(path: Path) -> str:
    """A stable artifact name for a saved report file."""
    stem = path.stem if path.suffix else path.name
    return f"saved_{stem}"


@dataclass(frozen=True)
class RunContext:
    """The directory reserved for one run, before the graph starts."""

    run_id: str
    run_dir: Path


@dataclass(frozen=True)
class ManifestWriteResult:
    """What happened to this run's manifest: written, or not, and why."""

    success: bool
    manifest_path: Path | None
    artifacts: list[dict]
    error: BaseException | None


def _reserve_run_directory(results_dir, ticker: str, trade_date: str) -> RunContext:
    """Reserve a fresh directory for this run, at most three attempts.

    The directory is created with ``exist_ok=False`` so two runs of the same
    ticker and date never share one. When all three attempts collide the caller
    is told loudly and the run stops before the graph starts; nothing existing is
    touched.
    """
    base = Path(results_dir) / safe_ticker_component(ticker) / trade_date / "runs"
    base.mkdir(parents=True, exist_ok=True)
    for _attempt in range(3):
        run_id = uuid.uuid4().hex
        run_dir = base / run_id
        try:
            run_dir.mkdir(exist_ok=False)
        except FileExistsError:
            continue
        return RunContext(run_id=run_id, run_dir=run_dir)
    raise RunDirectoryUnavailable(
        f"could not reserve a run directory for {ticker} on {trade_date} "
        f"after 3 attempts under {base}"
    )


def _artifact_references(
    artifact_files,
    *,
    results_dir,
    run_dir,
) -> list[dict]:
    """Phase 1 references for the files this run wrote, relative to ``results_dir``.

    ``results_dir`` decides containment: a path that resolves outside it is
    rejected by the writer rather than silently trimmed. ``run_dir`` only
    decides the stability label, so a file inside this run's own directory is
    ``run_unique`` and everything else is ``shared_mutable``.
    """
    results_root = Path(results_dir).resolve()
    run_root = Path(run_dir).resolve()
    references = []
    for path, name in artifact_files:
        candidate = Path(path).resolve()
        try:
            candidate.relative_to(results_root)
        except ValueError:
            # A separately chosen save path outside the results root keeps its
            # files on disk but is not referenced from the manifest.
            continue
        try:
            candidate.relative_to(run_root)
            stability = "run_unique"
        except ValueError:
            stability = "shared_mutable"
        references.append(
            manifest_module.make_artifact_reference(
                name, candidate, stability, base=results_root
            )
        )
    return references


def _expected_report_files(final_state: dict, save_path: Path, html: bool) -> list[Path]:
    """The files a successful ``write_report_tree`` writes for this run.

    Computed before the write from the writer's own section selection, so a stale
    file left in the directory is never mistaken for one this run produced.
    """
    expected = []
    for _heading, folder, written in report_parts(final_state):
        for _agent, filename, _value in written:
            expected.append(save_path / folder / filename)
    expected.append(save_path / "complete_report.md")
    if html:
        expected.append(save_path / "complete_report.html")
    return expected


def _finalize_run_manifest(
    run_context: RunContext,
    *,
    config: dict,
    artifacts,
) -> ManifestWriteResult:
    """Write this run's manifest once, and report what happened to it.

    ``artifacts`` are Phase 1 artifact references built by the caller with
    ``_artifact_references``. A failure here never disturbs the analysis: the
    result and its rating are already on screen and on disk. The manifest is
    written atomically, so a failure leaves no half file.
    """
    try:
        manifest = manifest_module.build_manifest(
            ticker=config["ticker"],
            asset_type=config["asset_type"],
            analysis_date=config["analysis_date"],
            analysts=config["analysts"],
            config=config,
            artifacts=artifacts,
        )
        path = manifest_module.write_manifest(run_context.run_dir / "manifest.json", manifest)
    except Exception as exc:  # noqa: BLE001 - reported, never raised into the run
        console.print(
            "[yellow]Manifest not saved: this run's provenance record is "
            f"unavailable ({exc}).[/yellow]"
        )
        return ManifestWriteResult(
            success=False, manifest_path=None, artifacts=list(artifacts), error=exc
        )
    return ManifestWriteResult(
        success=True, manifest_path=path, artifacts=list(artifacts), error=None
    )


def _announce_checkpoint_state(graph, ticker: str, trade_date: str) -> None:
    """Say whether this run resumed a saved one, where the user can see it.

    The graph logs this, but nothing in the CLI configures logging and the live
    view owns the screen, so a resume was invisible.
    """
    if getattr(graph, "_resuming", False):
        message_buffer.add_message(
            "System", f"Resuming the saved run for {ticker} on {trade_date}"
        )
    else:
        message_buffer.add_message("System", f"Starting fresh for {ticker} on {trade_date}")


def _build_run_config(selections: dict, checkpoint: bool | None) -> dict:
    """Assemble the run config from interactive selections, honoring env precedence.

    Round counts and checkpoint follow "explicit env/flag wins": an env-applied
    value on DEFAULT_CONFIG is preserved unless the user overrode it on the CLI.
    """
    config = DEFAULT_CONFIG.copy()
    # Research depth sets both round counts, but an explicit env override
    # (TRADINGAGENTS_MAX_DEBATE_ROUNDS / _MAX_RISK_ROUNDS) wins over the
    # interactive selection — leave the env-applied value in place (#977).
    rounds = (("TRADINGAGENTS_MAX_DEBATE_ROUNDS", "max_debate_rounds"),
              ("TRADINGAGENTS_MAX_RISK_ROUNDS", "max_risk_discuss_rounds"))
    depth_was_asked = not depth_from_env()
    for env_var, key in rounds:
        if not os.environ.get(env_var):
            config[key] = selections["research_depth"]
        elif depth_was_asked:
            # The depth question appeared (it is skipped only when both are
            # set), so say which half of the answer the environment overrode.
            console.print(
                f"[green]✓ {key} from environment:[/green] {config[key]} "
                f"(set by {env_var}, so the research depth you chose does not apply to it)"
            )
    config["quick_think_llm"] = selections["quick_think_llm"]
    config["deep_think_llm"] = selections["deep_think_llm"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = selections["llm_provider"].lower()
    # Provider-specific thinking configuration. Only the main provider's is
    # asked; a tier on another provider keeps its configured value (#1440).
    for key in ("google_thinking_level", "openai_reasoning_effort", "anthropic_effort"):
        if selections.get(key) is not None:
            config[key] = selections[key]
    config["output_language"] = selections.get("output_language", "English")
    # --checkpoint/--no-checkpoint overrides only when explicitly given; omitting
    # the flag preserves TRADINGAGENTS_CHECKPOINT_ENABLED / the default (#976).
    if checkpoint is not None:
        config["checkpoint_enabled"] = checkpoint
    return config


def run_analysis(checkpoint: bool | None = None, portfolio=None, flags=None):
    flags = flags or {}
    # With no terminal nothing can answer a prompt: name every question still
    # open before any model is called, rather than stopping at the first one.
    if not (sys.stdin and sys.stdin.isatty()):
        gaps = unattended_gaps(flags)
        if gaps:
            console.print("[red]No terminal to answer the setup questions. Set:[/red]")
            for gap in gaps:
                console.print(f"  {gap}")
            raise typer.Exit(code=1)

    selections = get_user_selections(flags)

    config = _build_run_config(selections, checkpoint)

    # Normalize analyst selection to predefined order (selection is a 'set', order is fixed)
    selected_set = {analyst.value for analyst in selections["analysts"]}
    selected_analyst_keys = [a for a in ANALYST_ORDER if a in selected_set]
    analyst_execution_plan = build_analyst_execution_plan(selected_analyst_keys)
    analyst_wall_time_tracker = AnalystWallTimeTracker(analyst_execution_plan)

    # O6: the handler learns this run's analyst keys from the plan, so a call
    # tagged with one of them is attributed to that analyst and a tagged call
    # without a usable key is counted as unattributed. It is built here, after
    # the plan exists, and registered once through the graph execution config
    # below -- the constructor registration was removed once that single path
    # was shown to carry every analyst call.
    selected_spec_keys = [spec.key for spec in analyst_execution_plan.specs]
    stats_handler = StatsCallbackHandler(selected_spec_keys)

    start_time = time.time()

    results_dir = _run_directory(config, selections["ticker"], selections["analysis_date"])
    results_dir.mkdir(parents=True, exist_ok=True)

    # O2: reserve this run's own directory before the graph is even built, so two
    # runs of the same ticker and date never share one. A failure stops the run
    # here, before any graph work, and leaves existing files untouched.
    try:
        # Pass the configured results root: the helper appends the safe ticker
        # and trade date itself, then the run directory beneath them. Passing an
        # already-suffixed directory would nest ticker/date twice.
        run_context = _reserve_run_directory(config["results_dir"], selections["ticker"], selections["analysis_date"])
    except RunDirectoryUnavailable as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    # O5 S5: the reserved run directory is the destination for this run's
    # O5 evidence. The scope opens after the reservation succeeded and
    # before the graph exists, so a construction failure, a stream failure
    # or an interrupt all leave through the same cleanup. It also covers
    # the report offer and the manifest write at the end of this function.
    with o5_evidence_run(run_context.run_dir):
        graph = TradingAgentsGraph(
            selected_analyst_keys,
            config=config,
            debug=True,
        )

        message_buffer.init_for_analysis(selected_analyst_keys)

        report_dir = results_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        log_file = results_dir / "message_tool.log"
        log_file.touch(exist_ok=True)

        # Files this run actually wrote. Each entry is (path, artifact name); an
        # entry is added only after the write that produced it succeeded.
        produced_files: list[tuple[Path, str]] = []
        state_log_written = False

        def _register(path: Path, name: str) -> None:
            produced_files.append((Path(path), name))

        # The message/tool log gets one entry for the whole file, once any write
        # has landed; registering per write would repeat the same path.
        log_registered = False

        def _note_log_write() -> None:
            nonlocal log_registered
            if not log_registered:
                _register(log_file, "message_tool_log")
                log_registered = True

        def save_message_decorator(obj, func_name):
            func = getattr(obj, func_name)

            @wraps(func)
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                timestamp, message_type, content = obj.messages[-1]
                content = content.replace("\n", " ")  # Replace newlines with spaces
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} [{message_type}] {content}\n")
                _note_log_write()
            return wrapper

        def save_tool_call_decorator(obj, func_name):
            func = getattr(obj, func_name)

            @wraps(func)
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                timestamp, tool_name, args = obj.tool_calls[-1]
                args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} [Tool Call] {tool_name}({args_str})\n")
                _note_log_write()
            return wrapper

        # Section files this run wrote, by name; one registry entry each even when
        # a section is rewritten as the run progresses.
        section_files: dict[str, Path] = {}

        def save_report_section_decorator(obj, func_name):
            func = getattr(obj, func_name)

            @wraps(func)
            def wrapper(section_name, content):
                func(section_name, content)
                if section_name in obj.report_sections and obj.report_sections[section_name] is not None:
                    content = obj.report_sections[section_name]
                    if content:
                        file_name = f"{section_name}.md"
                        text = "\n".join(str(item) for item in content) if isinstance(content, list) else content
                        target = report_dir / file_name
                        with open(target, "w", encoding="utf-8") as f:
                            f.write(text)
                        section_files[section_name] = target
            return wrapper

        message_buffer.add_message = save_message_decorator(message_buffer, "add_message")
        message_buffer.add_tool_call = save_tool_call_decorator(message_buffer, "add_tool_call")
        message_buffer.update_report_section = save_report_section_decorator(message_buffer, "update_report_section")

        layout = create_layout()

        # The alternate screen keeps a layout taller than the window from redrawing
        # by scrolling; the final report prints after this block, on the normal screen.
        with Live(layout, refresh_per_second=4, screen=True):
            # Initial display
            update_display(layout, stats_handler=stats_handler, start_time=start_time)

            message_buffer.add_message("System", f"Selected ticker: {selections['ticker']}")
            if selections["asset_type"] != "stock":
                message_buffer.add_message("System", f"Detected asset type: {selections['asset_type']}")
            message_buffer.add_message(
                "System", f"Analysis date: {selections['analysis_date']}"
            )
            message_buffer.add_message(
                "System",
                f"Selected analysts: {', '.join(analyst.value for analyst in selections['analysts'])}",
            )
            update_display(layout, stats_handler=stats_handler, start_time=start_time)

            # The analysts start together.
            for spec in analyst_execution_plan.specs:
                message_buffer.update_agent_status(spec.agent_node, "in_progress")
                analyst_wall_time_tracker.mark_started(spec.key)
            update_display(layout, stats_handler=stats_handler, start_time=start_time)

            spinner_text = (
                f"Analyzing {selections['ticker']} on {selections['analysis_date']}..."
            )
            update_display(layout, spinner_text, stats_handler=stats_handler, start_time=start_time)

            # The same initial state propagate() builds, with the resolved
            # instrument identity; the graph's Memory Log step settles past
            # decisions and loads their lessons alongside the analysts.
            init_agent_state = graph.create_run_state(
                selections["ticker"], selections["analysis_date"], selections["asset_type"], portfolio
            )
            # Pass callbacks to graph config for tool execution tracking
            # (LLM tracking is handled separately via LLM constructor)
            args = graph.propagator.get_graph_args(callbacks=[stats_handler])

            # Recompile with a checkpointer and inject the thread_id so --checkpoint
            # actually saves and resumes on the CLI path (#1249); a no-op when
            # checkpointing is disabled. Torn down in the finally below.
            checkpoint_tid = graph.begin_checkpoint(
                selections["ticker"], selections["analysis_date"], selections["asset_type"], portfolio
            )
            if checkpoint_tid is not None:
                args.setdefault("config", {}).setdefault("configurable", {})["thread_id"] = checkpoint_tid
                _announce_checkpoint_state(graph, selections["ticker"], selections["analysis_date"])

            # Stream the analysis. On resume, feed None so LangGraph continues the
            # interrupted run instead of re-appending the initial state (#1249); the
            # try/finally tears the checkpointer down even if the stream raises.
            trace = []
            # O4: the Portfolio Manager's decision text, held back until the Gate has
            # judged it. Remains empty when the run never produced one.
            pm_decision_text = ""
            # O4: the PM's streamed message, held back for the same reason, so the
            # message area shows no approved recommendation before the Gate.
            pm_decision_message = None
            try:
                for messages, chunk in graph.stream_run(graph.checkpoint_input(init_agent_state), **args):
                    for message in messages:
                        msg_id = getattr(message, "id", None)
                        if msg_id is not None:
                            if msg_id in message_buffer._processed_message_ids:
                                continue
                            message_buffer._processed_message_ids.add(msg_id)

                        msg_type, content = classify_message_type(message)
                        if content and content.strip():
                            # O4: the Portfolio Manager's own message is held back
                            # with its decision, so the pre-Gate view cannot show an
                            # approved recommendation. Everything else streams as before.
                            if _is_pm_message(message):
                                pm_decision_message = (msg_type, content)
                            else:
                                message_buffer.add_message(msg_type, content)

                        if hasattr(message, "tool_calls") and message.tool_calls:
                            for tool_call in message.tool_calls:
                                if isinstance(tool_call, dict):
                                    message_buffer.add_tool_call(tool_call["name"], tool_call["args"])
                                else:
                                    message_buffer.add_tool_call(tool_call.name, tool_call.args)

                    if chunk is None:   # a step inside an analyst's graph: messages only
                        update_display(layout, stats_handler=stats_handler, start_time=start_time)
                        continue

                    update_analyst_statuses(
                        message_buffer,
                        chunk,
                        wall_time_tracker=analyst_wall_time_tracker,
                    )

                    # Research Team - Handle Investment Debate State
                    if chunk.get("investment_debate_state"):
                        debate_state = chunk["investment_debate_state"]
                        bull_hist = debate_state.get("bull_history", "").strip()
                        bear_hist = debate_state.get("bear_history", "").strip()
                        judge = (chunk.get("investment_plan") or "").strip()

                        # Only update status when there's actual content
                        if bull_hist or bear_hist:
                            update_research_team_status("in_progress")
                        if bull_hist:
                            message_buffer.update_report_section(
                                "investment_plan", f"### Bull Researcher Analysis\n{bull_hist}"
                            )
                        if bear_hist:
                            message_buffer.update_report_section(
                                "investment_plan", f"### Bear Researcher Analysis\n{bear_hist}"
                            )
                        if judge:
                            message_buffer.update_report_section(
                                "investment_plan", f"### Research Manager Decision\n{judge}"
                            )
                            update_research_team_status("completed")
                            message_buffer.update_agent_status("Trader", "in_progress")

                    # Trading Team
                    if chunk.get("trader_investment_plan"):
                        message_buffer.update_report_section(
                            "trader_investment_plan", chunk["trader_investment_plan"]
                        )
                        if message_buffer.agent_status.get("Trader") != "completed":
                            message_buffer.update_agent_status("Trader", "completed")
                            message_buffer.update_agent_status("Aggressive Analyst", "in_progress")

                    # Risk Management Team - Handle Risk Debate State
                    if chunk.get("risk_debate_state"):
                        risk_state = chunk["risk_debate_state"]
                        agg_hist = risk_state.get("aggressive_history", "").strip()
                        con_hist = risk_state.get("conservative_history", "").strip()
                        neu_hist = risk_state.get("neutral_history", "").strip()
                        judge = (chunk.get("final_trade_decision") or "").strip()

                        if agg_hist:
                            if message_buffer.agent_status.get("Aggressive Analyst") != "completed":
                                message_buffer.update_agent_status("Aggressive Analyst", "in_progress")
                            message_buffer.update_report_section(
                                "final_trade_decision", f"### Aggressive Analyst Analysis\n{agg_hist}"
                            )
                        if con_hist:
                            if message_buffer.agent_status.get("Conservative Analyst") != "completed":
                                message_buffer.update_agent_status("Conservative Analyst", "in_progress")
                            message_buffer.update_report_section(
                                "final_trade_decision", f"### Conservative Analyst Analysis\n{con_hist}"
                            )
                        if neu_hist:
                            if message_buffer.agent_status.get("Neutral Analyst") != "completed":
                                message_buffer.update_agent_status("Neutral Analyst", "in_progress")
                            message_buffer.update_report_section(
                                "final_trade_decision", f"### Neutral Analyst Analysis\n{neu_hist}"
                            )
                        if judge and message_buffer.agent_status.get("Portfolio Manager") != "completed":
                            message_buffer.update_agent_status("Portfolio Manager", "in_progress")
                            # O4: hold the PM decision back until the Gate has judged
                            # it, so no approved Buy/Sell is published before then.
                            # Only the status marker goes to the live section now.
                            pm_decision_text = judge
                            message_buffer.update_report_section(
                                "final_trade_decision", "### Portfolio Manager Decision\n"
                            )
                            message_buffer.update_agent_status("Aggressive Analyst", "completed")
                            message_buffer.update_agent_status("Conservative Analyst", "completed")
                            message_buffer.update_agent_status("Neutral Analyst", "completed")
                            message_buffer.update_agent_status("Portfolio Manager", "completed")

                    update_display(layout, stats_handler=stats_handler, start_time=start_time)

                    trace.append(chunk)

                # Streamed chunks are per-node deltas, not full state. Merge them
                # so every report field populated across the run is present.
                final_state = {}
                for chunk in trace:
                    final_state.update(chunk)

                # Clean run: log the decision, then drop this run's checkpoint so a
                # later run starts fresh. A mid-stream failure skips both, keeping
                # the checkpoint for resume.
                graph.record_decision(selections["ticker"], selections["analysis_date"], final_state)
                # Only a normal return proves this run's state log was written and
                # closed; a raise propagates out of the try before this line.
                state_log_written = True
                # O4: the Gate has judged the run, so the buffered decision may be
                # published now. A REVIEW is labelled as unapproved original content
                # rather than presented as the run's recommendation.
                if pm_decision_text:
                    if is_review(run_rating(final_state)):
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            "### Portfolio Manager Decision (unapproved original content; "
                            f"withheld from the run's rating)\n{pm_decision_text}",
                        )
                    else:
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Portfolio Manager Decision\n{pm_decision_text}",
                        )
                # O4: the held-back PM message is released only now, after the Gate,
                # and carries the same non-authoritative label on REVIEW.
                if pm_decision_message is not None:
                    msg_type, content = pm_decision_message
                    if is_review(run_rating(final_state)):
                        message_buffer.add_message(
                            msg_type,
                            "(unapproved original content; withheld from the run's "
                            f"rating)\n{content}",
                        )
                    else:
                        message_buffer.add_message(msg_type, content)
                graph.clear_checkpoint_on_success(
                    selections["ticker"], selections["analysis_date"], selections["asset_type"], portfolio
                )
            finally:
                # Always restore the plain uncheckpointed graph, even on failure.
                graph.end_checkpoint()

            for agent in message_buffer.agent_status:
                message_buffer.update_agent_status(agent, "completed")

            message_buffer.add_message(
                "System", f"Completed analysis for {selections['analysis_date']}"
            )
            message_buffer.add_message("System", analyst_wall_time_tracker.format_summary())

            for section in message_buffer.report_sections:
                if section in final_state:
                    message_buffer.update_report_section(section, final_state[section])

            update_display(layout, stats_handler=stats_handler, start_time=start_time)

        # Post-analysis prompts (outside Live context for clean interaction)
        console.print("\n[bold cyan]Analysis Complete![/bold cyan]\n")

        # A decision nobody can read is not a position. Say so here rather than
        # leaving the run to look like a normal result.
        if is_review(run_rating(final_state)):
            console.print(
                "[yellow]No rating could be read from the final decision, so this run "
                "is recorded for review rather than as a position. Re-run, or read the "
                "decision text below and judge it yourself.[/yellow]\n"
            )
        console.print(f"[dim]{analyst_wall_time_tracker.format_summary()}[/dim]")

        # O6: per-analyst usage. Placed after the completion notice, the conditional
        # REVIEW notice and the elapsed-time line, and before the report options
        # below; this is the current placement, not yet a formally approved order.
        # The live footer is three lines and cannot hold per-analyst rows.
        display_agent_summary(stats_handler)

        saved_reports = _offer_reports(final_state, graph, selections["ticker"],
                                       save=flags.get("save"), show=flags.get("show"), html=flags.get("html"))

        # O2: one manifest for this run, after the save choice has been handled.
        # Only files whose own write succeeded are recorded. A caller that replaces
        # _offer_reports and returns nothing contributes no saved reports.
        for path in saved_reports or ():
            _register(path, _artifact_name(path))
        for section, path in section_files.items():
            _register(path, f"live_{section}")
        # The state log counts only if record_decision() returned without raising;
        # the flag is set at that call, not inferred from the file being present.
        if state_log_written:
            _register(_state_log_path(config, selections["ticker"], selections["analysis_date"]), "state_log")

        manifest_config = {
            **config,
            "ticker": selections["ticker"],
            "asset_type": selections["asset_type"],
            "analysis_date": selections["analysis_date"],
            "analysts": [analyst.value for analyst in selections["analysts"]],
        }
        references = _artifact_references(
            produced_files,
            results_dir=config["results_dir"],
            run_dir=run_context.run_dir,
        )
        result = _finalize_run_manifest(run_context, config=manifest_config, artifacts=references)
        if result.success and result.manifest_path is not None:
            # Say where the manifest went, so a run's provenance record is findable
            # without inspecting the run directory afterwards.
            console.print(f"\n[green]✓ Manifest written to:[/green] {result.manifest_path}")
        else:
            # The warning names the failure; make clear the analysis itself stands.
            console.print(
                "[yellow]The analysis result above stands; only its provenance "
                "record is missing.[/yellow]"
            )


def _yes(question: str) -> bool:
    return typer.prompt(question, default="Y").strip().upper() in ("Y", "YES", "")


def _graphical_browser():
    """A browser that opens a page in its own window on this machine, or None.

    Over SSH the page sits on the remote machine, and a terminal browser (lynx,
    w3m, elinks) would take over the terminal, so neither is offered.
    """
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"):
        return None
    try:
        browser = webbrowser.get()
    except webbrowser.Error:
        return None
    if type(browser) is webbrowser.GenericBrowser or isinstance(browser, webbrowser.Elinks):
        return None
    return browser


def _open_page(page: Path) -> None:
    """Offer to open the saved page in a browser window, and say where it is if opening fails."""
    browser = _graphical_browser()
    if browser is None or not _yes("Open it in your browser?"):
        return
    try:
        opened = browser.open(page.as_uri())
    except (webbrowser.Error, OSError):
        opened = False
    if not opened:
        console.print(f"  [dim]Could not open a browser; the page is at:[/dim] {page}")


def _offer_reports(final_state, graph, ticker, save=None, show=None, html=None):
    """Save the report tree and show it; ``save``/``show``/``html`` answer the questions when given.

    A saved report includes the HTML page unless ``html`` is False. Someone
    answering the save question at the prompt is also asked about the page and
    offered to open it; a run whose flags answer the save question asks neither.

    Returns the files this call actually wrote, so the caller never has to guess
    from what happens to be on disk. A declined save, or one that fails partway,
    returns nothing: a half-written tree is not a saved report.
    """
    written: list[Path] = []
    asked = save is None
    if asked:
        save = typer.prompt("Save report?", default="Y").strip().upper() in ("Y", "YES", "")
    if save:
        # Under results_dir, not the working directory: in Docker the working
        # directory is inside the container and the report goes with it, while
        # results_dir is the mounted volume the rest of the run already writes to.
        save_path = graph.default_report_path(ticker)
        if asked:   # someone at the prompt may pick another folder
            save_path = Path(typer.prompt(
                "Save path (press Enter for default)", default=str(save_path)
            ).strip())
        if html is None:
            html = _yes("Also save it as an HTML page?") if asked else True
        # The files the writer will produce, decided before it runs: save_reports
        # returns only the complete report, so this is what makes the inventory
        # exact without scanning the directory afterwards.
        expected = _expected_report_files(final_state, Path(save_path), html)
        saved = False
        try:
            report_file = graph.save_reports(final_state, ticker, save_path, html=html)
            saved = True
            console.print(f"\n[green]✓ Report saved to:[/green] {save_path.resolve()}")
            console.print(f"  [dim]Complete report:[/dim] {report_file.name}")
        except Exception as e:
            console.print(f"[red]Error saving report: {e}[/red]")
        if saved:
            written = expected
        if saved and html:
            page = (save_path / "complete_report.html").resolve()
            console.print(f"  [dim]HTML report:[/dim] {page.name}")
            if asked:
                _open_page(page)

    if show is None:
        show = typer.prompt("\nDisplay full report on screen?", default="Y").strip().upper() in ("Y", "YES", "")
    if show:
        display_complete_report(final_state)
    return written
