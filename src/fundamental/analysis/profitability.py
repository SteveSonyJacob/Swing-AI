"""Profitability analysis: Margins, ROE, ROCE, and margin trend."""

from typing import Dict, Any, Optional, List
import pandas as pd
from src.fundamental.ratios.financial_ratios import (
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roe,
    calculate_roce
)


def determine_margin_trend(margins: List[float]) -> str:
    """Determines if margin is improving, stable, or deteriorating over recent periods."""
    if len(margins) < 2:
        return "stable"
    diffs = [margins[i] - margins[i - 1] for i in range(1, len(margins))]
    avg_diff = sum(diffs) / len(diffs)
    if avg_diff > 0.5:
        return "improving"
    elif avg_diff < -0.5:
        return "deteriorating"
    else:
        return "stable"


def analyze_profitability(
    quarterly_is: Dict[str, Dict[str, float]],
    quarterly_bs: Dict[str, Dict[str, float]],
    annual_is: Dict[str, Dict[str, float]],
    annual_bs: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Computes profitability metrics: ROE, ROCE, Operating Margin, Net Margin, and Margin Trend.
    """
    sorted_q_dates = sorted(quarterly_is.keys(), key=lambda d: pd.to_datetime(d))
    sorted_a_dates = sorted(annual_is.keys(), key=lambda d: pd.to_datetime(d))

    latest_is = quarterly_is[sorted_q_dates[-1]] if sorted_q_dates else (annual_is[sorted_a_dates[-1]] if sorted_a_dates else {})
    latest_bs = quarterly_bs.get(sorted_q_dates[-1], {}) if sorted_q_dates else (annual_bs.get(sorted_a_dates[-1], {}) if sorted_a_dates else {})

    # Revenue and profits
    rev = latest_is.get("Total Revenue")
    ebit = latest_is.get("Operating Income") or latest_is.get("EBITDA")
    pat = latest_is.get("Net Income")

    op_margin = calculate_operating_margin(ebit, rev)
    net_margin = calculate_net_margin(pat, rev)

    # Balance sheet items for ROE & ROCE
    equity = latest_bs.get("Stockholders Equity")
    debt = latest_bs.get("Total Debt") or 0.0
    cap_employed = (equity + debt) if equity is not None else None

    # For annualizing quarterly figures: prefer true 4-quarter TTM aggregation
    if len(sorted_q_dates) >= 4:
        ann_pat = sum(quarterly_is[d].get("Net Income", 0.0) for d in sorted_q_dates[-4:])
        ann_ebit = sum((quarterly_is[d].get("Operating Income") or quarterly_is[d].get("EBITDA") or 0.0) for d in sorted_q_dates[-4:])
    elif sorted_a_dates:
        latest_ann = annual_is[sorted_a_dates[-1]]
        ann_pat = latest_ann.get("Net Income")
        ann_ebit = latest_ann.get("Operating Income") or latest_ann.get("EBITDA")
    else:
        is_quarterly = bool(sorted_q_dates)
        multiplier = 4.0 if is_quarterly else 1.0
        ann_pat = (pat * multiplier) if pat is not None else None
        ann_ebit = (ebit * multiplier) if ebit is not None else None

    roe = calculate_roe(ann_pat, equity)
    roce = calculate_roce(ann_ebit, cap_employed)

    # Margin trend over last 3-4 quarters
    historical_margins = []
    for d in sorted_q_dates[-4:]:
        q_data = quarterly_is[d]
        q_rev = q_data.get("Total Revenue")
        q_ebit = q_data.get("Operating Income") or q_data.get("EBITDA")
        m = calculate_operating_margin(q_ebit, q_rev)
        if m is not None:
            historical_margins.append(m)

    trend = determine_margin_trend(historical_margins)

    return {
        "roe": roe,
        "roce": roce,
        "operating_margin": op_margin,
        "net_margin": net_margin,
        "margin_trend": trend
    }
