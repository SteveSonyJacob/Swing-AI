"""Liquidity and quality screening filter."""

from typing import Dict, Any


def evaluate_liquidity_criteria(candidate: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates candidate's price and liquidity:
    - Filters out penny stocks (< min_price)
    - Validates minimum volume / turnover
    """
    price = candidate.get("price") or candidate.get("current_price") or 0.0
    turnover_cr = candidate.get("turnover_cr")
    volume = candidate.get("volume") or candidate.get("avg_volume_20")

    price_thresh = thresholds.get("price", {})
    min_price = price_thresh.get("min_price", 20.0)
    preferred_min_price = price_thresh.get("preferred_min_price", 100.0)

    liq_thresh = thresholds.get("liquidity", {})
    min_vol = liq_thresh.get("min_avg_daily_volume", 100000)
    min_turnover = liq_thresh.get("min_turnover_cr", 5.0)

    # Price checks
    is_penny_stock = price < min_price
    price_healthy = price >= preferred_min_price

    # Volume checks
    has_sufficient_vol = (volume is None) or (volume >= min_vol)
    has_sufficient_turnover = (turnover_cr is None) or (turnover_cr >= min_turnover)

    passed = not is_penny_stock and has_sufficient_vol and has_sufficient_turnover

    return {
        "passed": passed,
        "is_penny_stock": is_penny_stock,
        "price_healthy": price_healthy,
        "has_sufficient_volume": has_sufficient_vol,
        "has_sufficient_turnover": has_sufficient_turnover
    }
