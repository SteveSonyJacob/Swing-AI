"""Ownership and shareholding pattern analysis."""

from typing import Dict, Any, Optional


def analyze_ownership(info_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyzes institutional and insider ownership percentages if available."""
    if info_dict is None:
        return {
            "insider_holding": None,
            "institutional_holding": None,
            "ownership_trend": "stable"
        }

    held_insiders = info_dict.get("heldPercentInsiders")
    held_institutions = info_dict.get("heldPercentInstitutions")

    if held_insiders is not None and held_insiders <= 1.0:
        held_insiders = round(held_insiders * 100.0, 2)
    if held_institutions is not None and held_institutions <= 1.0:
        held_institutions = round(held_institutions * 100.0, 2)

    return {
        "insider_holding": held_insiders,
        "institutional_holding": held_institutions,
        "ownership_trend": "stable"
    }
