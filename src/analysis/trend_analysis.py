"""Multi-timeframe trend synthesis."""

from typing import Dict, Any


def evaluate_trend_confirmation(daily_trend: str, hourly_trend: str) -> Dict[str, Any]:
    """
    Evaluates multi-timeframe trend alignment and confirmation.
    """
    if daily_trend == "bullish" and hourly_trend == "bullish":
        confirmation = "bullish_confirmation"
        aligned = True
    elif daily_trend == "bearish" and hourly_trend == "bearish":
        confirmation = "bearish_confirmation"
        aligned = True
    elif daily_trend == "bullish" and hourly_trend == "bearish":
        confirmation = "short_term_pullback"
        aligned = False
    elif daily_trend == "bearish" and hourly_trend == "bullish":
        confirmation = "short_term_countertrend"
        aligned = False
    else:
        confirmation = "unconfirmed_or_mixed"
        aligned = False

    return {
        "daily": daily_trend,
        "hourly": hourly_trend,
        "confirmation_status": confirmation,
        "aligned": aligned
    }
