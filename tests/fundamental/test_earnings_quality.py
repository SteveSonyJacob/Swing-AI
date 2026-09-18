"""Unit tests for earnings quality analysis."""

import pytest
from src.fundamental.analysis.earnings_quality import analyze_earnings_quality


def test_earnings_quality_strong():
    growth = {"revenue_yoy": 18.0, "pat_yoy": 22.0}
    cash_flow = {"ocf_pat_ratio": 1.15}
    balance_sheet = {"debt_equity": 0.2, "interest_coverage": 12.0}

    res = analyze_earnings_quality(growth, cash_flow, balance_sheet, {}, {})
    assert res["score"] >= 8
    assert res["status"] == "strong"
    assert len(res["warnings"]) == 0


def test_earnings_quality_warning_on_accrual_divergence():
    growth = {"revenue_yoy": 5.0, "pat_yoy": 45.0}
    cash_flow = {"ocf_pat_ratio": 0.35}  # Bad cash conversion
    balance_sheet = {"debt_equity": 2.5, "interest_coverage": 1.5}

    res = analyze_earnings_quality(growth, cash_flow, balance_sheet, {}, {})
    assert res["score"] < 6
    assert res["status"] in ("moderate", "warning")
    assert len(res["warnings"]) > 0
