"""Volume indicators: Relative volume (RVOL) and price-volume confirmation."""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def calculate_relative_volume(volume_series: pd.Series, lookback: int = 20) -> pd.Series:
    """
    Calculates Relative Volume (RVOL) = Current Volume / Average Volume over lookback periods.
    Note: The average volume excludes the current candle to avoid biasing the denominator.
    """
    avg_vol = volume_series.shift(1).rolling(window=lookback, min_periods=1).mean()
    rvol = volume_series / (avg_vol + 1e-10)
    return rvol


def add_volume_indicators(
    df: pd.DataFrame,
    lookback: int = 20,
    breakout_threshold: float = 1.5,
    expansion_threshold: float = 1.2,
    contraction_threshold: float = 0.8
) -> pd.DataFrame:
    """Appends volume indicators and confirmation signals."""
    res = df.copy()
    vol = res["volume"]

    res["vol_avg_20"] = vol.shift(1).rolling(window=lookback, min_periods=1).mean()
    res["rvol"] = calculate_relative_volume(vol, lookback=lookback)

    # Volume regimes
    res["volume_expansion"] = res["rvol"] >= expansion_threshold
    res["volume_contraction"] = res["rvol"] <= contraction_threshold
    res["breakout_volume"] = res["rvol"] >= breakout_threshold

    # Price-volume confirmation: price closed up with above-average volume (> 1.0)
    price_up = res["close"] > res["close"].shift(1)
    res["price_volume_confirmation"] = price_up & (res["rvol"] >= 1.0)

    return res
