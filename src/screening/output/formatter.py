"""JSON and CLI table output formatters for Agent 1 — Screening Agent."""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime


def format_screening_output(
    candidates: List[Dict[str, Any]],
    total_scanned: int,
    universe_name: str,
    scan_timestamp: Optional[str] = None,
    market: str = "NSE"
) -> Dict[str, Any]:
    """
    Constructs the canonical JSON output structure for Agent 1.
    """
    if scan_timestamp is None:
        scan_timestamp = datetime.now().isoformat()

    formatted_candidates: List[Dict[str, Any]] = []

    for c in candidates:
        price = c.get("current_price") or c.get("price")
        formatted_c = {
            "symbol": str(c.get("symbol", "")).upper().replace(".NS", ""),
            "name": str(c.get("name", c.get("symbol", ""))),
            "current_price": round(float(price), 2) if price is not None else None,
            "change_pct": round(float(c.get("change_pct", 0.0)), 2) if c.get("change_pct") is not None else None,
            "screening_score": int(c.get("screening_score", 0)),
            "category": str(c.get("category", "WATCHLIST")),
            "score_breakdown": c.get("score_breakdown", {}),
            "tags": c.get("tags", []),
            "source": c.get("sources", [c.get("screener_source", "unknown")]),
            "metrics": {
                "volume_ratio": c.get("volume_ratio"),
                "rsi": c.get("rsi"),
                "distance_52w_high_pct": c.get("distance_52w_high_pct"),
                "breakout_20d": c.get("breakout_20d", False),
                "turnover_cr": c.get("turnover_cr"),
                "days_to_results": c.get("days_to_results")
            },
            "suggested_action": "pass_to_agent_2_and_3"
        }
        formatted_candidates.append(formatted_c)

    return {
        "status": "success",
        "market": market,
        "scan_timestamp": scan_timestamp,
        "universe": universe_name,
        "total_scanned": total_scanned,
        "candidates_count": len(formatted_candidates),
        "candidates": formatted_candidates
    }


def format_screening_error(error_message: str, universe_name: str = "unknown", market: str = "NSE") -> Dict[str, Any]:
    """Constructs error output structure."""
    return {
        "status": "error",
        "market": market,
        "scan_timestamp": datetime.now().isoformat(),
        "universe": universe_name,
        "total_scanned": 0,
        "candidates_count": 0,
        "candidates": [],
        "error": str(error_message)
    }


def print_screening_summary_table(output_data: Dict[str, Any]) -> None:
    """Pretty-prints candidates in a clean CLI table format."""
    candidates = output_data.get("candidates", [])
    universe = output_data.get("universe", "unknown")
    total = output_data.get("total_scanned", 0)

    print("\n" + "=" * 90)
    print(f" AGENT 1 - SCREENING AGENT REPORT | Universe: {universe} | Scanned: {total} stocks")
    print("=" * 90)

    if not candidates:
        print("  No candidate stocks met the minimum screening criteria.")
        print("=" * 90 + "\n")
        return

    # Header
    header = f"{'Symbol':<12} {'Price (INR)':<10} {'Chg %':<8} {'Score':<7} {'Category':<16} {'Tags':<35}"
    print(header)
    print("-" * 90)

    for c in candidates:
        sym = c.get("symbol", "")
        price = f"{c.get('current_price', 0.0):.2f}" if c.get("current_price") else "-"
        chg = f"{c.get('change_pct', 0.0):+.2f}%" if c.get("change_pct") is not None else "-"
        score = f"{c.get('screening_score', 0)}/100"
        cat = c.get("category", "")
        tags = ", ".join(c.get("tags", [])[:3])
        print(f"{sym:<12} {price:<10} {chg:<8} {score:<7} {cat:<16} {tags:<35}")

    print("=" * 90 + "\n")
