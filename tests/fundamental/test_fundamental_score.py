"""Unit tests for the 100-point fundamental scoring engine and normalization."""

import pytest
from src.fundamental.scoring.fundamental_score import (
    compute_fundamental_score,
    score_growth,
    score_profitability,
    score_balance_sheet,
    score_cash_flow,
    score_earnings_quality,
    score_valuation
)


def test_fundamental_score_bounds_and_breakdown():
    growth = {"revenue_yoy": 18.2, "pat_yoy": 31.4, "pat_cagr_3y": 21.3}
    prof = {"roe": 21.3, "roce": 24.8, "operating_margin": 18.4, "margin_trend": "improving"}
    bs = {"debt_equity": 0.18, "net_debt": -50.0, "interest_coverage": 12.4, "current_ratio": 1.72}
    cf = {"operating_cash_flow": 1100.0, "free_cash_flow": 820.0, "ocf_pat_ratio": 1.10, "cash_flow_trend": "strong"}
    eq = {"score": 8, "status": "strong"}
    val = {"pe": 28.0, "valuation_assessment": "premium"}

    res = compute_fundamental_score(growth, prof, bs, cf, eq, val)
    score = res["fundamental_score"]
    breakdown = res["score_breakdown"]

    assert 0 <= score <= 100
    assert score >= 75
    assert len(breakdown) == 8


def test_fundamental_score_missing_data_normalization():
    # If cash flow is completely missing, the score should still normalize to 100 gracefully
    growth = {"revenue_yoy": 15.0, "pat_yoy": 20.0}
    prof = {"roe": 18.0, "operating_margin": 15.0}
    bs = {"debt_equity": 0.3}
    cf = {}  # Empty cash flow
    eq = {"score": 8}
    val = {"pe": 20.0, "valuation_assessment": "fair"}

    res = compute_fundamental_score(growth, prof, bs, cf, eq, val)
    score = res["fundamental_score"]
    assert 0 <= score <= 100
    assert res["data_completeness_pct"] < 100.0


def test_bank_nbfc_balance_sheet_exemption():
    """Verify that banks and financial institutions are exempt from corporate D/E and current ratio."""
    bs_financial = {"is_financial": True, "debt_equity": 6.5, "current_ratio": 0.5}
    pts, weight = score_balance_sheet(bs_financial, max_points=15)
    assert pts == 0
    assert weight == 0  # Zero weight means omitted from denominator

    # When scoring a healthy bank, missing corporate BS ratios do not drag down the normalized score
    growth = {"revenue_yoy": 25.0, "pat_yoy": 30.0}
    prof = {"roe": 19.0, "operating_margin": 22.0}
    cf = {"operating_cash_flow": 5000.0, "free_cash_flow": 4000.0, "ocf_pat_ratio": 1.1}
    eq = {"score": 9}
    val = {"pe": 16.0, "valuation_assessment": "discount"}

    res = compute_fundamental_score(growth, prof, bs_financial, cf, eq, val)
    # The score should be strong because available components are normalized over remaining weight
    assert res["fundamental_score"] >= 80

