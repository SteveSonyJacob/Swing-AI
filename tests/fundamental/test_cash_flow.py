"""Unit and regression tests for cash flow analysis and period granularity matching."""

import pytest
from src.fundamental.analysis.cash_flow import analyze_cash_flow, determine_cash_flow_trend


def test_determine_cash_flow_trend():
    assert determine_cash_flow_trend(1000.0, 500.0, 1.2) == "strong"
    assert determine_cash_flow_trend(1000.0, -100.0, 0.75) == "moderate"
    assert determine_cash_flow_trend(-200.0, -400.0, -0.5) == "negative"


def test_quarterly_ocf_with_matching_quarterly_pat():
    q_cf = {
        "2025-06-30": {
            "Operating Cash Flow": 1200.0,
            "Capital Expenditure": 300.0,
            "Free Cash Flow": 900.0
        }
    }
    q_is = {
        "2025-06-30": {"Net Income": 1000.0}
    }
    res = analyze_cash_flow(q_cf, {}, quarterly_is=q_is)
    assert res["operating_cash_flow"] == 1200.0
    assert res["free_cash_flow"] == 900.0
    assert res["ocf_pat_ratio"] == 1.20
    assert res["cash_flow_trend"] == "strong"
    assert res["period_type"] == "quarterly"


def test_annual_ocf_with_matching_annual_pat_no_quarterly_mixing():
    """Verify that when quarterly cash flow is missing, annual OCF is strictly matched with annual PAT."""
    q_cf = {}  # No quarterly cash flow
    a_cf = {
        "2025-03-31": {
            "Operating Cash Flow": 5000.0,
            "Capital Expenditure": 1200.0
        }
    }
    # Quarterly IS has single quarter PAT of 1200
    q_is = {
        "2025-06-30": {"Net Income": 1200.0}
    }
    # Annual IS has full year PAT of 4500
    a_is = {
        "2025-03-31": {"Net Income": 4500.0}
    }

    res = analyze_cash_flow(q_cf, a_cf, quarterly_is=q_is, annual_is=a_is)
    assert res["operating_cash_flow"] == 5000.0
    assert res["free_cash_flow"] == 3800.0
    # Must be 5000 / 4500 = 1.11, NOT 5000 / 1200 = 4.17
    assert res["ocf_pat_ratio"] == round(5000.0 / 4500.0, 2)
    assert res["period_type"] == "annual"


def test_ttm_ocf_with_ttm_pat():
    """Verify rolling 4-quarter TTM calculation when 4 quarters of data are present."""
    q_cf = {
        "2024-09-30": {"Operating Cash Flow": 1000.0, "Capital Expenditure": 200.0},
        "2024-12-31": {"Operating Cash Flow": 1100.0, "Capital Expenditure": 250.0},
        "2025-03-31": {"Operating Cash Flow": 1200.0, "Capital Expenditure": 300.0},
        "2025-06-30": {"Operating Cash Flow": 1300.0, "Capital Expenditure": 350.0},
    }
    q_is = {
        "2024-09-30": {"Net Income": 900.0},
        "2024-12-31": {"Net Income": 950.0},
        "2025-03-31": {"Net Income": 1000.0},
        "2025-06-30": {"Net Income": 1050.0},
    }
    res = analyze_cash_flow(q_cf, {}, quarterly_is=q_is)
    # TTM OCF = 1000 + 1100 + 1200 + 1300 = 4600
    assert res["operating_cash_flow"] == 4600.0
    # TTM capex = 200 + 250 + 300 + 350 = 1100 => FCF = 3500
    assert res["free_cash_flow"] == 3500.0
    # TTM PAT = 900 + 950 + 1000 + 1050 = 3900 => OCF/PAT = 4600 / 3900 = 1.18
    assert res["ocf_pat_ratio"] == round(4600.0 / 3900.0, 2)
    assert res["period_type"] == "ttm"


def test_missing_matching_pat_returns_none():
    """When matching PAT is unavailable for the cash flow statement period, ocf_pat_ratio must be None."""
    a_cf = {
        "2025-03-31": {"Operating Cash Flow": 4000.0, "Capital Expenditure": 1000.0}
    }
    # No matching annual income statement
    res = analyze_cash_flow({}, a_cf, quarterly_is={}, annual_is={})
    assert res["operating_cash_flow"] == 4000.0
    assert res["ocf_pat_ratio"] is None
