"""Unit tests for growth and CAGR calculations."""

import pytest
from src.fundamental.analysis.growth import calculate_pct_growth, calculate_cagr, analyze_growth


def test_pct_growth():
    assert calculate_pct_growth(120.0, 100.0) == 20.0
    assert calculate_pct_growth(80.0, 100.0) == -20.0
    assert calculate_pct_growth(None, 100.0) is None
    assert calculate_pct_growth(100.0, 0) is None


def test_cagr():
    # 100 growing to 133.1 over 3 years is 10% CAGR
    assert calculate_cagr(100.0, 133.1, years=3.0) == 10.0
    assert calculate_cagr(None, 100.0) is None
    assert calculate_cagr(-50.0, 100.0) is None


def test_analyze_growth_quarterly_and_annual():
    q_is = {
        "2024-06-30": {"Total Revenue": 1000.0, "Net Income": 100.0, "Diluted EPS": 1.0},
        "2024-09-30": {"Total Revenue": 1050.0, "Net Income": 105.0, "Diluted EPS": 1.05},
        "2024-12-31": {"Total Revenue": 1100.0, "Net Income": 110.0, "Diluted EPS": 1.10},
        "2025-03-31": {"Total Revenue": 1150.0, "Net Income": 115.0, "Diluted EPS": 1.15},
        "2025-06-30": {"Total Revenue": 1200.0, "Net Income": 130.0, "Diluted EPS": 1.30},
    }
    a_is = {
        "2022-03-31": {"Total Revenue": 3000.0, "Net Income": 300.0},
        "2023-03-31": {"Total Revenue": 3500.0, "Net Income": 360.0},
        "2024-03-31": {"Total Revenue": 4000.0, "Net Income": 430.0},
        "2025-03-31": {"Total Revenue": 4800.0, "Net Income": 550.0},
    }

    res = analyze_growth(q_is, a_is)
    # YoY Q5 vs Q1: Rev (1200 - 1000) / 1000 = 20%
    assert res["revenue_yoy"] == 20.0
    # YoY Q5 vs Q1: PAT (130 - 100) / 100 = 30%
    assert res["pat_yoy"] == 30.0
    assert res["eps_yoy"] == 30.0
    assert res["revenue_cagr_3y"] is not None
    assert res["pat_cagr_3y"] is not None
