"""Unit tests for screening filters."""

import pytest
from src.screening.filters.technical_filter import evaluate_technical_criteria
from src.screening.filters.volume_filter import evaluate_volume_criteria
from src.screening.filters.liquidity_filter import evaluate_liquidity_criteria
from src.screening.filters.catalyst_filter import evaluate_catalyst_criteria

THRESHOLDS = {
    "price": {"min_price": 20.0, "preferred_min_price": 100.0},
    "liquidity": {"min_avg_daily_volume": 100000, "min_turnover_cr": 5.0},
    "technical": {"rsi_min": 50.0, "rsi_max": 75.0, "proximity_52w_high_pct": 5.0},
    "volume": {"surge_multiplier": 1.3, "shocker_multiplier": 2.0},
    "catalyst": {"earnings_lookahead_days": 14}
}


def test_evaluate_technical_criteria():
    bullish_candidate = {
        "price": 500.0,
        "ema_20": 480.0,
        "ema_50": 460.0,
        "ema_200": 420.0,
        "rsi": 62.0,
        "distance_52w_high_pct": 2.5,
        "breakout_20d": True
    }
    res = evaluate_technical_criteria(bullish_candidate, THRESHOLDS)
    assert res["passed"] is True
    assert res["trend_aligned"] is True
    assert res["rsi_in_range"] is True
    assert res["near_52w_high"] is True

    bearish_candidate = {
        "price": 300.0,
        "ema_20": 320.0,
        "ema_50": 340.0,
        "ema_200": 400.0,
        "rsi": 38.0,
        "distance_52w_high_pct": 35.0,
        "breakout_20d": False
    }
    res_bear = evaluate_technical_criteria(bearish_candidate, THRESHOLDS)
    assert res_bear["passed"] is False
    assert res_bear["trend_aligned"] is False


def test_evaluate_volume_criteria():
    shocker_cand = {"tags": ["VOLUME_SHOCKER"], "volume_ratio": 2.5}
    res = evaluate_volume_criteria(shocker_cand, THRESHOLDS)
    assert res["passed"] is True
    assert res["is_volume_shocker"] is True

    low_vol_cand = {"tags": [], "volume_ratio": 0.8}
    res_low = evaluate_volume_criteria(low_vol_cand, THRESHOLDS)
    assert res_low["passed"] is False


def test_evaluate_liquidity_criteria():
    penny_cand = {"price": 12.0, "turnover_cr": 1.0, "volume": 50000}
    res = evaluate_liquidity_criteria(penny_cand, THRESHOLDS)
    assert res["passed"] is False
    assert res["is_penny_stock"] is True

    liquid_cand = {"price": 1250.0, "turnover_cr": 45.0, "volume": 2000000}
    res_liq = evaluate_liquidity_criteria(liquid_cand, THRESHOLDS)
    assert res_liq["passed"] is True
    assert res_liq["price_healthy"] is True


def test_evaluate_catalyst_criteria():
    cand_with_earnings = {"days_to_results": 5}
    res = evaluate_catalyst_criteria(cand_with_earnings, THRESHOLDS)
    assert res["has_catalyst"] is True

    cand_far = {"days_to_results": 45}
    res_far = evaluate_catalyst_criteria(cand_far, THRESHOLDS)
    assert res_far["has_catalyst"] is False
