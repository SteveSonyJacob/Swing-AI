"""Unit and regression tests for multi-agent confirmation gating and composite verdicts."""

import pytest
from src.screening.output.pipeline import evaluate_composite_verdict


def test_scenario_b_fundamentally_strong_but_technically_broken():
    """High screening + High fundamentals + Bearish technical must NEVER be a BUY."""
    score, verdict, reason = evaluate_composite_verdict(
        agent_1_score=85,
        agent_2_score=37,
        agent_3_score=80,
        daily_trend="bearish",
        tech_status="success",
        fund_status="success"
    )
    assert verdict != "STRONG_BUY_CANDIDATE"
    assert verdict != "MODERATE_BUY_CANDIDATE"
    assert verdict == "WATCHLIST_WAIT_FOR_SETUP"
    assert "bearish" in reason.lower()


def test_scenario_a_mutual_strong_confirmation():
    """High screening + High fundamentals + Bullish technical must be a STRONG_BUY_CANDIDATE."""
    score, verdict, reason = evaluate_composite_verdict(
        agent_1_score=80,
        agent_2_score=75,
        agent_3_score=75,
        daily_trend="bullish",
        tech_status="success",
        fund_status="success"
    )
    assert verdict == "STRONG_BUY_CANDIDATE"
    assert score >= 70


def test_moderate_buy_setup():
    """Moderate technical setup (>= 55) and decent fundamentals can be MODERATE_BUY_CANDIDATE."""
    score, verdict, reason = evaluate_composite_verdict(
        agent_1_score=60,
        agent_2_score=60,
        agent_3_score=58,
        daily_trend="bullish",
        tech_status="success",
        fund_status="success"
    )
    assert verdict == "MODERATE_BUY_CANDIDATE"


def test_scenario_c_technically_strong_fundamentally_weak():
    """Technically bullish but weak fundamentals must be marked speculative, not regular buy."""
    score, verdict, reason = evaluate_composite_verdict(
        agent_1_score=75,
        agent_2_score=72,
        agent_3_score=30,  # distressed/poor fundamentals
        daily_trend="bullish",
        tech_status="success",
        fund_status="success"
    )
    assert verdict == "SPECULATIVE_TECHNICAL_ONLY"
    assert "poor" in reason.lower() or "risk" in reason.lower()


def test_scenario_d_missing_technical_data():
    """Missing or failed Agent 2 technical data cannot trigger a buy."""
    score, verdict, reason = evaluate_composite_verdict(
        agent_1_score=85,
        agent_2_score=None,
        agent_3_score=80,
        daily_trend=None,
        tech_status="insufficient_data"
    )
    assert verdict == "INSUFFICIENT_DATA_HOLD"
