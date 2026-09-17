"""JSON and structured output formatter conforming to plan.md Section 19 schema."""

from typing import Dict, Any, Optional
import json
from datetime import datetime


def format_agent_output(
    symbol: str,
    market: str,
    analysis_timestamp: str,
    technical_score: int,
    score_breakdown: Dict[str, int],
    daily_trend: Dict[str, Any],
    hourly_trend: Dict[str, Any],
    daily_momentum: Dict[str, Any],
    hourly_momentum: Dict[str, Any],
    volume_data: Dict[str, Any],
    breakout_data: Dict[str, Any],
    levels_data: Dict[str, Optional[float]],
    volatility_data: Dict[str, Any],
    relative_strength_data: Dict[str, Any],
    trade_setup_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Constructs the canonical JSON output defined in Section 19.
    """
    # Format momentum MACD states as "bullish" / "bearish"
    daily_macd_str = "bullish" if daily_momentum.get("macd_line", 0) > daily_momentum.get("macd_signal", 0) else "bearish"
    hourly_macd_str = "bullish" if hourly_momentum.get("macd_line", 0) > hourly_momentum.get("macd_signal", 0) else "bearish"

    output = {
        "status": "success",
        "symbol": symbol.upper().replace(".NS", ""),
        "market": market,
        "analysis_timestamp": analysis_timestamp,

        "technical_score": int(technical_score),

        "score_breakdown": {
            "daily_trend": int(score_breakdown.get("daily_trend", 0)),
            "hourly_trend": int(score_breakdown.get("hourly_trend", 0)),
            "momentum": int(score_breakdown.get("momentum", 0)),
            "volume": int(score_breakdown.get("volume", 0)),
            "breakout": int(score_breakdown.get("breakout", 0)),
            "support_resistance": int(score_breakdown.get("support_resistance", 0)),
            "relative_strength": int(score_breakdown.get("relative_strength", 0)),
            "volatility": int(score_breakdown.get("volatility", 0))
        },

        "trend": {
            "daily": str(daily_trend.get("trend", "neutral")),
            "hourly": str(hourly_trend.get("trend", "neutral")),
            "daily_ema_alignment": bool(daily_trend.get("ema_alignment", False)),
            "hourly_ema_alignment": bool(hourly_trend.get("ema_alignment", False)),
            "market_structure": str(daily_trend.get("market_structure", "mixed"))
        },

        "momentum": {
            "daily_rsi": round(float(daily_momentum.get("rsi", 50.0)), 1),
            "hourly_rsi": round(float(hourly_momentum.get("rsi", 50.0)), 1),
            "daily_macd": daily_macd_str,
            "hourly_macd": hourly_macd_str
        },

        "volume": {
            "relative_volume": round(float(volume_data.get("rvol", 1.0)), 2),
            "confirmation": bool(volume_data.get("price_volume_confirmation", False))
        },

        "breakout": {
            "detected": bool(breakout_data.get("detected", False)),
            "type": str(breakout_data.get("type", "none")),
            "volume_confirmed": bool(breakout_data.get("volume_confirmed", False))
        },

        "levels": {
            "support": levels_data.get("support"),
            "resistance": levels_data.get("resistance")
        },

        "volatility": {
            "atr_14": round(float(volatility_data.get("atr_14", 0.0)), 1),
            "atr_percent": round(float(volatility_data.get("atr_percent", 0.0)), 2)
        },

        "relative_strength": {
            "vs_nifty_1m": relative_strength_data.get("vs_nifty_1m"),
            "vs_sector_1m": relative_strength_data.get("vs_sector_1m")
        },

        "trade_setup": {
            "direction": trade_setup_data.get("direction", "long"),
            "entry_zone": trade_setup_data.get("entry_zone"),
            "stop_loss": trade_setup_data.get("stop_loss"),
            "target_1": trade_setup_data.get("target_1"),
            "target_2": trade_setup_data.get("target_2"),
            "risk_reward": trade_setup_data.get("risk_reward")
        }
    }

    return output


def format_error_output(symbol: str, reason: str, status: str = "insufficient_data") -> Dict[str, Any]:
    """Constructs the canonical error output defined in Section 6."""
    return {
        "status": status,
        "symbol": symbol.upper().replace(".NS", ""),
        "reason": reason
    }
