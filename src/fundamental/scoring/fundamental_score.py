"""Fundamental scoring engine implementing the 100-point deterministic rubric with missing-data normalization."""

from typing import Dict, Any, Optional, Tuple
import math
import numpy as np


def score_growth(growth_data: Dict[str, Any], max_points: int = 20) -> Tuple[int, int]:
    """Scores growth up to max_points. Returns (points, available_weight)."""
    rev_yoy = growth_data.get("revenue_yoy")
    pat_yoy = growth_data.get("pat_yoy")
    cagr_3y = growth_data.get("pat_cagr_3y") or growth_data.get("revenue_cagr_3y")

    if rev_yoy is None and pat_yoy is None and cagr_3y is None:
        return 0, 0

    points = 0
    # Revenue YoY (up to 6)
    if rev_yoy is not None:
        if rev_yoy >= 20.0:
            points += 6
        elif rev_yoy >= 12.0:
            points += 4
        elif rev_yoy >= 5.0:
            points += 2

    # PAT YoY (up to 8)
    if pat_yoy is not None:
        if pat_yoy >= 25.0:
            points += 8
        elif pat_yoy >= 15.0:
            points += 5
        elif pat_yoy >= 5.0:
            points += 3

    # Multi-year CAGR (up to 6)
    if cagr_3y is not None:
        if cagr_3y >= 20.0:
            points += 6
        elif cagr_3y >= 12.0:
            points += 4
        elif cagr_3y >= 5.0:
            points += 2

    return min(points, max_points), max_points


def score_profitability(prof_data: Dict[str, Any], max_points: int = 15) -> Tuple[int, int]:
    """Scores profitability up to max_points. Returns (points, available_weight)."""
    roe = prof_data.get("roe")
    roce = prof_data.get("roce")
    op_m = prof_data.get("operating_margin")
    trend = prof_data.get("margin_trend", "stable")

    if roe is None and roce is None and op_m is None:
        return 0, 0

    points = 0
    # ROE (up to 5)
    if roe is not None:
        if roe >= 18.0:
            points += 5
        elif roe >= 12.0:
            points += 3
        elif roe >= 8.0:
            points += 1

    # ROCE (up to 4)
    if roce is not None:
        if roce >= 20.0:
            points += 4
        elif roce >= 14.0:
            points += 2
        elif roce >= 8.0:
            points += 1

    # Operating Margin (up to 3)
    if op_m is not None:
        if op_m >= 18.0:
            points += 3
        elif op_m >= 10.0:
            points += 2
        elif op_m >= 5.0:
            points += 1

    # Margin trend (up to 3)
    if trend == "improving":
        points += 3
    elif trend == "stable":
        points += 2

    return min(points, max_points), max_points


def score_balance_sheet(bs_data: Dict[str, Any], max_points: int = 15) -> Tuple[int, int]:
    """Scores balance sheet health up to max_points. Returns (points, available_weight)."""
    de = bs_data.get("debt_equity")
    net_debt = bs_data.get("net_debt")
    ic = bs_data.get("interest_coverage")
    cr = bs_data.get("current_ratio")

    if de is None and ic is None and cr is None:
        return 0, 0

    points = 0
    # Debt to Equity (up to 6)
    if de is not None:
        if de <= 0.3:
            points += 6
        elif de <= 0.8:
            points += 4
        elif de <= 1.5:
            points += 2

    # Interest Coverage (up to 4)
    if ic is not None:
        if ic >= 8.0:
            points += 4
        elif ic >= 4.0:
            points += 2
        elif ic >= 2.0:
            points += 1

    # Current Ratio (up to 3)
    if cr is not None:
        if cr >= 1.3:
            points += 3
        elif cr >= 1.0:
            points += 2
        elif cr >= 0.8:
            points += 1

    # Net Debt (up to 2)
    if net_debt is not None and net_debt <= 0:
        points += 2

    return min(points, max_points), max_points


def score_cash_flow(cf_data: Dict[str, Any], max_points: int = 15) -> Tuple[int, int]:
    """Scores cash flows up to max_points. Returns (points, available_weight)."""
    ocf = cf_data.get("operating_cash_flow")
    fcf = cf_data.get("free_cash_flow")
    ocf_pat = cf_data.get("ocf_pat_ratio")
    trend = cf_data.get("cash_flow_trend", "moderate")

    if ocf is None and fcf is None and ocf_pat is None:
        return 0, 0

    points = 0
    # OCF / PAT ratio (up to 7)
    if ocf_pat is not None:
        if ocf_pat >= 1.0:
            points += 7
        elif ocf_pat >= 0.8:
            points += 5
        elif ocf_pat >= 0.5:
            points += 2

    # FCF (up to 4)
    if fcf is not None and fcf > 0:
        points += 4

    # Trend (up to 4)
    if trend == "strong":
        points += 4
    elif trend == "moderate":
        points += 2

    return min(points, max_points), max_points


def score_earnings_quality(eq_data: Dict[str, Any], max_points: int = 10) -> Tuple[int, int]:
    """Scores earnings quality up to max_points. Returns (points, available_weight)."""
    raw_pts = eq_data.get("score")
    if raw_pts is None:
        return 0, 0
    return min(int(raw_pts), max_points), max_points


def score_valuation(val_data: Dict[str, Any], growth_data: Dict[str, Any], max_points: int = 15) -> Tuple[int, int]:
    """Scores valuation considering relative sector multiples and growth. Returns (points, available_weight)."""
    pe = val_data.get("pe")
    assessment = val_data.get("valuation_assessment", "fair")
    pat_yoy = growth_data.get("pat_yoy") or 0.0

    if pe is None and val_data.get("pb") is None and val_data.get("ev_ebitda") is None:
        return 0, 0

    points = 0
    # Relative sector multiple (up to 10)
    if assessment == "discount":
        points += 10
    elif assessment == "fair":
        points += 7
    elif assessment == "premium":
        points += 5
    else:
        points += 2

    # Growth-adjusted valuation (up to 5)
    if pe is not None and pe > 0:
        if pe < 20:
            points += 5
        elif pe < 35 and pat_yoy > 20:
            points += 5
        elif pe < 45 and pat_yoy > 15:
            points += 3
        else:
            points += 1
    else:
        points += 2

    return min(points, max_points), max_points


def score_consistency(growth_data: Dict[str, Any], prof_data: Dict[str, Any], max_points: int = 5) -> Tuple[int, int]:
    """Scores earnings and margin consistency up to max_points."""
    points = 0
    rev_yoy = growth_data.get("revenue_yoy")
    pat_yoy = growth_data.get("pat_yoy")
    trend = prof_data.get("margin_trend")

    if rev_yoy is not None and rev_yoy > 0 and pat_yoy is not None and pat_yoy > 0:
        points += 3
    if trend in ("improving", "stable"):
        points += 2

    return min(points, max_points), max_points


def score_sector_relative(val_data: Dict[str, Any], prof_data: Dict[str, Any], max_points: int = 5) -> Tuple[int, int]:
    """Scores sector-relative positioning up to max_points."""
    points = 0
    roe = prof_data.get("roe")
    assessment = val_data.get("valuation_assessment")

    if roe is not None and roe > 15:
        points += 3
    if assessment in ("discount", "fair"):
        points += 2

    return min(points, max_points), max_points


def compute_fundamental_score(
    growth_data: Dict[str, Any],
    profitability_data: Dict[str, Any],
    balance_sheet_data: Dict[str, Any],
    cash_flow_data: Dict[str, Any],
    earnings_quality_data: Dict[str, Any],
    valuation_data: Dict[str, Any],
    weights: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Computes deterministic 100-point fundamental score and component breakdown,
    normalizing dynamically if non-critical data is missing.
    """
    if weights is None:
        weights = {
            "growth": 20,
            "profitability": 15,
            "balance_sheet": 15,
            "cash_flow": 15,
            "earnings_quality": 10,
            "valuation": 15,
            "consistency": 5,
            "sector_relative": 5
        }

    g_pts, g_w = score_growth(growth_data, weights["growth"])
    p_pts, p_w = score_profitability(profitability_data, weights["profitability"])
    b_pts, b_w = score_balance_sheet(balance_sheet_data, weights["balance_sheet"])
    c_pts, c_w = score_cash_flow(cash_flow_data, weights["cash_flow"])
    eq_pts, eq_w = score_earnings_quality(earnings_quality_data, weights["earnings_quality"])
    v_pts, v_w = score_valuation(valuation_data, growth_data, weights["valuation"])
    con_pts, con_w = score_consistency(growth_data, profitability_data, weights["consistency"])
    sec_pts, sec_w = score_sector_relative(valuation_data, profitability_data, weights["sector_relative"])

    breakdown = {
        "growth": g_pts,
        "profitability": p_pts,
        "balance_sheet": b_pts,
        "cash_flow": c_pts,
        "earnings_quality": eq_pts,
        "valuation": v_pts,
        "consistency": con_pts,
        "sector_relative": sec_pts
    }

    raw_sum = sum(breakdown.values())
    total_avail_weight = g_w + p_w + b_w + c_w + eq_w + v_w + con_w + sec_w

    if total_avail_weight > 0:
        normalized_score = int(round((raw_sum / total_avail_weight) * 100))
    else:
        normalized_score = 0

    normalized_score = max(0, min(100, normalized_score))

    return {
        "fundamental_score": normalized_score,
        "score_breakdown": breakdown,
        "data_completeness_pct": round((total_avail_weight / 100.0) * 100.0, 1)
    }
