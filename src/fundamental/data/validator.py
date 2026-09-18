"""Data validation and quality assessment for fundamental data."""

from typing import Dict, Any, List, Optional, Tuple


class FundamentalDataQuality:
    """Tracks available vs missing metrics and overall data completeness."""
    def __init__(self):
        self.missing_metrics: List[str] = []
        self.available_metrics: List[str] = []

    def register(self, name: str, value: Any):
        if value is None:
            self.missing_metrics.append(name)
        else:
            self.available_metrics.append(name)

    @property
    def status(self) -> str:
        if not self.available_metrics:
            return "insufficient"
        if not self.missing_metrics:
            return "complete"
        return "partial"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "missing_metrics": sorted(list(set(self.missing_metrics)))
        }
