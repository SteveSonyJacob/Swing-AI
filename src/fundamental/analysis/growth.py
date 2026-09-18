"""Growth analysis: YoY quarterly growth, QoQ sequential growth, and multi-year CAGR."""

from typing import Dict, Any, Optional, List
import pandas as pd


def calculate_pct_growth(current: Optional[float], base: Optional[float]) -> Optional[float]:
    """Calculates percentage change."""
    if current is None or base is None or base == 0:
        return None
    # If base is negative, conventional percentage change can be misleading
    if base < 0:
        return round(((current - base) / abs(base)) * 100.0, 2)
    return round(((current - base) / base) * 100.0, 2)


def calculate_cagr(start_val: Optional[float], end_val: Optional[float], years: float = 3.0) -> Optional[float]:
    """CAGR = (End / Start) ** (1 / years) - 1."""
    if start_val is None or end_val is None or start_val <= 0 or end_val <= 0 or years <= 0:
        return None
    try:
        cagr = ((end_val / start_val) ** (1.0 / years) - 1.0) * 100.0
        return round(cagr, 2)
    except Exception:
        return None


def analyze_growth(quarterly_is: Dict[str, Dict[str, float]], annual_is: Dict[str, Dict[str, float]]) -> Dict[str, Optional[float]]:
    """
    Analyzes quarterly YoY, QoQ, and 3-Year CAGR for revenue, PAT, and EPS.
    """
    sorted_q_dates = sorted(quarterly_is.keys(), key=lambda d: pd.to_datetime(d))
    sorted_a_dates = sorted(annual_is.keys(), key=lambda d: pd.to_datetime(d))

    rev_yoy = None
    pat_yoy = None
    eps_yoy = None

    # YoY quarterly growth (need at least 5 quarters to compare Q[t] with Q[t-4])
    if len(sorted_q_dates) >= 5:
        curr_q = quarterly_is[sorted_q_dates[-1]]
        yoy_q = quarterly_is[sorted_q_dates[-5]]

        rev_yoy = calculate_pct_growth(curr_q.get("Total Revenue"), yoy_q.get("Total Revenue"))
        pat_yoy = calculate_pct_growth(curr_q.get("Net Income"), yoy_q.get("Net Income"))
        eps_yoy = calculate_pct_growth(curr_q.get("Diluted EPS"), yoy_q.get("Diluted EPS"))
    elif len(sorted_a_dates) >= 2:
        # Fallback to annual YoY if quarterly history is short
        curr_a = annual_is[sorted_a_dates[-1]]
        prev_a = annual_is[sorted_a_dates[-2]]
        rev_yoy = calculate_pct_growth(curr_a.get("Total Revenue"), prev_a.get("Total Revenue"))
        pat_yoy = calculate_pct_growth(curr_a.get("Net Income"), prev_a.get("Net Income"))
        eps_yoy = calculate_pct_growth(curr_a.get("Diluted EPS"), prev_a.get("Diluted EPS"))

    # 3-Year CAGR from annual financial statements
    rev_cagr_3y = None
    pat_cagr_3y = None

    if len(sorted_a_dates) >= 4:
        start_a = annual_is[sorted_a_dates[-4]]
        end_a = annual_is[sorted_a_dates[-1]]
        rev_cagr_3y = calculate_cagr(start_a.get("Total Revenue"), end_a.get("Total Revenue"), years=3.0)
        pat_cagr_3y = calculate_cagr(start_a.get("Net Income"), end_a.get("Net Income"), years=3.0)
    elif len(sorted_a_dates) >= 3:
        start_a = annual_is[sorted_a_dates[-3]]
        end_a = annual_is[sorted_a_dates[-1]]
        rev_cagr_3y = calculate_cagr(start_a.get("Total Revenue"), end_a.get("Total Revenue"), years=2.0)
        pat_cagr_3y = calculate_cagr(start_a.get("Net Income"), end_a.get("Net Income"), years=2.0)

    return {
        "revenue_yoy": rev_yoy,
        "pat_yoy": pat_yoy,
        "eps_yoy": eps_yoy,
        "revenue_cagr_3y": rev_cagr_3y,
        "pat_cagr_3y": pat_cagr_3y
    }
