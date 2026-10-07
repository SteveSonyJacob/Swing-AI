"""Cash flow health analysis: OCF, FCF, and OCF/PAT ratio with strict period granularity matching."""

from typing import Dict, Any, Optional
import pandas as pd
from src.fundamental.ratios.financial_ratios import calculate_ocf_pat_ratio


def determine_cash_flow_trend(ocf: Optional[float], fcf: Optional[float], ocf_pat: Optional[float]) -> str:
    """Evaluates cash flow quality trend."""
    if ocf is None or ocf <= 0:
        return "negative"
    if ocf_pat is not None and ocf_pat >= 1.0 and (fcf is not None and fcf > 0):
        return "strong"
    elif ocf_pat is not None and ocf_pat >= 0.7:
        return "moderate"
    else:
        return "weak"


def analyze_cash_flow(
    quarterly_cf: Dict[str, Dict[str, float]],
    annual_cf: Dict[str, Dict[str, float]],
    quarterly_is: Optional[Dict[str, Dict[str, float]]] = None,
    annual_is: Optional[Dict[str, Dict[str, float]]] = None,
    latest_pat: Optional[float] = None
) -> Dict[str, Any]:
    """
    Analyzes cash flows ensuring strict period granularity alignment:
    - Annual OCF is compared strictly with Annual PAT
    - Quarterly OCF is compared strictly with Quarterly PAT
    - TTM OCF is compared strictly with TTM PAT
    Never mixes annual cash flows with quarterly earnings. Returns controlled None if matching PAT is missing.
    """
    sorted_q_cf = sorted(quarterly_cf.keys(), key=lambda d: pd.to_datetime(d))
    sorted_a_cf = sorted(annual_cf.keys(), key=lambda d: pd.to_datetime(d))

    ocf = None
    fcf = None
    ocf_pat = None
    period_type = "none"

    # Case 1: TTM cash flow (if at least 4 consecutive quarterly cash flow statements exist)
    if len(sorted_q_cf) >= 4 and quarterly_is and len(quarterly_is) >= 4:
        recent_4_cf = sorted_q_cf[-4:]
        has_all_cf = all("Operating Cash Flow" in quarterly_cf[d] for d in recent_4_cf)
        has_all_pat = all(d in quarterly_is and "Net Income" in quarterly_is[d] for d in recent_4_cf)

        if has_all_cf and has_all_pat:
            ttm_ocf = sum(quarterly_cf[d]["Operating Cash Flow"] for d in recent_4_cf)
            ttm_capex = sum(abs(quarterly_cf[d].get("Capital Expenditure", 0.0)) for d in recent_4_cf)
            ttm_pat = sum(quarterly_is[d]["Net Income"] for d in recent_4_cf)

            ocf = ttm_ocf
            fcf = ttm_ocf - ttm_capex
            ocf_pat = calculate_ocf_pat_ratio(ttm_ocf, ttm_pat)
            period_type = "ttm"

    # Case 2: Latest quarterly cash flow (matched to quarterly PAT)
    if ocf is None and sorted_q_cf:
        latest_q_date = sorted_q_cf[-1]
        latest_cf = quarterly_cf[latest_q_date]
        ocf = latest_cf.get("Operating Cash Flow")
        capex = latest_cf.get("Capital Expenditure")
        fcf = latest_cf.get("Free Cash Flow")
        if fcf is None and ocf is not None and capex is not None:
            fcf = ocf - abs(capex)

        matching_pat = None
        if quarterly_is and latest_q_date in quarterly_is:
            matching_pat = quarterly_is[latest_q_date].get("Net Income")
        elif latest_pat is not None:
            matching_pat = latest_pat

        ocf_pat = calculate_ocf_pat_ratio(ocf, matching_pat)
        period_type = "quarterly"

    # Case 3: Annual cash flow (matched strictly to Annual PAT)
    if ocf is None and sorted_a_cf:
        latest_a_date = sorted_a_cf[-1]
        latest_cf = annual_cf[latest_a_date]
        ocf = latest_cf.get("Operating Cash Flow")
        capex = latest_cf.get("Capital Expenditure")
        fcf = latest_cf.get("Free Cash Flow")
        if fcf is None and ocf is not None and capex is not None:
            fcf = ocf - abs(capex)

        matching_pat = None
        if annual_is and latest_a_date in annual_is:
            matching_pat = annual_is[latest_a_date].get("Net Income")

        # Crucial: Never pair annual OCF with quarterly PAT! If annual matching PAT is missing, ocf_pat is None.
        ocf_pat = calculate_ocf_pat_ratio(ocf, matching_pat)
        period_type = "annual"

    trend = determine_cash_flow_trend(ocf, fcf, ocf_pat)

    return {
        "operating_cash_flow": round(ocf, 2) if ocf is not None else None,
        "free_cash_flow": round(fcf, 2) if fcf is not None else None,
        "ocf_pat_ratio": ocf_pat,
        "cash_flow_trend": trend,
        "period_type": period_type
    }
