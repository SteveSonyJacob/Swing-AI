"""Balance sheet health analysis."""

from typing import Dict, Any, Optional
import pandas as pd
from src.fundamental.ratios.financial_ratios import (
    calculate_debt_equity,
    calculate_net_debt,
    calculate_interest_coverage,
    calculate_current_ratio
)


def analyze_balance_sheet(
    quarterly_is: Dict[str, Dict[str, float]],
    quarterly_bs: Dict[str, Dict[str, float]],
    annual_is: Dict[str, Dict[str, float]],
    annual_bs: Dict[str, Dict[str, float]]
) -> Dict[str, Optional[float]]:
    """
    Analyzes balance sheet health: Debt/Equity, Net Debt, Interest Coverage, Current Ratio.
    """
    sorted_q_dates = sorted(quarterly_is.keys(), key=lambda d: pd.to_datetime(d))
    sorted_a_dates = sorted(annual_is.keys(), key=lambda d: pd.to_datetime(d))

    latest_is = quarterly_is[sorted_q_dates[-1]] if sorted_q_dates else (annual_is[sorted_a_dates[-1]] if sorted_a_dates else {})
    latest_bs = quarterly_bs.get(sorted_q_dates[-1], {}) if sorted_q_dates else (annual_bs.get(sorted_a_dates[-1], {}) if sorted_a_dates else {})

    total_debt = latest_bs.get("Total Debt")
    cash = latest_bs.get("Cash And Cash Equivalents")
    equity = latest_bs.get("Stockholders Equity")
    curr_assets = latest_bs.get("Current Assets")
    curr_liab = latest_bs.get("Current Liabilities")

    ebit = latest_is.get("Operating Income") or latest_is.get("EBITDA")
    interest = latest_is.get("Interest Expense")

    de = calculate_debt_equity(total_debt, equity)
    net_debt = calculate_net_debt(total_debt, cash)
    ic = calculate_interest_coverage(ebit, interest)
    cr = calculate_current_ratio(curr_assets, curr_liab)

    return {
        "debt_equity": de,
        "net_debt": net_debt,
        "interest_coverage": ic,
        "current_ratio": cr
    }
