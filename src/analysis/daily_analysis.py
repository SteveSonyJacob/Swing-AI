"""Daily trend and market structure analysis."""

from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np


def detect_swing_pivots(df: pd.DataFrame, window: int = 5) -> Tuple[List[float], List[float]]:
    """
    Detects confirmed swing highs and swing lows using a rolling window.
    Only confirmed pivots (at least window periods ago) are returned to prevent look-ahead bias.
    """
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)
    
    swing_highs = []
    swing_lows = []
    
    for i in range(window, n - window):
        # Check if i is local maximum in [i-window, i+window]
        is_high = True
        for j in range(i - window, i + window + 1):
            if j != i and highs[j] >= highs[i]:
                is_high = False
                break
        if is_high:
            swing_highs.append(float(highs[i]))
            
        # Check if i is local minimum in [i-window, i+window]
        is_low = True
        for j in range(i - window, i + window + 1):
            if j != i and lows[j] <= lows[i]:
                is_low = False
                break
        if is_low:
            swing_lows.append(float(lows[i]))

    return swing_highs, swing_lows


def determine_market_structure(df: pd.DataFrame, window: int = 4) -> str:
    """
    Determines market structure (higher_highs_higher_lows, lower_highs_lower_lows, or mixed).
    """
    swing_highs, swing_lows = detect_swing_pivots(df, window=window)
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        # Fallback: compare 20-day vs 50-day rolling highs/lows
        recent_high = df["high"].iloc[-20:].max()
        prior_high = df["high"].iloc[-40:-20].max() if len(df) >= 40 else recent_high
        recent_low = df["low"].iloc[-20:].min()
        prior_low = df["low"].iloc[-40:-20].min() if len(df) >= 40 else recent_low
        
        if recent_high > prior_high and recent_low > prior_low:
            return "higher_highs_higher_lows"
        elif recent_high < prior_high and recent_low < prior_low:
            return "lower_highs_lower_lows"
        return "mixed"

    hh = swing_highs[-1] > swing_highs[-2]
    hl = swing_lows[-1] > swing_lows[-2]
    lh = swing_highs[-1] < swing_highs[-2]
    ll = swing_lows[-1] < swing_lows[-2]

    if hh and hl:
        return "higher_highs_higher_lows"
    elif lh and ll:
        return "lower_highs_lower_lows"
    elif hh and not hl:
        return "higher_highs_lower_lows"
    elif not hh and hl:
        return "lower_highs_higher_lows"
    else:
        return "mixed"


def analyze_daily_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs daily trend analysis:
    - EMA alignment (20 > 50 > 200 or 20 < 50 < 200)
    - EMA slopes
    - Market structure
    - Overall daily trend classification: bullish, bearish, neutral, mixed
    """
    latest = df.iloc[-1]
    close = float(latest["close"])
    ema20 = float(latest["ema_20"])
    ema50 = float(latest["ema_50"])
    ema200 = float(latest["ema_200"])
    
    ema20_slope = float(latest.get("ema_20_slope", 0.0))
    ema50_slope = float(latest.get("ema_50_slope", 0.0))

    bullish_alignment = (close > ema20) and (ema20 > ema50) and (ema50 > ema200)
    bearish_alignment = (close < ema20) and (ema20 < ema50) and (ema50 < ema200)

    structure = determine_market_structure(df)

    if bullish_alignment and ema20_slope > 0:
        trend = "bullish"
    elif bearish_alignment and ema20_slope < 0:
        trend = "bearish"
    elif close > ema200 and ema20 > ema50:
        trend = "bullish" if structure == "higher_highs_higher_lows" else "mixed"
    elif close < ema200 and ema20 < ema50:
        trend = "bearish" if structure == "lower_highs_lower_lows" else "mixed"
    else:
        trend = "neutral" if abs(ema20_slope) < 0.002 else "mixed"

    return {
        "trend": trend,
        "ema_alignment": bool(bullish_alignment),
        "ema20_slope": round(ema20_slope, 4),
        "ema50_slope": round(ema50_slope, 4),
        "market_structure": structure,
        "close": close,
        "ema20": round(ema20, 2),
        "ema50": round(ema50, 2),
        "ema200": round(ema200, 2)
    }
