"""Calculation of standard fundamental ratios."""

from typing import Optional, Dict, Any
import numpy as np


def calculate_operating_margin(operating_profit: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Operating Margin = (Operating Profit / Revenue) * 100."""
    if operating_profit is None or revenue is None or revenue <= 0:
        return None
    return round((operating_profit / revenue) * 100.0, 2)


def calculate_net_margin(pat: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Net Margin = (PAT / Revenue) * 100."""
    if pat is None or revenue is None or revenue <= 0:
        return None
    return round((pat / revenue) * 100.0, 2)


def calculate_roe(net_income: Optional[float], equity: Optional[float]) -> Optional[float]:
    """ROE = (Net Income / Shareholders' Equity) * 100."""
    if net_income is None or equity is None or equity <= 0:
        return None
    return round((net_income / equity) * 100.0, 2)


def calculate_roce(ebit: Optional[float], capital_employed: Optional[float]) -> Optional[float]:
    """ROCE = (EBIT / Capital Employed) * 100."""
    if ebit is None or capital_employed is None or capital_employed <= 0:
        return None
    return round((ebit / capital_employed) * 100.0, 2)


def calculate_debt_equity(total_debt: Optional[float], equity: Optional[float]) -> Optional[float]:
    """Debt / Equity ratio."""
    if total_debt is None or equity is None or equity <= 0:
        return None
    return round(total_debt / equity, 2)


def calculate_net_debt(total_debt: Optional[float], cash: Optional[float]) -> Optional[float]:
    """Net Debt = Total Debt - Cash."""
    if total_debt is None:
        return None
    cash_val = cash if cash is not None else 0.0
    return round(total_debt - cash_val, 2)


def calculate_interest_coverage(ebit: Optional[float], interest_expense: Optional[float]) -> Optional[float]:
    """Interest Coverage = EBIT / Interest Expense."""
    if ebit is None or interest_expense is None:
        return None
    if interest_expense <= 0:
        return 999.0 if ebit > 0 else 0.0
    return round(ebit / interest_expense, 2)


def calculate_current_ratio(current_assets: Optional[float], current_liabilities: Optional[float]) -> Optional[float]:
    """Current Ratio = Current Assets / Current Liabilities."""
    if current_assets is None or current_liabilities is None or current_liabilities <= 0:
        return None
    return round(current_assets / current_liabilities, 2)


def calculate_ocf_pat_ratio(ocf: Optional[float], pat: Optional[float]) -> Optional[float]:
    """Earnings-to-cash conversion = OCF / PAT."""
    if ocf is None or pat is None or pat == 0:
        return None
    return round(ocf / pat, 2)
