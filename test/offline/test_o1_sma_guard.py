"""O1 SMA validity guard: T-O1-01 through T-O1-12.

The 50- and 200-session SMAs are reported as a number only when enough usable,
non-missing dated closes exist through the reported date. Otherwise the result
is the exact insufficient-history text. Duplicate trading dates are rejected
with the exact invalid-history text. These cases are deterministic and offline:
the Yahoo loader is either mocked or driven against a seeded local cache.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import stockstats

from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.vendors.yahoo import market, ohlcv, snapshot

INSUFFICIENT = "N/A: insufficient history (needs {w} sessions, have {n})"
DUPLICATE = "N/A: invalid price history (duplicate trading date)"
HOLIDAY = "N/A: Not a trading day (weekend or holiday)"

W50 = 50
W200 = 200


def _frame(n, *, shuffle=False, start="2025-01-01"):
    """n dated rows with non-constant closes; the last close is unique."""
    dates = pd.bdate_range(start, periods=n)
    closes = [100.0 + i * 0.5 for i in range(n)]
    frame = pd.DataFrame(
        {
            "Date": dates,
            "Open": closes,
            "High": [c + 1.0 for c in closes],
            "Low": [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1_000_000 + i for i in range(n)],
        }
    )
    if shuffle:
        # A genuine permutation: every date appears exactly once, out of order.
        rng = np.random.default_rng(20261116)
        order = rng.permutation(n)
        frame = frame.iloc[order].reset_index(drop=True)
    return frame


def _mean(closes, w):
    return sum(closes[-w:]) / w


def _mean_through(frame, date, w):
    upto = frame[frame["Date"] <= pd.Timestamp(date)]["Close"].tolist()
    return _mean(upto, w)


def _mock_loader(monkeypatch, frame, module=market):
    monkeypatch.setattr(module, "load_ohlcv", lambda s, d, fill_gaps=True: frame.copy())


def _date(frame, idx):
    return pd.Timestamp(frame["Date"].iloc[idx]).strftime("%Y-%m-%d")


# --- T-O1-01 / -02 / -03: bulk boundaries ----------------------------------


@pytest.mark.unit
def test_t_o1_01_bulk_40_and_49(monkeypatch):
    f40 = _frame(40)
    _mock_loader(monkeypatch, f40)
    d = _date(f40, -1)
    assert market._get_stock_stats_bulk("X", "close_50_sma", d)[d] == INSUFFICIENT.format(w=50, n=40)
    assert market._get_stock_stats_bulk("X", "close_200_sma", d)[d] == INSUFFICIENT.format(w=200, n=40)

    f49 = _frame(49)
    _mock_loader(monkeypatch, f49)
    d = _date(f49, -1)
    out = market._get_stock_stats_bulk("X", "close_50_sma", d)[d]
    assert out == INSUFFICIENT.format(w=50, n=49)
    assert not out.replace("N/A", "").strip().replace(":", "").strip().split()[0].replace(".", "").isdigit()


@pytest.mark.unit
def test_t_o1_02_bulk_50_and_60(monkeypatch):
    f50 = _frame(50)
    _mock_loader(monkeypatch, f50)
    d = _date(f50, -1)
    v = float(market._get_stock_stats_bulk("X", "close_50_sma", d)[d])
    assert abs(v - _mean_through(f50, d, 50)) <= 1e-6
    assert market._get_stock_stats_bulk("X", "close_200_sma", d)[d] == INSUFFICIENT.format(w=200, n=50)

    f60 = _frame(60)
    _mock_loader(monkeypatch, f60)
    d = _date(f60, -1)
    v = float(market._get_stock_stats_bulk("X", "close_50_sma", d)[d])
    assert abs(v - _mean_through(f60, d, 50)) <= 1e-6
    assert market._get_stock_stats_bulk("X", "close_200_sma", d)[d] == INSUFFICIENT.format(w=200, n=60)


@pytest.mark.unit
def test_t_o1_03_bulk_199_200_220(monkeypatch):
    f199 = _frame(199)
    _mock_loader(monkeypatch, f199)
    d = _date(f199, -1)
    assert market._get_stock_stats_bulk("X", "close_200_sma", d)[d] == INSUFFICIENT.format(w=200, n=199)

    for n in (200, 220):
        frame = _frame(n)
        _mock_loader(monkeypatch, frame)
        d = _date(frame, -1)
        v50 = float(market._get_stock_stats_bulk("X", "close_50_sma", d)[d])
        v200 = float(market._get_stock_stats_bulk("X", "close_200_sma", d)[d])
        assert abs(v50 - _mean_through(frame, d, 50)) <= 1e-6
        assert abs(v200 - _mean_through(frame, d, 200)) <= 1e-6


# --- T-O1-04: early date in a long frame -----------------------------------


@pytest.mark.unit
def test_t_o1_04_early_date_uses_its_own_history(monkeypatch):
    frame = _frame(260)
    _mock_loader(monkeypatch, frame)
    target = _date(frame, 59)  # the 60th chronological session
    bulk50 = market._get_stock_stats_bulk("X", "close_50_sma", _date(frame, -1))
    bulk200 = market._get_stock_stats_bulk("X", "close_200_sma", _date(frame, -1))
    v50 = float(bulk50[target])
    assert abs(v50 - _mean_through(frame, target, 50)) <= 1e-6
    assert bulk200[target] == INSUFFICIENT.format(w=200, n=60)


# --- T-O1-05: verified snapshot -------------------------------------------


def _snapshot_cell(text, name):
    for line in text.splitlines():
        if line.strip().startswith(f"| {name} |"):
            return line.split("|")[2].strip()
    raise AssertionError(f"{name} row not found")


@pytest.mark.unit
def test_t_o1_05_snapshot_boundaries(monkeypatch):
    f40 = _frame(40)
    _mock_loader(monkeypatch, f40, module=snapshot)
    d = _date(f40, -1)
    snap = snapshot.build_verified_market_snapshot("X", d)
    assert _snapshot_cell(snap, "close_50_sma") == INSUFFICIENT.format(w=50, n=40)
    assert _snapshot_cell(snap, "close_200_sma") == INSUFFICIENT.format(w=200, n=40)

    f49 = _frame(49)
    _mock_loader(monkeypatch, f49, module=snapshot)
    d = _date(f49, -1)
    snap = snapshot.build_verified_market_snapshot("X", d)
    assert _snapshot_cell(snap, "close_50_sma") == INSUFFICIENT.format(w=50, n=49)

    f50 = _frame(50)
    _mock_loader(monkeypatch, f50, module=snapshot)
    d = _date(f50, -1)
    snap = snapshot.build_verified_market_snapshot("X", d)
    assert _snapshot_cell(snap, "close_50_sma") == snapshot.price_text(_mean_through(f50, d, 50))
    assert _snapshot_cell(snap, "close_200_sma") == INSUFFICIENT.format(w=200, n=50)

    f199 = _frame(199)
    _mock_loader(monkeypatch, f199, module=snapshot)
    d = _date(f199, -1)
    snap = snapshot.build_verified_market_snapshot("X", d)
    assert _snapshot_cell(snap, "close_50_sma") == snapshot.price_text(_mean_through(f199, d, 50))
    assert _snapshot_cell(snap, "close_200_sma") == INSUFFICIENT.format(w=200, n=199)

    f200 = _frame(200)
    _mock_loader(monkeypatch, f200, module=snapshot)
    d = _date(f200, -1)
    snap = snapshot.build_verified_market_snapshot("X", d)
    assert _snapshot_cell(snap, "close_50_sma") == snapshot.price_text(_mean_through(f200, d, 50))
    assert _snapshot_cell(snap, "close_200_sma") == snapshot.price_text(_mean_through(f200, d, 200))


# --- T-O1-06: per-day fallback --------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("n,w", [(49, 50), (50, 50), (199, 200), (200, 200)])
def test_t_o1_06_fallback_guard(monkeypatch, n, w):
    frame = _frame(n)
    d = _date(frame, -1)
    indicator = "close_50_sma" if w == 50 else "close_200_sma"

    def _boom(*a, **k):
        raise RuntimeError("bulk failed")

    spy = {"ran": False}
    real = market.get_stockstats_indicator

    def _spy(*a, **k):
        spy["ran"] = True
        return real(*a, **k)

    monkeypatch.setattr(market, "_get_stock_stats_bulk", _boom)
    monkeypatch.setattr(market, "get_stockstats_indicator", _spy)
    _mock_loader(monkeypatch, frame)

    out = market.get_stock_stats_indicators_window("X", indicator, d, 0)
    assert spy["ran"], "the per-day fallback did not run"
    line = next(ln for ln in out.splitlines() if ln.startswith(f"{d}:"))
    value = line.split(":", 1)[1].strip()
    if n < w:
        assert value == INSUFFICIENT.format(w=w, n=n)
    else:
        assert abs(float(value) - _mean_through(frame, d, w)) <= 1e-6


# --- T-O1-07: non-SMA control ---------------------------------------------


@pytest.mark.unit
def test_t_o1_07_non_sma_unchanged(monkeypatch):
    frame = _frame(60)
    _mock_loader(monkeypatch, frame)
    d = _date(frame, -1)

    stock = stockstats.wrap(frame.copy())
    stock["Date"] = stock["Date"].dt.strftime("%Y-%m-%d")
    stock["rsi"]
    expected = stock.loc[stock["Date"] == d, "rsi"].iloc[0]

    bulk = market._get_stock_stats_bulk("X", "rsi", d)[d]
    if pd.isna(expected):
        assert bulk == "N/A"
    else:
        assert abs(float(bulk) - float(expected)) <= 1e-6

    def _force_fallback(*args, **kwargs):
        raise RuntimeError("force per-day fallback")

    monkeypatch.setattr(market, "_get_stock_stats_bulk", _force_fallback)
    fallback = market.get_stock_stats_indicators_window("X", "rsi", d, 0)
    fallback_line = next(line for line in fallback.splitlines() if line.startswith(f"{d}:"))
    fallback_value = fallback_line.split(":", 1)[1].strip()
    assert abs(float(fallback_value) - float(expected)) <= 1e-6

    _mock_loader(monkeypatch, frame, module=snapshot)
    snap = snapshot.build_verified_market_snapshot("X", d)
    assert _snapshot_cell(snap, "rsi") == snapshot.price_text(float(expected))


# --- T-O1-08: insufficient vs non-trading-day -----------------------------


@pytest.mark.unit
def test_t_o1_08_distinct_messages(monkeypatch):
    frame = _frame(49)
    _mock_loader(monkeypatch, frame)
    last_trading = pd.Timestamp(frame["Date"].iloc[-1])
    # The nearest Saturday on or after the last trading date is an absent
    # calendar date (a non-trading day) within the same window.
    saturday = last_trading + pd.Timedelta(days=1)
    while saturday.weekday() != 5:
        saturday += pd.Timedelta(days=1)
    as_of = saturday.strftime("%Y-%m-%d")
    # Size the window so it spans from the last trading date through the Saturday,
    # so the output has both the short-history trading date and the absent day.
    look_back = (saturday - last_trading).days

    out = market.get_stock_stats_indicators_window("X", "close_50_sma", as_of, look_back)
    by_date = {}
    for ln in out.splitlines():
        if ":" in ln and ln[:4].isdigit():
            by_date[ln.split(":", 1)[0]] = ln.split(":", 1)[1].strip()

    # a nearby absent weekend date keeps the holiday text
    assert by_date[as_of] == HOLIDAY
    # the short-history trading date has the insufficient text, not the holiday text
    trade_key = last_trading.strftime("%Y-%m-%d")
    assert by_date[trade_key] == INSUFFICIENT.format(w=50, n=49)
    assert by_date[trade_key] != HOLIDAY


# --- T-O1-09: real loader, one missing close ------------------------------


def _stamp(path, ts):
    t = ts.to_pydatetime().timestamp()
    os.utime(path, (t, t))


def _run_load(monkeypatch, tmp_path, frame, curr_date):
    monkeypatch.setattr(ohlcv, "get_config", lambda: {"data_cache_dir": str(tmp_path)})
    today = pd.Timestamp(curr_date)
    monkeypatch.setattr(ohlcv.pd.Timestamp, "today", staticmethod(lambda: today))
    cache_file = tmp_path / "AAPL-YFin-data.csv"
    cache_file.write_text(frame.to_csv(index=False))
    _stamp(cache_file, today)

    def _fail_download(*a, **k):
        raise AssertionError("should use the seeded cache, not download")

    monkeypatch.setattr(ohlcv.yf, "Ticker", lambda symbol: SimpleNamespace(history=_fail_download))
    return ohlcv.load_ohlcv("AAPL", curr_date)


@pytest.mark.unit
@pytest.mark.parametrize("n,w", [(50, 50), (200, 200)])
def test_t_o1_09_real_loader_missing_close(monkeypatch, tmp_path, n, w):
    frame = _frame(n)
    mid = n // 2
    frame.loc[mid, "Close"] = float("nan")
    curr_date = _date(frame, -1)

    loaded = _run_load(monkeypatch, tmp_path, frame, curr_date)
    assert len(loaded) == n - 1  # the missing-close row was dropped

    monkeypatch.setattr(market, "load_ohlcv", lambda s, d, fill_gaps=True: loaded)
    indicator = "close_50_sma" if w == 50 else "close_200_sma"
    out = market._get_stock_stats_bulk("AAPL", indicator, curr_date)[curr_date]
    assert out == INSUFFICIENT.format(w=w, n=n - 1)


# --- T-O1-10: all closes missing ------------------------------------------


@pytest.mark.unit
def test_t_o1_10_all_closes_missing(monkeypatch, tmp_path):
    frame = _frame(50)
    frame["Close"] = float("nan")
    curr_date = _date(frame, -1)

    with pytest.raises(NoMarketDataError, match="no bar in range has a closing price"):
        _run_load(monkeypatch, tmp_path, frame, curr_date)

    # Routed tool: use the same cache and real loader, not an injected error.
    from tradingagents.agents.tools import get_verified_market_snapshot

    real_loader = snapshot.load_ohlcv
    calls = []

    def _spy_loader(symbol, as_of_date, fill_gaps=True):
        calls.append((symbol, as_of_date, fill_gaps))
        return real_loader(symbol, as_of_date, fill_gaps=fill_gaps)

    monkeypatch.setattr(snapshot, "load_ohlcv", _spy_loader)
    out = get_verified_market_snapshot.invoke({"symbol": "AAPL", "curr_date": curr_date})
    assert calls == [("AAPL", curr_date, False)]
    assert out.startswith("NO_DATA_AVAILABLE:")
    assert "no bar in range has a closing price" in out
    assert "sma" not in out.lower()
    assert "have 0" not in out


# --- T-O1-11: shuffled + future rows --------------------------------------


@pytest.mark.unit
def test_t_o1_11_shuffled_and_future_rows(monkeypatch):
    sorted_frame = _frame(260)
    shuffled = _frame(260, shuffle=True)
    early = _date(sorted_frame, 59)
    last = _date(sorted_frame, -1)

    _mock_loader(monkeypatch, sorted_frame)
    s50_early = market._get_stock_stats_bulk("X", "close_50_sma", early)[early]
    s200_early = market._get_stock_stats_bulk("X", "close_200_sma", early)[early]
    s50_last = market._get_stock_stats_bulk("X", "close_50_sma", last)[last]
    s200_last = market._get_stock_stats_bulk("X", "close_200_sma", last)[last]

    _mock_loader(monkeypatch, shuffled)
    f50_early = market._get_stock_stats_bulk("X", "close_50_sma", early)[early]
    f200_early = market._get_stock_stats_bulk("X", "close_200_sma", early)[early]
    f50_last = market._get_stock_stats_bulk("X", "close_50_sma", last)[last]
    f200_last = market._get_stock_stats_bulk("X", "close_200_sma", last)[last]

    assert abs(float(s50_early) - _mean_through(sorted_frame, early, 50)) <= 1e-6
    assert s200_early == INSUFFICIENT.format(w=200, n=60)
    assert abs(float(s50_last) - _mean_through(sorted_frame, last, 50)) <= 1e-6
    assert abs(float(s200_last) - _mean_through(sorted_frame, last, 200)) <= 1e-6
    # shuffled and sorted agree for each date
    assert abs(float(f50_early) - float(s50_early)) <= 1e-6
    assert f200_early == s200_early
    assert abs(float(f50_last) - float(s50_last)) <= 1e-6
    assert abs(float(f200_last) - float(s200_last)) <= 1e-6

    # An extreme price after the earlier analysis date must not affect that date.
    with_future = _frame(260)
    future_date = pd.bdate_range(pd.Timestamp(with_future["Date"].iloc[-1]) + pd.Timedelta(days=1), periods=1)[0]
    future_row = with_future.iloc[[-1]].copy()
    future_row["Date"] = future_date
    future_row["Close"] = 1.0e9
    extended = pd.concat([with_future, future_row], ignore_index=True)
    _mock_loader(monkeypatch, extended)
    x50_early = market._get_stock_stats_bulk("X", "close_50_sma", early)[early]
    assert abs(float(x50_early) - _mean_through(sorted_frame, early, 50)) <= 1e-6


# --- T-O1-12: duplicate trading date --------------------------------------


@pytest.mark.unit
def test_t_o1_12_duplicate_date_rejected(monkeypatch):
    frame = _frame(60)
    dup = frame.iloc[[30]].copy()
    dup["Close"] = dup["Close"] + 5.0
    repeated = pd.concat([frame, dup], ignore_index=True)
    _mock_loader(monkeypatch, repeated)
    d = _date(frame, -1)

    assert market._get_stock_stats_bulk("X", "close_50_sma", d)[d] == DUPLICATE
    assert market._get_stock_stats_bulk("X", "close_200_sma", d)[d] == DUPLICATE
    assert market.get_stock_stats("X", "close_50_sma", d) == DUPLICATE
    assert market.get_stock_stats("X", "close_200_sma", d) == DUPLICATE

    _mock_loader(monkeypatch, repeated, module=snapshot)
    snap = snapshot.build_verified_market_snapshot("X", d)
    assert _snapshot_cell(snap, "close_50_sma") == DUPLICATE
    assert _snapshot_cell(snap, "close_200_sma") == DUPLICATE

    # A non-SMA indicator is not rejected by the SMA duplicate rule.
    _mock_loader(monkeypatch, repeated)
    rsi = market._get_stock_stats_bulk("X", "rsi", d)[d]
    assert rsi != DUPLICATE
