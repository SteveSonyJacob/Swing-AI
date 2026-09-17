"""Volatility indicators: True Range, ATR(14), and ATR%."""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def calculate_atr(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series]:
    """
    Calculates Average True Range (ATR) using Wilder's smoothing, and ATR%.
    """
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's smoothing for ATR: ewm with alpha=1/period
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    atr_percent = (atr / df["close"]) * 100.0

    return atr, atr_percent


def add_volatility_indicators(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Appends ATR and ATR% indicators to DataFrame."""
    res = df.copy()
    atr, atr_percent = calculate_atr(res, period=period)
    res[f"atr_{period}"] = atr
    res[f"atr_percent"] = atr_percent
    return res
