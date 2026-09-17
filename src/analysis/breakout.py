"""Breakout detection with look-ahead bias protection and volume confirmation."""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def detect_breakouts(
    df: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 50,
    volume_threshold: float = 1.5
) -> Dict[str, Any]:
    """
    Detects 20-day and 50-day price breakouts.
    Strictly excludes current candle to prevent look-ahead bias:
    previous_high = high.shift(1).rolling(window).max()
    """
    res = df.copy()
    high = res["high"]
    close = res["close"]
    rvol = res.get("rvol", pd.Series(1.0, index=res.index))

    # Rolling prior highs (shifted by 1)
    res[f"prior_{short_window}d_high"] = high.shift(1).rolling(short_window, min_periods=short_window).max()
    res[f"prior_{long_window}d_high"] = high.shift(1).rolling(long_window, min_periods=long_window).max()

    latest = res.iloc[-1]
    latest_close = float(latest["close"])
    latest_rvol = float(latest.get("rvol", 1.0))
    
    prior_short_high = latest[f"prior_{short_window}d_high"]
    prior_long_high = latest[f"prior_{long_window}d_high"]

    is_50d_breakout = False
    is_20d_breakout = False

    if not pd.isna(prior_long_high) and latest_close > prior_long_high:
        is_50d_breakout = True

    if not pd.isna(prior_short_high) and latest_close > prior_short_high:
        is_20d_breakout = True

    volume_confirmed = latest_rvol >= volume_threshold

    if is_50d_breakout:
        breakout_type = "50_day_high"
        detected = True
    elif is_20d_breakout:
        breakout_type = "20_day_high"
        detected = True
    else:
        breakout_type = "none"
        detected = False

    return {
        "detected": detected,
        "type": breakout_type,
        "volume_confirmed": volume_confirmed if detected else False,
        "prior_20d_high": round(float(prior_short_high), 2) if not pd.isna(prior_short_high) else None,
        "prior_50d_high": round(float(prior_long_high), 2) if not pd.isna(prior_long_high) else None,
        "current_close": round(latest_close, 2),
        "rvol": round(latest_rvol, 2)
    }
