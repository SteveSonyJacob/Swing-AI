"""Valuation analysis and sector relative comparison."""

from typing import Dict, Any, Optional


def assess_valuation(premium_pct: Optional[float], pe: Optional[float]) -> str:
    """Qualitative assessment of valuation relative to sector median and absolute levels."""
    if premium_pct is None:
        if pe is None:
            return "unvalued"
        if pe < 15:
            return "discount"
        elif pe < 28:
            return "fair"
        elif pe < 45:
            return "premium"
        else:
            return "expensive"

    if premium_pct <= -15.0:
        return "discount"
    elif -15.0 < premium_pct <= 15.0:
        return "fair"
    elif 15.0 < premium_pct <= 40.0:
        return "premium"
    else:
        return "expensive"


def analyze_valuation(
    market_metrics: Dict[str, Optional[float]],
    sector_name: str,
    sector_benchmarks: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Computes valuation multiples and compares against sector benchmarks.
    """
    pe = market_metrics.get("pe")
    pb = market_metrics.get("pb")
    ev_ebitda = market_metrics.get("ev_ebitda")

    benchmarks = sector_benchmarks.get(sector_name) or sector_benchmarks.get("Default", {"pe": 24.0})
    sector_pe = benchmarks.get("pe", 24.0)

    pe_premium = None
    if pe is not None and sector_pe is not None and sector_pe > 0:
        pe_premium = round(((pe - sector_pe) / sector_pe) * 100.0, 1)

    assessment = assess_valuation(pe_premium, pe)

    return {
        "pe": pe,
        "pb": pb,
        "ev_ebitda": ev_ebitda,
        "sector_pe": sector_pe,
        "pe_premium_to_sector": pe_premium,
        "valuation_assessment": assessment
    }
