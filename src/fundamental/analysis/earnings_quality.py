"""Earnings quality analysis and accounting anomaly detection."""

from typing import Dict, Any, List, Optional


def analyze_earnings_quality(
    growth_data: Dict[str, Any],
    cash_flow_data: Dict[str, Any],
    balance_sheet_data: Dict[str, Any],
    quarterly_is: Dict[str, Dict[str, float]],
    quarterly_bs: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Evaluates earnings quality by comparing cash conversion, receivables expansion,
    and debt-funded growth.
    """
    warnings: List[str] = []
    points = 10  # Baseline out of 10

    ocf_pat = cash_flow_data.get("ocf_pat_ratio")
    rev_yoy = growth_data.get("revenue_yoy")
    pat_yoy = growth_data.get("pat_yoy")
    de = balance_sheet_data.get("debt_equity")
    ic = balance_sheet_data.get("interest_coverage")

    # 1. Cash flow vs Accounting Earnings
    if ocf_pat is not None:
        if ocf_pat < 0.5:
            warnings.append("Low earnings-to-cash conversion (OCF/PAT < 0.5)")
            points -= 4
        elif ocf_pat < 0.8:
            warnings.append("Moderate cash conversion shortfall (OCF/PAT < 0.8)")
            points -= 2

    # 2. PAT growth vs Revenue growth divergence
    if pat_yoy is not None and rev_yoy is not None:
        if pat_yoy > 40 and rev_yoy < 5:
            warnings.append("PAT growth significantly outpaces revenue without apparent core operational expansion")
            points -= 2

    # 3. Solvency & Coverage Risk
    if de is not None and de > 2.0:
        warnings.append(f"Elevated financial leverage (Debt/Equity: {de})")
        points -= 2
    if ic is not None and ic < 2.0:
        warnings.append(f"Tight interest coverage ratio ({ic}x)")
        points -= 2

    points = max(0, min(10, points))

    if points >= 8:
        status = "strong"
    elif points >= 5:
        status = "moderate"
    else:
        status = "warning"

    return {
        "score": points,
        "status": status,
        "warnings": warnings
    }
