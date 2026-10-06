"""Unit tests for yfinance scanner and indicators."""

import pytest
import pandas as pd
import numpy as np
from src.screening.sources.yfinance_scanner import (
    format_symbol_for_yf,
    clean_symbol,
    compute_rsi,
    compute_metrics_from_ohlcv,
    scan_yfinance_universe
)


def test_symbol_helpers():
    assert format_symbol_for_yf("RELIANCE") == "RELIANCE.NS"
    assert format_symbol_for_yf("TCS.NS") == "TCS.NS"
    assert format_symbol_for_yf("^NSEI") == "^NSEI"
    assert clean_symbol("RELIANCE.NS") == "RELIANCE"
    assert clean_symbol("TCS") == "TCS"


def test_compute_rsi_monotonic():
    # Monotonically increasing close series should have very high RSI
    up_prices = pd.Series([100.0 + i * 2.0 for i in range(30)])
    rsi_up = compute_rsi(up_prices, period=14)
    assert rsi_up > 80.0

    # Monotonically decreasing series should have very low RSI
    down_prices = pd.Series([200.0 - i * 2.0 for i in range(30)])
    rsi_down = compute_rsi(down_prices, period=14)
    assert rsi_down < 20.0


def test_compute_metrics_from_ohlcv():
    dates = pd.date_range("2026-01-01", periods=50, freq="B")
    close = [100.0 + i for i in range(50)]
    high = [c + 2.0 for c in close]
    low = [c - 2.0 for c in close]
    volume = [100000] * 49 + [250000]  # Volume spike on last candle

    df = pd.DataFrame({"close": close, "high": high, "low": low, "volume": volume}, index=dates)
    metrics = compute_metrics_from_ohlcv(df, "TEST")

    assert metrics is not None
    assert metrics["symbol"] == "TEST"
    assert metrics["current_price"] == 149.0
    assert metrics["volume_ratio"] >= 2.0
    assert "VOLUME_SHOCKER" in metrics["tags"]
    assert metrics["breakout_20d"] is True
    assert metrics["distance_52w_high_pct"] <= 3.0


def test_scan_yfinance_universe_offline():
    symbols = ["RELIANCE", "TCS", "INFY"]
    res = scan_yfinance_universe(symbols, offline=True)
    assert len(res) == 3
    found_symbols = [r["symbol"] for r in res]
    assert "RELIANCE" in found_symbols
    assert "TCS" in found_symbols
    assert all("current_price" in r for r in res)
    assert all("rsi" in r for r in res)
