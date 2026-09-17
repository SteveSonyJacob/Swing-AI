"""Unit tests for trend and market structure analysis."""

import pytest
import pandas as pd
import numpy as np
from src.indicators.moving_averages import add_moving_averages
from src.analysis.daily_analysis import analyze_daily_trend, determine_market_structure
from src.analysis.trend_analysis import evaluate_trend_confirmation


def test_bullish_daily_trend():
    # Construct a strong ascending price trend
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    prices = np.linspace(100, 300, 250)
    df = pd.DataFrame({
        "open": prices,
        "high": prices + 2,
        "low": prices - 2,
        "close": prices + 1,
        "volume": np.full(250, 100000)
    }, index=dates)

    df = add_moving_averages(df, 20, 50, 200)
    trend_result = analyze_daily_trend(df)

    assert trend_result["trend"] == "bullish"
    assert trend_result["ema_alignment"] == True
    assert trend_result["ema20_slope"] > 0


def test_bearish_daily_trend():
    # Construct a strong descending price trend
    dates = pd.date_range("2024-01-01", periods=250, freq="B")
    prices = np.linspace(300, 100, 250)
    df = pd.DataFrame({
        "open": prices,
        "high": prices + 2,
        "low": prices - 2,
        "close": prices - 1,
        "volume": np.full(250, 100000)
    }, index=dates)

    df = add_moving_averages(df, 20, 50, 200)
    trend_result = analyze_daily_trend(df)

    assert trend_result["trend"] == "bearish"
    assert trend_result["ema_alignment"] == False
    assert trend_result["ema20_slope"] < 0


def test_trend_confirmation():
    conf1 = evaluate_trend_confirmation("bullish", "bullish")
    assert conf1["aligned"] == True
    assert conf1["confirmation_status"] == "bullish_confirmation"

    conf2 = evaluate_trend_confirmation("bullish", "bearish")
    assert conf2["aligned"] == False
    assert conf2["confirmation_status"] == "short_term_pullback"
