"""Unit tests for Agent 1 candidate scoring engine."""

import pytest
from src.screening.scoring.screening_score import compute_screening_score


def test_scoring_bounds_and_structure():
    cand = {
        "price": 2880.0,
        "change_pct": 11.5,
        "ema_20": 2600.0,
        "ema_50": 2400.0,
        "ema_200": 2000.0,
        "rsi": 64.0,
        "distance_52w_high_pct": 0.5,
        "breakout_20d": True,
        "volume_ratio": 2.4,
        "volume": 2500000,
        "turnover_cr": 150.0,
        "days_to_results": 7,
        "tags": ["VOLUME_SHOCKER"]
    }
    res = compute_screening_score(cand)
    score = res["screening_score"]
    bd = res["score_breakdown"]

    assert 0 <= score <= 100
    assert score >= 80
    assert res["category"] in ["PRIME_SETUP", "STRONG_CANDIDATE"]
    assert "trend" in bd
    assert "momentum_breakout" in bd
    assert "volume" in bd
    assert "liquidity" in bd
    assert "catalyst" in bd
    assert "52W_HIGH_BREAKOUT" in res["tags"]
    assert "VOLUME_SHOCKER" in res["tags"]


def test_penny_stock_penalty():
    penny_cand = {
        "price": 8.5,
        "change_pct": 1.2,
        "volume": 50000
    }
    res = compute_screening_score(penny_cand)
    assert res["score_breakdown"]["liquidity"] == 0
    assert "PENNY_STOCK_WARNING" in res["tags"]


def test_custom_weights():
    cand = {"price": 250.0, "change_pct": 5.0, "volume": 1000000}
    custom_weights = {
        "trend": 50,
        "momentum_breakout": 10,
        "volume": 20,
        "liquidity": 10,
        "catalyst": 10
    }
    res = compute_screening_score(cand, weights=custom_weights)
    assert 0 <= res["screening_score"] <= 100
