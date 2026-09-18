"""Unit tests for valuation analysis."""

import pytest
from src.fundamental.analysis.valuation import analyze_valuation, assess_valuation


def test_assess_valuation():
    assert assess_valuation(-20.0, 18.0) == "discount"
    assert assess_valuation(5.0, 25.0) == "fair"
    assert assess_valuation(25.0, 30.0) == "premium"
    assert assess_valuation(50.0, 45.0) == "expensive"


def test_analyze_valuation_against_sector():
    market_metrics = {"pe": 28.0, "pb": 4.1, "ev_ebitda": 18.2}
    sector_benchmarks = {"Energy": {"pe": 24.0, "pb": 3.0}}

    res = analyze_valuation(market_metrics, "Energy", sector_benchmarks)
    assert res["pe"] == 28.0
    assert res["sector_pe"] == 24.0
    assert res["pe_premium_to_sector"] == 16.7
    assert res["valuation_assessment"] == "premium"
