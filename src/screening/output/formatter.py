"""Output formatters for Agent 1 — Market-Wide Stock Discovery Engine.

Conforms to Section 6 clean output contract:
- Primary output: eligible symbols collection (no scores or rankings).
- Separate operational metadata and discovery diagnostics.
"""

import sys
from typing import Dict, Any, List, Optional
from datetime import datetime


def format_screening_output(
    symbols: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    total_scanned: Optional[int] = None,
    universe_name: str = "broad_market",
    scan_timestamp: Optional[str] = None,
    market: str = "NSE",
    warnings: Optional[List[str]] = None,
    candidates: Optional[List[Any]] = None  # Legacy compatibility parameter
) -> Dict[str, Any]:
    """
    Constructs the canonical JSON output structure for Agent 1.
    Primary output is 'symbols', completely decoupled from ranking or scores.
    """
    if symbols is None:
        if candidates is not None:
            symbols = [
                c.get("symbol", "").upper().replace(".NS", "")
                if isinstance(c, dict) else str(c).upper().replace(".NS", "")
                for c in candidates
                if c
            ]
        else:
            symbols = []

    # Clean and deduplicate symbols preserving order
    clean_symbols: List[str] = []
    for s in symbols:
        sym = str(s).strip().upper().replace(".NS", "")
        if sym and sym not in clean_symbols:
            clean_symbols.append(sym)

    if scan_timestamp is None:
        scan_timestamp = datetime.now().isoformat()

    meta = dict(metadata or {})
    if "discovery_timestamp" not in meta:
        meta["discovery_timestamp"] = scan_timestamp
    if "total_eligible" not in meta:
        meta["total_eligible"] = len(clean_symbols)
    if "total_discovered" not in meta:
        meta["total_discovered"] = total_scanned or len(clean_symbols)
    if "coverage_status" not in meta:
        meta["coverage_status"] = "complete" if not meta.get("is_cached") else "cached"
    if "data_source" not in meta:
        meta["data_source"] = "NSE_OFFICIAL_EQUITY_MASTER"
    if warnings:
        meta["warnings"] = warnings

    output: Dict[str, Any] = {
        "status": "success",
        "market": market,
        "discovery_timestamp": scan_timestamp,
        "universe_mode": universe_name,
        "total_eligible": len(clean_symbols),
        "symbols": clean_symbols,
        "metadata": meta
    }

    # Maintain backward compatibility for legacy test harnesses expecting candidates field
    if candidates is not None or "candidates" in meta:
        output["candidates"] = [
            {"symbol": s, "suggested_action": "pass_to_agent_2_and_3"}
            for s in clean_symbols
        ]
        output["candidates_count"] = len(clean_symbols)
        output["total_scanned"] = meta.get("total_discovered", len(clean_symbols))

    return output


def format_screening_error(
    error_message: str,
    universe_name: str = "broad_market",
    market: str = "NSE"
) -> Dict[str, Any]:
    """Constructs diagnostic error output structure."""
    return {
        "status": "error",
        "market": market,
        "discovery_timestamp": datetime.now().isoformat(),
        "universe_mode": universe_name,
        "total_eligible": 0,
        "symbols": [],
        "metadata": {
            "coverage_status": "failed",
            "error": str(error_message)
        }
    }


def print_screening_summary_table(output_data: Dict[str, Any]) -> None:
    """Pretty-prints broad discovery diagnostics and eligible symbols preview to CLI."""
    symbols = output_data.get("symbols", [])
    if not symbols and "candidates" in output_data:
        symbols = [c.get("symbol", "") if isinstance(c, dict) else str(c) for c in output_data["candidates"]]

    meta = output_data.get("metadata", {})
    universe = output_data.get("universe_mode", output_data.get("universe", "broad_market"))
    total_disc = meta.get("total_discovered", len(symbols))
    total_elig = meta.get("total_eligible", len(symbols))
    source = meta.get("data_source", "NSE_EQUITY_MASTER")
    coverage = meta.get("coverage_status", "complete").upper()
    is_cached = meta.get("is_cached", False)
    last_refresh = meta.get("last_refresh") or meta.get("discovery_timestamp", "N/A")

    print("\n" + "=" * 90)
    print(f" AGENT 1 - STOCK DISCOVERY REPORT (Market-Wide NSE Universe)")
    print("=" * 90)
    print(f"  * Market           : {output_data.get('market', 'NSE')} (India)")
    print(f"  * Universe Mode    : {universe}")
    print(f"  * Data Source      : {source}")
    print(f"  * Coverage Status  : {coverage} {'(Cached)' if is_cached else ''}")
    print(f"  * Last Refreshed   : {last_refresh}")
    print(f"  * Total Discovered : {total_disc} securities")
    print(f"  * Total Eligible   : {total_elig} ordinary equities (Series: EQ, BE)")

    exclusions = meta.get("exclusion_reasons")
    if exclusions and isinstance(exclusions, dict):
        ex_parts = [f"{k}: {v}" for k, v in exclusions.items() if v > 0]
        if ex_parts:
            print(f"  * Exclusions       : {', '.join(ex_parts)}")

    warnings = meta.get("warnings") or output_data.get("warnings", [])
    if warnings:
        print("-" * 90)
        for w in warnings:
            print(f"  [!] NOTICE: {w}")

    print("-" * 90)
    if not symbols:
        print("  No eligible equity symbols discovered.")
        print("=" * 90 + "\n")
        return

    preview_limit = 40
    preview_syms = symbols[:preview_limit]
    print(f"  Eligible Equities Sample (showing {len(preview_syms)} of {len(symbols)}):")
    
    # Format symbols into clean lines of 8 symbols each
    chunk_size = 8
    for i in range(0, len(preview_syms), chunk_size):
        chunk = preview_syms[i:i + chunk_size]
        print("    " + "  ".join(f"{s:<10}" for s in chunk))

    if len(symbols) > preview_limit:
        print(f"    ... and {len(symbols) - preview_limit} more eligible equities ready for downstream analysis.")

    print("=" * 90 + "\n")
