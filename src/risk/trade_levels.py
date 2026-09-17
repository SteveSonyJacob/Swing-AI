"""Risk management and trade setup level calculations."""

from typing import Dict, Any, Optional
import numpy as np


def calculate_trade_levels(
    current_close: float,
    atr: float,
    levels: Dict[str, Optional[float]],
    trend: str,
    stop_atr_multiplier: float = 1.5,
    min_score_for_setup: int = 50,
    technical_score: int = 0
) -> Dict[str, Any]:
    """
    Calculates trade setup levels for bullish setups:
    - Entry zone
    - Stop loss
    - Target 1
    - Target 2
    - Risk/Reward ratio
    If setup is not bullish, trend is bearish, or data is insufficient, returns nulls.
    """
    default_setup = {
        "direction": "long" if trend in ("bullish", "neutral") else "none",
        "entry_zone": None,
        "stop_loss": None,
        "target_1": None,
        "target_2": None,
        "risk_reward": None
    }

    # Only generate trade setups when technical score and trend warrant a long setup
    if trend not in ("bullish", "positive") or technical_score < min_score_for_setup:
        return default_setup

    if atr is None or np.isnan(atr) or atr <= 0 or current_close <= 0:
        return default_setup

    entry = current_close
    entry_low = round(entry * 0.995, 2)
    entry_high = round(entry * 1.005, 2)
    entry_zone_str = f"{entry_low} - {entry_high}"

    # Stop loss based on 1.5 * ATR
    atr_stop = entry - (stop_atr_multiplier * atr)
    
    # If a nearby support exists just below entry (within 2 * ATR), we can place stop just below support
    support = levels.get("support")
    if support is not None and (entry - support) <= (2.0 * atr) and support < entry:
        stop_loss = min(atr_stop, support - (0.2 * atr))
    else:
        stop_loss = atr_stop

    stop_loss = round(stop_loss, 2)
    risk = entry - stop_loss
    if risk <= 0:
        return default_setup

    # Target 1: nearby resistance if at least 1.5 * risk away, otherwise entry + 1.5 * risk
    resistance = levels.get("resistance")
    if resistance is not None and resistance > entry and (resistance - entry) >= (1.2 * risk):
        target_1 = round(resistance, 2)
    else:
        target_1 = round(entry + (1.5 * risk), 2)

    # Target 2: entry + 2.5 * risk (or 2x resistance level)
    target_2 = round(entry + (2.5 * risk), 2)

    reward = target_1 - entry
    risk_reward = round(reward / risk, 2) if risk > 0 else None

    return {
        "direction": "long",
        "entry_zone": entry_zone_str,
        "stop_loss": stop_loss,
        "target_1": target_1,
        "target_2": target_2,
        "risk_reward": risk_reward
    }
