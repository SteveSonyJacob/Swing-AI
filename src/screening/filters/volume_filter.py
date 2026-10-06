"""Volume screening filter for shockers and surges."""

from typing import Dict, Any


def evaluate_volume_criteria(candidate: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates candidate's volume expansion:
    - Relative volume vs 20-day SMA
    - Volume shocker tags from Moneycontrol or scanner
    """
    tags = candidate.get("tags", [])
    vol_ratio = candidate.get("volume_ratio")
    vol_thresh = thresholds.get("volume", {})
    surge_mult = vol_thresh.get("surge_multiplier", 1.3)
    shocker_mult = vol_thresh.get("shocker_multiplier", 2.0)

    is_shocker = "VOLUME_SHOCKER" in tags or (vol_ratio is not None and vol_ratio >= shocker_mult)
    is_surge = is_shocker or "VOLUME_SURGE" in tags or (vol_ratio is not None and vol_ratio >= surge_mult)

    return {
        "passed": is_surge or is_shocker,
        "is_volume_shocker": is_shocker,
        "is_volume_surge": is_surge,
        "volume_ratio": vol_ratio
    }
