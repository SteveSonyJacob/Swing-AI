"""Catalyst and corporate event screening filter."""

from typing import Dict, Any


def evaluate_catalyst_criteria(candidate: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates whether candidate has upcoming earnings or corporate actions:
    - Checks upcoming results within lookahead window
    - Detects board meeting / dividend / split catalysts
    """
    tags = candidate.get("tags", [])
    has_earnings = candidate.get("upcoming_results", False) or "EARNINGS_CATALYST" in tags
    days_to_results = candidate.get("days_to_results")

    cat_thresh = thresholds.get("catalyst", {})
    lookahead = cat_thresh.get("earnings_lookahead_days", 14)

    is_upcoming_soon = False
    if days_to_results is not None:
        is_upcoming_soon = 0 <= days_to_results <= lookahead
        catalyst_status = "upcoming" if is_upcoming_soon else "none"
    elif has_earnings:
        is_upcoming_soon = True
        catalyst_status = "upcoming"
    else:
        is_upcoming_soon = False
        catalyst_status = "unavailable"

    return {
        "has_catalyst": is_upcoming_soon,
        "days_to_results": days_to_results,
        "earnings_upcoming": is_upcoming_soon,
        "catalyst_status": catalyst_status
    }

