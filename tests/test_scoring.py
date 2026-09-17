"""Unit tests for the scoring engine."""

import pytest
from src.scoring.technical_score import (
    compute_technical_score,
    calculate_daily_trend_score,
    calculate_hourly_trend_score,
    calculate_momentum_score,
    calculate_volume_score,
    calculate_breakout_score,
    calculate_support_resistance_score,
    calculate_relative_strength_score,
    calculate_volatility_score,
    categorize_score
)


def test_score_breakdown_sum():
    daily_analysis = {
        "close": 1500,
        "ema20": 1450,
        "ema50": 1400,
        "ema200": 1300,
        "ema20_slope": 0.015,
        "ema50_slope": 0.008,
        "market_structure": "higher_highs_higher_lows"
    }
    hourly_analysis = {
        "close": 1500,
        "ema20": 1490,
        "ema50": 1480,
        "ema20_slope": 0.005,
        "market_structure": "higher_highs_higher_lows"
    }
    momentum_data = {
        "rsi": 64.5,
        "macd_line": 15.0,
        "macd_signal": 12.0,
        "macd_histogram": 3.0,
        "macd_bullish_crossover": True
    }
    volume_data = {
        "rvol": 2.1,
        "volume_expansion": True,
        "price_volume_confirmation": True
    }
    breakout_data = {
        "detected": True,
        "type": "50_day_high",
        "volume_confirmed": True
    }
    sr_levels = {
        "support": 1420.0,
        "resistance": 1600.0
    }
    rs_data = {
        "vs_nifty_1m": 8.5,
        "vs_sector_1m": 4.2
    }
    atr_percent = 2.1

    result = compute_technical_score(
        daily_analysis=daily_analysis,
        hourly_analysis=hourly_analysis,
        momentum_data=momentum_data,
        volume_data=volume_data,
        breakout_data=breakout_data,
        sr_levels=sr_levels,
        rs_data=rs_data,
        atr_percent=atr_percent
    )

    score = result["technical_score"]
    breakdown = result["score_breakdown"]

    assert sum(breakdown.values()) == score
    assert 0 <= score <= 100
    assert result["category"] in ["strong", "very_strong"]


def test_score_categorization():
    assert categorize_score(25) == "weak"
    assert categorize_score(45) == "neutral"
    assert categorize_score(65) == "positive"
    assert categorize_score(80) == "strong"
    assert categorize_score(92) == "very_strong"


def test_zero_baseline_score():
    result = compute_technical_score(
        daily_analysis={},
        hourly_analysis={},
        momentum_data={"rsi": 20.0, "macd_line": -5, "macd_signal": 0, "macd_histogram": -5},
        volume_data={"rvol": 0.3},
        breakout_data={"detected": False, "type": "none"},
        sr_levels={},
        rs_data={},
        atr_percent=0.1
    )
    assert result["technical_score"] < 20
    assert result["category"] == "weak"
