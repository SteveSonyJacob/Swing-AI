"""Technical scoring engine implementing the 100-point deterministic rubric."""

from typing import Dict, Any, Optional
import math
import numpy as np


def calculate_daily_trend_score(daily_analysis: Dict[str, Any], max_points: int = 20) -> int:
    """Daily trend scoring (up to 20 points)."""
    points = 0
    close = daily_analysis.get("close", 0.0)
    ema20 = daily_analysis.get("ema20", 0.0)
    ema50 = daily_analysis.get("ema50", 0.0)
    ema200 = daily_analysis.get("ema200", 0.0)
    ema20_slope = daily_analysis.get("ema20_slope", 0.0)
    ema50_slope = daily_analysis.get("ema50_slope", 0.0)
    structure = daily_analysis.get("market_structure", "")

    # Price > EMA20 (+4)
    if close > ema20:
        points += 4

    # EMA20 > EMA50 (+4)
    if ema20 > ema50:
        points += 4

    # EMA50 > EMA200 (+4)
    if ema50 > ema200:
        points += 4

    # Positive EMA slopes (+4: +2 for each)
    if ema20_slope > 0:
        points += 2
    if ema50_slope > 0:
        points += 2

    # Market structure (+4)
    if structure == "higher_highs_higher_lows":
        points += 4
    elif structure in ("higher_highs_lower_lows", "lower_highs_higher_lows"):
        points += 2

    return min(points, max_points)


def calculate_hourly_trend_score(hourly_analysis: Dict[str, Any], max_points: int = 15) -> int:
    """Hourly trend scoring (up to 15 points)."""
    points = 0
    close = hourly_analysis.get("close", 0.0)
    ema20 = hourly_analysis.get("ema20", 0.0)
    ema50 = hourly_analysis.get("ema50", 0.0)
    ema20_slope = hourly_analysis.get("ema20_slope", 0.0)
    structure = hourly_analysis.get("market_structure", "")

    # Price > EMA20 (+4)
    if close > ema20:
        points += 4

    # EMA20 > EMA50 (+4)
    if ema20 > ema50:
        points += 4

    # Positive slope (+3)
    if ema20_slope > 0:
        points += 3

    # Bullish structure (+4)
    if structure == "higher_highs_higher_lows":
        points += 4
    elif structure in ("higher_highs_lower_lows", "lower_highs_higher_lows"):
        points += 2

    return min(points, max_points)


def calculate_momentum_score(daily_indicators: Dict[str, Any], max_points: int = 15) -> int:
    """Momentum scoring (up to 15 points) based on RSI and MACD."""
    points = 0
    rsi = daily_indicators.get("rsi", 50.0)
    macd_line = daily_indicators.get("macd_line", 0.0)
    macd_signal = daily_indicators.get("macd_signal", 0.0)
    macd_hist = daily_indicators.get("macd_histogram", 0.0)
    crossover = daily_indicators.get("macd_bullish_crossover", False)

    # RSI (up to 7 points)
    if 60.0 <= rsi <= 70.0:
        points += 7
    elif 50.0 <= rsi < 60.0:
        points += 5
    elif rsi > 70.0:
        points += 4
    elif 30.0 <= rsi < 50.0:
        points += 2
    else:
        points += 0

    # MACD (up to 8 points)
    if macd_line > macd_signal:
        points += 4
    if macd_hist > 0:
        points += 2
    if crossover:
        points += 2

    return min(points, max_points)


def calculate_volume_score(volume_data: Dict[str, Any], max_points: int = 15) -> int:
    """Volume scoring (up to 15 points)."""
    points = 0
    rvol = volume_data.get("rvol", 1.0)
    expansion = volume_data.get("volume_expansion", False)
    confirmation = volume_data.get("price_volume_confirmation", False)

    # Relative volume points (up to 7)
    if rvol >= 2.0:
        points += 7
    elif rvol >= 1.5:
        points += 5
    elif rvol >= 1.2:
        points += 3
    elif rvol >= 1.0:
        points += 2

    # Volume expansion (+4)
    if expansion:
        points += 4

    # Price-volume confirmation (+4)
    if confirmation:
        points += 4

    return min(points, max_points)


def calculate_breakout_score(breakout_data: Dict[str, Any], max_points: int = 15) -> int:
    """Breakout scoring (up to 15 points)."""
    points = 0
    detected = breakout_data.get("detected", False)
    breakout_type = breakout_data.get("type", "none")
    volume_confirmed = breakout_data.get("volume_confirmed", False)

    if detected:
        if breakout_type == "50_day_high":
            points += 10
        elif breakout_type == "20_day_high":
            points += 7

        if volume_confirmed:
            points += 5

    return min(points, max_points)


def calculate_support_resistance_score(
    levels: Dict[str, Optional[float]],
    current_close: float,
    max_points: int = 10
) -> int:
    """Support & resistance quality score (up to 10 points)."""
    points = 0
    support = levels.get("support")
    resistance = levels.get("resistance")

    # Above confirmed support and reasonably close (+5)
    if support is not None and current_close >= support:
        dist_to_support = (current_close - support) / current_close
        if dist_to_support <= 0.08:  # within 8% of support
            points += 5
        else:
            points += 3

    # Room to resistance without immediate overhead ceiling (+5)
    if resistance is not None and resistance > current_close:
        dist_to_res = (resistance - current_close) / current_close
        if dist_to_res >= 0.03:  # at least 3% room to run
            points += 5
        else:
            points += 2
    elif resistance is None:
        # Blue sky / all-time highs
        points += 5

    return min(points, max_points)


def calculate_relative_strength_score(rs_data: Dict[str, Any], max_points: int = 5) -> int:
    """Relative strength score (up to 5 points)."""
    points = 0
    vs_nifty = rs_data.get("vs_nifty_1m")
    vs_sector = rs_data.get("vs_sector_1m")

    if vs_nifty is not None:
        if vs_nifty > 5.0:
            points += 3
        elif vs_nifty > 0.0:
            points += 2

    if vs_sector is not None:
        if vs_sector > 0.0:
            points += 2

    return min(points, max_points)


def calculate_volatility_score(atr_percent: float, max_points: int = 5) -> int:
    """Volatility & trade quality score (up to 5 points)."""
    if np.isnan(atr_percent) or atr_percent <= 0:
        return 0
    # Sweet spot for swing trading: 1.2% to 4.5% daily range
    if 1.2 <= atr_percent <= 4.5:
        return 5
    elif 0.8 <= atr_percent < 1.2:
        return 3
    elif 4.5 < atr_percent <= 6.5:
        return 3
    else:
        return 1


def categorize_score(score: int) -> str:
    """Maps numerical score to Section 17 categories."""
    if score < 30:
        return "weak"
    elif score < 50:
        return "neutral"
    elif score < 70:
        return "positive"
    elif score <= 85:
        return "strong"
    else:
        return "very_strong"


def compute_technical_score(
    daily_analysis: Dict[str, Any],
    hourly_analysis: Dict[str, Any],
    momentum_data: Dict[str, Any],
    volume_data: Dict[str, Any],
    breakout_data: Dict[str, Any],
    sr_levels: Dict[str, Optional[float]],
    rs_data: Dict[str, Any],
    atr_percent: float,
    weights: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """Computes total deterministic technical score and component breakdown."""
    if weights is None:
        weights = {
            "daily_trend": 20,
            "hourly_trend": 15,
            "momentum": 15,
            "volume": 15,
            "breakout": 15,
            "support_resistance": 10,
            "relative_strength": 5,
            "volatility": 5
        }

    daily_score = calculate_daily_trend_score(daily_analysis, weights["daily_trend"])
    hourly_score = calculate_hourly_trend_score(hourly_analysis, weights["hourly_trend"])
    mom_score = calculate_momentum_score(momentum_data, weights["momentum"])
    vol_score = calculate_volume_score(volume_data, weights["volume"])
    breakout_score = calculate_breakout_score(breakout_data, weights["breakout"])
    current_close = daily_analysis.get("close", 0.0)
    sr_score = calculate_support_resistance_score(sr_levels, current_close, weights["support_resistance"])
    rs_score = calculate_relative_strength_score(rs_data, weights["relative_strength"])
    volat_score = calculate_volatility_score(atr_percent, weights["volatility"])

    breakdown = {
        "daily_trend": daily_score,
        "hourly_trend": hourly_score,
        "momentum": mom_score,
        "volume": vol_score,
        "breakout": breakout_score,
        "support_resistance": sr_score,
        "relative_strength": rs_score,
        "volatility": volat_score
    }

    total_score = sum(breakdown.values())
    total_score = max(0, min(100, total_score))

    return {
        "technical_score": total_score,
        "category": categorize_score(total_score),
        "score_breakdown": breakdown
    }
