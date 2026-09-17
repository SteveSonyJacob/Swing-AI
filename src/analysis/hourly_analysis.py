"""Hourly trend analysis and multi-timeframe confirmation."""

from typing import Dict, Any, Optional
import pandas as pd
from src.analysis.daily_analysis import determine_market_structure


def analyze_hourly_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs hourly trend analysis:
    - EMA alignment (EMA 20, 50, and 200 if enough candles exist, else 20 & 50)
    - Slopes
    - Trend classification
    """
    latest = df.iloc[-1]
    close = float(latest["close"])
    ema20 = float(latest["ema_20"])
    ema50 = float(latest["ema_50"])
    has_ema200 = "ema_200" in latest and not pd.isna(latest["ema_200"])
    ema200 = float(latest["ema_200"]) if has_ema200 else ema50

    ema20_slope = float(latest.get("ema_20_slope", 0.0))
    ema50_slope = float(latest.get("ema_50_slope", 0.0))

    if has_ema200:
        bullish_alignment = (close > ema20) and (ema20 > ema50) and (ema50 > ema200)
        bearish_alignment = (close < ema20) and (ema20 < ema50) and (ema50 < ema200)
    else:
        bullish_alignment = (close > ema20) and (ema20 > ema50)
        bearish_alignment = (close < ema20) and (ema20 < ema50)

    structure = determine_market_structure(df, window=3)

    if bullish_alignment and ema20_slope > 0:
        trend = "bullish"
    elif bearish_alignment and ema20_slope < 0:
        trend = "bearish"
    elif close > ema50 and ema20_slope >= 0:
        trend = "bullish"
    elif close < ema50 and ema20_slope <= 0:
        trend = "bearish"
    else:
        trend = "mixed"

    return {
        "trend": trend,
        "ema_alignment": bool(bullish_alignment),
        "ema20_slope": round(ema20_slope, 4),
        "ema50_slope": round(ema50_slope, 4),
        "market_structure": structure,
        "close": close,
        "ema20": round(ema20, 2),
        "ema50": round(ema50, 2)
    }
