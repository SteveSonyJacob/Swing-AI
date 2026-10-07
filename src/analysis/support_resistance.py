"""Support and resistance identification from swing pivots and rolling extremes."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from src.analysis.daily_analysis import detect_swing_pivots


def identify_key_levels(df: pd.DataFrame, window: int = 5) -> Dict[str, Optional[float]]:
    """
    Identifies the nearest confirmed support below current price and nearest resistance above current price.
    Uses swing pivots and rolling 20/50 day extremes.
    """
    latest_close = float(df["close"].iloc[-1])
    
    # Confirmed swing points
    swing_highs, swing_lows = detect_swing_pivots(df, window=window)
    
    # Rolling extremes (shifted 1 period)
    high_20 = float(df["high"].shift(1).rolling(20, min_periods=5).max().iloc[-1])
    low_20 = float(df["low"].shift(1).rolling(20, min_periods=5).min().iloc[-1])
    high_50 = float(df["high"].shift(1).rolling(50, min_periods=10).max().iloc[-1])
    low_50 = float(df["low"].shift(1).rolling(50, min_periods=10).min().iloc[-1])

    resistance_candidates = [p for p in swing_highs if p > latest_close]
    if not np.isnan(high_20) and high_20 > latest_close:
        resistance_candidates.append(high_20)
    if not np.isnan(high_50) and high_50 > latest_close:
        resistance_candidates.append(high_50)

    support_candidates = [p for p in swing_lows if p < latest_close]
    if not np.isnan(low_20) and low_20 < latest_close:
        support_candidates.append(low_20)
    if not np.isnan(low_50) and low_50 < latest_close:
        support_candidates.append(low_50)

    # Nearest resistance is minimum candidate above current price
    nearest_resistance = min(resistance_candidates) if resistance_candidates else None
    # Nearest support is maximum candidate below current price
    nearest_support = max(support_candidates) if support_candidates else None

    # Fallback to recent low/high if candidates empty, strictly excluding active candle
    if nearest_support is None and len(df) >= 20:
        prior_lows = df["low"].iloc[-21:-1] if len(df) >= 21 else df["low"].iloc[:-1]
        if not prior_lows.empty:
            candidate = float(prior_lows.min())
            if candidate < latest_close:
                nearest_support = candidate

    if nearest_resistance is None and len(df) >= 20:
        prior_highs = df["high"].iloc[-21:-1] if len(df) >= 21 else df["high"].iloc[:-1]
        if not prior_highs.empty:
            candidate = float(prior_highs.max())
            if candidate > latest_close:
                nearest_resistance = candidate

    return {
        "support": round(nearest_support, 2) if nearest_support is not None else None,
        "resistance": round(nearest_resistance, 2) if nearest_resistance is not None else None
    }
