"""Cash flow health analysis: OCF, FCF, and OCF/PAT ratio."""

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
    latest_pat: Optional[float]
) -> Dict[str, Any]:
    """
    Analyzes cash flows from quarterly or annual cash flow statements.
    """
    sorted_q_dates = sorted(quarterly_cf.keys(), key=lambda d: pd.to_datetime(d))
    sorted_a_dates = sorted(annual_cf.keys(), key=lambda d: pd.to_datetime(d))

    latest_cf = quarterly_cf[sorted_q_dates[-1]] if sorted_q_dates else (annual_cf[sorted_a_dates[-1]] if sorted_a_dates else {})

    ocf = latest_cf.get("Operating Cash Flow")
    capex = latest_cf.get("Capital Expenditure")
    fcf = latest_cf.get("Free Cash Flow")

    if fcf is None and ocf is not None and capex is not None:
        fcf = ocf - abs(capex)

    ocf_pat = calculate_ocf_pat_ratio(ocf, latest_pat)
    trend = determine_cash_flow_trend(ocf, fcf, ocf_pat)

    return {
        "operating_cash_flow": round(ocf, 2) if ocf is not None else None,
        "free_cash_flow": round(fcf, 2) if fcf is not None else None,
        "ocf_pat_ratio": ocf_pat,
        "cash_flow_trend": trend
    }
