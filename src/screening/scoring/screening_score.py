"""Deterministic 0-100 candidate scoring engine for Agent 1."""

from typing import Dict, Any, List, Optional


def compute_screening_score(
    candidate: Dict[str, Any],
    weights: Optional[Dict[str, int]] = None,
    thresholds: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes a deterministic 0-100 screening score for an equity candidate.
    Returns:
    - screening_score: int (0 to 100)
    - score_breakdown: Dict with points per category
    - category: str (PRIME_SETUP, STRONG_CANDIDATE, WATCHLIST, WEAK)
    - tags: List[str] deduplicated tags
    """
    if weights is None:
        weights = {
            "trend": 25,
            "momentum_breakout": 25,
            "volume": 25,
            "liquidity": 15,
            "catalyst": 10
        }

    price = candidate.get("price") or candidate.get("current_price") or 0.0
    change_pct = candidate.get("change_pct") or 0.0
    ema_20 = candidate.get("ema_20")
    ema_50 = candidate.get("ema_50")
    ema_200 = candidate.get("ema_200")
    rsi = candidate.get("rsi")
    dist_52w = candidate.get("distance_52w_high_pct")
    breakout_20d = candidate.get("breakout_20d", False)
    vol_ratio = candidate.get("volume_ratio")
    volume = candidate.get("volume") or candidate.get("avg_volume_20") or 0
    turnover_cr = candidate.get("turnover_cr")
    days_to_results = candidate.get("days_to_results")
    tags = list(candidate.get("tags", []))

    # 1. Trend (max: weights['trend'], default 25)
    max_trend = weights.get("trend", 25)
    trend_pts = 0
    if ema_20 and ema_50:
        if price >= ema_50:
            trend_pts += 10
        if price >= ema_20:
            trend_pts += 8
        if ema_20 >= ema_50:
            trend_pts += 7
        if "BULLISH_TREND" not in tags and trend_pts >= 18:
            tags.append("BULLISH_TREND")
    elif ema_200 and price >= ema_200:
        trend_pts += 15
    else:
        # Fallback when technical EMAs not yet calculated (e.g., pure Moneycontrol screener)
        if change_pct >= 5.0:
            trend_pts += 20
        elif change_pct >= 2.0:
            trend_pts += 15
        elif change_pct > 0.0:
            trend_pts += 10
    trend_score = min(int(round((min(trend_pts, 25) / 25.0) * max_trend)), max_trend)

    # 2. Momentum & Breakout (max: weights['momentum_breakout'], default 25)
    max_mom = weights.get("momentum_breakout", 25)
    mom_pts = 0
    if "52W_HIGH" in tags or "52W_HIGH_BREAKOUT" in tags or (dist_52w is not None and dist_52w <= 3.0):
        mom_pts += 12
        if "52W_HIGH_BREAKOUT" not in tags:
            tags.append("52W_HIGH_BREAKOUT")
    elif dist_52w is not None and dist_52w <= 5.0:
        mom_pts += 6

    if breakout_20d or "20D_BREAKOUT" in tags:
        mom_pts += 8
        if "20D_BREAKOUT" not in tags:
            tags.append("20D_BREAKOUT")

    if rsi is not None:
        if 55.0 <= rsi <= 68.0:
            mom_pts += 5
            if "MOMENTUM_RSI" not in tags:
                tags.append("MOMENTUM_RSI")
        elif 50.0 <= rsi <= 75.0:
            mom_pts += 3

    if change_pct >= 4.0:
        mom_pts += 5
        if "TOP_GAINER" not in tags:
            tags.append("TOP_GAINER")

    mom_score = min(int(round((min(mom_pts, 25) / 25.0) * max_mom)), max_mom)

    # 3. Volume (max: weights['volume'], default 25)
    max_vol = weights.get("volume", 25)
    vol_pts = 0
    is_shocker = "VOLUME_SHOCKER" in tags or (vol_ratio is not None and vol_ratio >= 2.0)
    if is_shocker:
        vol_pts += 15
        if "VOLUME_SHOCKER" not in tags:
            tags.append("VOLUME_SHOCKER")
    elif vol_ratio is not None and vol_ratio >= 1.5:
        vol_pts += 10
        if "VOLUME_SURGE" not in tags:
            tags.append("VOLUME_SURGE")
    elif vol_ratio is not None and vol_ratio >= 1.2:
        vol_pts += 6
        if "VOLUME_SURGE" not in tags:
            tags.append("VOLUME_SURGE")

    if volume >= 1_000_000:
        vol_pts += 6
    elif volume >= 200_000:
        vol_pts += 4

    vol_score = min(int(round((min(vol_pts, 25) / 25.0) * max_vol)), max_vol)

    # 4. Liquidity & Quality (max: weights['liquidity'], default 15)
    max_liq = weights.get("liquidity", 15)
    liq_pts = 0
    if price < 20.0:
        liq_pts = 0  # Severe penalty for penny stocks
        tags.append("PENNY_STOCK_WARNING")
    else:
        if price >= 100.0:
            liq_pts += 5
        elif price >= 50.0:
            liq_pts += 3

        if turnover_cr is not None:
            if turnover_cr >= 20.0:
                liq_pts += 10
                if "HIGH_LIQUIDITY" not in tags:
                    tags.append("HIGH_LIQUIDITY")
            elif turnover_cr >= 5.0:
                liq_pts += 6
        elif volume >= 500_000:
            liq_pts += 7
        else:
            liq_pts += 4
    liq_score = min(int(round((min(liq_pts, 15) / 15.0) * max_liq)), max_liq)

    # 5. Catalyst Presence (max: weights['catalyst'], default 10)
    max_cat = weights.get("catalyst", 10)
    cat_pts = 0
    catalyst_status = candidate.get("catalyst_status")
    if days_to_results is not None and 0 <= days_to_results <= 14:
        cat_pts += 10
        catalyst_status = "upcoming"
        if "EARNINGS_CATALYST" not in tags:
            tags.append("EARNINGS_CATALYST")
    elif "EARNINGS_CATALYST" in tags:
        cat_pts += 10
        catalyst_status = "upcoming"
    elif "TOP_ACTIVE" in tags:
        cat_pts += 5
        if not catalyst_status:
            catalyst_status = "active_market"
    else:
        if not catalyst_status:
            catalyst_status = "unavailable"

    cat_score = min(int(round((min(cat_pts, 10) / 10.0) * max_cat)), max_cat)

    total_score = trend_score + mom_score + vol_score + liq_score + cat_score
    final_score = max(0, min(100, int(round(total_score))))

    if final_score >= 85:
        category = "PRIME_SETUP"
    elif final_score >= 70:
        category = "STRONG_CANDIDATE"
    elif final_score >= 50:
        category = "WATCHLIST"
    else:
        category = "WEAK"

    # Deduplicate tags preserving order
    clean_tags: List[str] = []
    for t in tags:
        if t not in clean_tags:
            clean_tags.append(t)

    return {
        "screening_score": final_score,
        "score_breakdown": {
            "trend": trend_score,
            "momentum_breakout": mom_score,
            "volume": vol_score,
            "liquidity": liq_score,
            "catalyst": cat_score
        },
        "category": category,
        "tags": clean_tags,
        "catalyst_status": catalyst_status
    }
