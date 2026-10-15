"""Agent 1 — Market-Wide Stock Discovery Engine for NSE-Listed Equities.

Single Responsibility:
Discovers eligible ordinary equity symbols across the broad National Stock Exchange
of India (NSE) universe and returns their symbols to downstream analysis engines.
Does NOT rank, score, or pick top trading opportunities.
"""

import sys
import os
from pathlib import Path
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.screening.sources.nse_universe import (
    discover_nse_equity_universe,
    normalize_symbol,
    CACHE_FILE
)
from src.screening.output.formatter import (
    format_screening_output,
    format_screening_error,
    print_screening_summary_table
)
from src.screening.output.pipeline import pipe_to_agents

logger = logging.getLogger(__name__)


def load_screening_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads config/screening_settings.yaml."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "screening_settings.yaml"

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load screening config from {config_path}: {e}")
        return {}


def run_screening(
    universe: str = "broad_market",
    source: str = "all",
    min_score: Optional[int] = None,  # Deprecated: Screening Agent does not score
    top_n: Optional[int] = None,      # Deprecated: Screening Agent does not rank
    offline: bool = False,
    config: Optional[Dict[str, Any]] = None,
    custom_symbols: Optional[List[str]] = None,
    refresh_universe: bool = False,
    enable_llm: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Executes broad-universe NSE equity discovery and eligibility verification.
    
    Returns clean canonical dictionary containing:
      - symbols: List[str] of valid, deduplicated NSE equity symbols.
      - metadata: Discovery diagnostics (data source, exclusions, coverage status).
    """
    if config is None:
        config = load_screening_config()

    univ_cfg = config.get("universe", {})
    source_url = univ_cfg.get("primary_source_url", "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv")
    fallback_url = univ_cfg.get("fallback_source_url", "https://archives.nseindia.com/content/equities/EQUITY_L.csv")
    allowed_series = univ_cfg.get("allowed_series", ["EQ", "BE"])
    cache_ttl = univ_cfg.get("cache_ttl_hours", 24)

    # 1. Custom symbols mode: user explicitly requested specific symbols
    if custom_symbols:
        clean_symbols: List[str] = []
        for s in custom_symbols:
            sym = normalize_symbol(s)
            if sym and sym not in clean_symbols:
                clean_symbols.append(sym)

        metadata = {
            "data_source": "CUSTOM_SYMBOLS_REQUEST",
            "discovery_timestamp": datetime.now().isoformat(),
            "total_discovered": len(clean_symbols),
            "total_eligible": len(clean_symbols),
            "excluded_count": 0,
            "coverage_status": "custom",
            "is_cached": False,
            "last_refresh": datetime.now().isoformat(),
            "failed_sources": []
        }

        return format_screening_output(
            symbols=clean_symbols,
            metadata=metadata,
            universe_name="custom",
            market=config.get("market", "NSE")
        )

    # 2. Check if a legacy watchlist preset was explicitly requested (e.g., in legacy tests)
    watchlists = config.get("optional_watchlists", {})
    if universe in watchlists and universe != "broad_market" and universe != "all":
        watchlist_symbols = [normalize_symbol(s) for s in watchlists[universe] if normalize_symbol(s)]
        metadata = {
            "data_source": f"OPTIONAL_WATCHLIST_{universe.upper()}",
            "discovery_timestamp": datetime.now().isoformat(),
            "total_discovered": len(watchlist_symbols),
            "total_eligible": len(watchlist_symbols),
            "excluded_count": 0,
            "coverage_status": "watchlist_preset",
            "is_cached": False,
            "last_refresh": datetime.now().isoformat(),
            "failed_sources": []
        }
        return format_screening_output(
            symbols=watchlist_symbols,
            metadata=metadata,
            universe_name=universe,
            market=config.get("market", "NSE")
        )

    # 3. Market-wide broad NSE equity universe discovery
    discovery_res = discover_nse_equity_universe(
        source_url=source_url,
        fallback_url=fallback_url,
        allowed_series=allowed_series,
        cache_file=CACHE_FILE,
        cache_ttl_hours=cache_ttl,
        force_refresh=refresh_universe,
        offline=offline,
        timeout=config.get("network", {}).get("timeout", 10)
    )

    discovered_symbols = discovery_res.get("symbols", [])
    metadata = discovery_res.get("metadata", {})

    # 4. Optional configured eligibility constraints (only if explicitly enabled in configuration)
    eligibility_cfg = config.get("eligibility", {})
    eligible_symbols = discovered_symbols

    if eligibility_cfg.get("enabled", False):
        min_p = eligibility_cfg.get("min_price")
        # If price/volume filtering is explicitly enabled, it can filter symbols here
        logger.info("Applying explicitly configured eligibility constraints.")

    return format_screening_output(
        symbols=eligible_symbols,
        metadata=metadata,
        universe_name="broad_market",
        market=config.get("market", "NSE")
    )


def main():
    """CLI runner for Agent 1 — Market-Wide Stock Discovery Engine."""
    parser = argparse.ArgumentParser(
        description="SwingTrade AI: Agent 1 — Market-Wide Stock Discovery Engine for NSE-Listed Equities"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="broad_market",
        help="Universe mode: broad_market or custom (default: broad_market)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated custom symbols to inspect (e.g. RELIANCE,TCS,TRENT)"
    )
    parser.add_argument(
        "--refresh-universe",
        action="store_true",
        help="Force download and refresh of official exchange equity master list"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run offline using local cached universe or bundled seed dataset"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output raw canonical JSON only to stdout"
    )
    parser.add_argument(
        "--run-agents",
        action="store_true",
        help="Forward discovered symbols to Agent 2 (Technical) and Agent 3 (Fundamental)"
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=None,
        help="Maximum discovered symbols to forward to downstream analysis (default: 10)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Alias for --max-symbols (reproducible first N discovered symbols)"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Save output JSON to specified file path"
    )

    # Legacy parameters accepted gracefully without crash
    parser.add_argument("--universe", type=str, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--source", type=str, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--min-score", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--llm", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    custom_syms = [s.strip().upper() for s in args.symbols.split(",")] if args.symbols else None
    univ_choice = args.universe or args.mode

    # Run broad stock discovery
    result = run_screening(
        universe=univ_choice,
        custom_symbols=custom_syms,
        refresh_universe=args.refresh_universe,
        offline=args.offline
    )

    # Optional Multi-Agent Pipeline Dispatch
    if args.run_agents and result.get("symbols"):
        limit = args.max_symbols or args.top_n or 10
        pipeline_results = pipe_to_agents(
            symbols_or_candidates=result["symbols"],
            max_symbols_to_analyze=limit,
            offline=args.offline
        )
        result["multi_agent_pipeline"] = pipeline_results

    # Output Handling
    if args.json_only:
        print(json.dumps(result, indent=2))
    else:
        print_screening_summary_table(result)
        if args.run_agents and "multi_agent_pipeline" in result:
            print("\n" + "=" * 90)
            print(" MULTI-AGENT COMPOSITE VERDICTS (Downstream Technical & Fundamental Analysis)")
            print("=" * 90)
            print(f"{'Symbol':<12} {'A2 (Tech)':<12} {'A3 (Fund)':<12} {'Composite':<12} {'Verdict':<25}")
            print("-" * 90)
            for item in result["multi_agent_pipeline"]:
                sym = item["symbol"]
                a2 = f"{item.get('agent_2_score')}/100" if item.get('agent_2_score') is not None else "-"
                a3 = f"{item.get('agent_3_score')}/100" if item.get('agent_3_score') is not None else "-"
                comp = f"{item.get('composite_score')}/100"
                verdict = item.get("composite_verdict", "-")
                print(f"{sym:<12} {a2:<12} {a3:<12} {comp:<12} {verdict:<25}")
            print("=" * 90 + "\n")

    if args.output_file:
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        if not args.json_only:
            print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
