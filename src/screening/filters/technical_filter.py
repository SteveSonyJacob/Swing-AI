"""Technical swing screening filter."""

from typing import Dict, Any


def evaluate_technical_criteria(candidate: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates whether candidate meets technical swing criteria:
    - Moving average alignment (Price > EMA 20, EMA 20 > EMA 50)
    - RSI momentum (in sweet spot, not severely overbought)
    - Proximity to 52W high or 20-day high breakout
    """
    price = candidate.get("price") or candidate.get("current_price") or 0.0
    ema_20 = candidate.get("ema_20")
    ema_50 = candidate.get("ema_50")
    ema_200 = candidate.get("ema_200")
    rsi = candidate.get("rsi")
    dist_52w = candidate.get("distance_52w_high_pct")
    breakout_20d = candidate.get("breakout_20d", False)

    tech_thresh = thresholds.get("technical", {})
    rsi_min = tech_thresh.get("rsi_min", 50.0)
    rsi_max = tech_thresh.get("rsi_max", 75.0)
    max_dist_52w = tech_thresh.get("proximity_52w_high_pct", 5.0)

    # 1. Trend alignment
    trend_aligned = False
    if ema_20 and ema_50:
        trend_aligned = price >= ema_20 and ema_20 >= ema_50
    elif ema_20:
        trend_aligned = price >= ema_20

    above_ema_200 = (price >= ema_200) if ema_200 else True

    # 2. RSI momentum
    rsi_in_range = (rsi_min <= rsi <= rsi_max) if rsi is not None else False

    # 3. Breakout or near high
    near_52w_high = (dist_52w is not None and dist_52w <= max_dist_52w)

    passed = (trend_aligned or breakout_20d or near_52w_high)

    return {
        "passed": passed,
        "trend_aligned": trend_aligned,
        "above_ema_200": above_ema_200,
        "rsi_in_range": rsi_in_range,
        "near_52w_high": near_52w_high,
        "breakout_20d": breakout_20d
    }
