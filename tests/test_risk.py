"""Unit tests for risk and trade level calculations."""

import pytest
from src.risk.trade_levels import calculate_trade_levels


def test_bullish_trade_levels_calculation():
    current_close = 1250.0
    atr = 30.0
    levels = {"support": 1210.0, "resistance": 1350.0}

    setup = calculate_trade_levels(
        current_close=current_close,
        atr=atr,
        levels=levels,
        trend="bullish",
        stop_atr_multiplier=1.5,
        min_score_for_setup=50,
        technical_score=75
    )

    assert setup["direction"] == "long"
    assert setup["entry_zone"] is not None
    assert setup["stop_loss"] is not None
    assert setup["stop_loss"] < current_close
    assert setup["target_1"] > current_close
    assert setup["target_2"] > setup["target_1"]
    assert setup["risk_reward"] > 0


def test_bearish_trade_levels_returns_null():
    current_close = 1250.0
    atr = 30.0
    levels = {"support": 1210.0, "resistance": 1350.0}

    setup = calculate_trade_levels(
        current_close=current_close,
        atr=atr,
        levels=levels,
        trend="bearish",
        technical_score=25
    )

    assert setup["direction"] == "none"
    assert setup["entry_zone"] is None
    assert setup["stop_loss"] is None
    assert setup["target_1"] is None
    assert setup["risk_reward"] is None
