"""Unit tests for breakout detection and look-ahead bias prevention."""

import pytest
import pandas as pd
import numpy as np
from src.analysis.breakout import detect_breakouts


def test_breakout_detection_no_lookahead():
    # 30 days of consolidation at 100 with high of 105
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    highs = np.full(30, 105.0)
    lows = np.full(30, 95.0)
    closes = np.full(30, 100.0)
    rvols = np.full(30, 1.0)

    # Day 30: price breaks out to 110 with 2.0 RVOL
    closes[-1] = 110.0
    highs[-1] = 112.0
    rvols[-1] = 2.0

    df = pd.DataFrame({
        "open": closes,
        "high": highs,
        "low": lows,
        "close": closes,
        "rvol": rvols
    }, index=dates)

    res = detect_breakouts(df, short_window=20, long_window=50, volume_threshold=1.5)

    assert res["detected"] == True
    assert res["type"] == "20_day_high"
    assert res["volume_confirmed"] == True
    assert res["prior_20d_high"] == 105.0  # prior high must not be today's high (112.0)


def test_no_breakout_when_below_prior_high():
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    highs = np.full(30, 105.0)
    # Give a peak at day 10 of 115
    highs[10] = 115.0
    closes = np.full(30, 100.0)

    # Day 30 close is 108 (higher than base, but below peak of 115)
    closes[-1] = 108.0

    df = pd.DataFrame({
        "open": closes,
        "high": highs,
        "low": closes - 5,
        "close": closes,
        "rvol": np.full(30, 1.0)
    }, index=dates)

    res = detect_breakouts(df, short_window=20, long_window=50)
    assert res["detected"] == False
    assert res["type"] == "none"
    assert res["prior_20d_high"] == 115.0
