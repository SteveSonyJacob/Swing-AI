"""Unit tests for cash flow analysis."""

import pytest
from src.fundamental.analysis.cash_flow import analyze_cash_flow, determine_cash_flow_trend


def test_determine_cash_flow_trend():
    assert determine_cash_flow_trend(1000.0, 500.0, 1.2) == "strong"
    assert determine_cash_flow_trend(1000.0, -100.0, 0.75) == "moderate"
    assert determine_cash_flow_trend(-200.0, -400.0, -0.5) == "negative"


def test_analyze_cash_flow():
    q_cf = {
        "2025-06-30": {
            "Operating Cash Flow": 1200.0,
            "Capital Expenditure": 300.0,
            "Free Cash Flow": 900.0
        }
    }
    res = analyze_cash_flow(q_cf, {}, latest_pat=1000.0)
    assert res["operating_cash_flow"] == 1200.0
    assert res["free_cash_flow"] == 900.0
    assert res["ocf_pat_ratio"] == 1.20
    assert res["cash_flow_trend"] == "strong"
