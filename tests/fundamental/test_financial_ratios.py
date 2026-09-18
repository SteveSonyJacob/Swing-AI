"""Unit tests for financial ratios calculation."""

import pytest
from src.fundamental.ratios.financial_ratios import (
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roe,
    calculate_roce,
    calculate_debt_equity,
    calculate_net_debt,
    calculate_interest_coverage,
    calculate_current_ratio,
    calculate_ocf_pat_ratio
)


def test_margins():
    assert calculate_operating_margin(200.0, 1000.0) == 20.0
    assert calculate_net_margin(120.0, 1000.0) == 12.0
    assert calculate_operating_margin(None, 1000.0) is None
    assert calculate_net_margin(120.0, 0) is None


def test_roe_and_roce():
    assert calculate_roe(250.0, 1000.0) == 25.0
    assert calculate_roce(300.0, 1200.0) == 25.0
    assert calculate_roe(None, 1000.0) is None
    assert calculate_roe(250.0, 0) is None


def test_balance_sheet_ratios():
    assert calculate_debt_equity(200.0, 1000.0) == 0.2
    assert calculate_net_debt(500.0, 200.0) == 300.0
    assert calculate_interest_coverage(100.0, 10.0) == 10.0
    assert calculate_current_ratio(150.0, 100.0) == 1.5


def test_ocf_pat_ratio():
    assert calculate_ocf_pat_ratio(1100.0, 1000.0) == 1.10
    assert calculate_ocf_pat_ratio(800.0, 1000.0) == 0.8
    assert calculate_ocf_pat_ratio(None, 1000.0) is None
