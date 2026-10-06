"""Agent 1 — Screening Agent execution pipeline and CLI."""

import sys
import os
from pathlib import Path
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import yaml

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.screening.sources.moneycontrol import fetch_moneycontrol_screeners
from src.screening.sources.yfinance_scanner import scan_yfinance_universe, clean_symbol
from src.screening.filters.technical_filter import evaluate_technical_criteria
from src.screening.filters.volume_filter import evaluate_volume_criteria
from src.screening.filters.liquidity_filter import evaluate_liquidity_criteria
from src.screening.filters.catalyst_filter import evaluate_catalyst_criteria
from src.screening.scoring.screening_score import compute_screening_score
from src.screening.output.formatter import (
    format_screening_output,
    format_screening_error,
    print_screening_summary_table
)
from src.screening.output.pipeline import pipe_to_agents

logger = logging.getLogger(__name__)


def load_screening_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads screening_settings.yaml."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "screening_settings.yaml"

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_screening(
    universe: str = "nifty50",
    source: str = "all",
    min_score: int = 50,
    top_n: int = 10,
    offline: bool = False,
    config: Optional[Dict[str, Any]] = None,
    custom_symbols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Executes the end-to-end Indian equity screening pipeline across
    Moneycontrol and yfinance.
    """
    if config is None:
        config = load_screening_config()

    weights = config.get("scoring", {}).get("weights")
    thresholds = config.get("thresholds", {})
    universes_cfg = config.get("universes", {})

    # Determine symbols for yfinance scan
    if custom_symbols:
        symbols_to_scan = [clean_symbol(s) for s in custom_symbols]
    elif universe == "all":
        symbols_to_scan = list(set(
            universes_cfg.get("nifty50", []) +
            universes_cfg.get("nifty_next50", []) +
            universes_cfg.get("midcap_picks", [])
        ))
    else:
        symbols_to_scan = universes_cfg.get(universe, universes_cfg.get("nifty50", []))

    all_candidates_by_sym: Dict[str, Dict[str, Any]] = {}
    total_scanned_count = 0

    # 1. Moneycontrol Screening
    if source in ["all", "moneycontrol"]:
        try:
            mc_candidates = fetch_moneycontrol_screeners(config=config, offline=offline)
            total_scanned_count += len(mc_candidates)
            for c in mc_candidates:
                sym = clean_symbol(c.get("symbol", ""))
                if not sym:
                    continue
                c["sources"] = ["moneycontrol"]
                all_candidates_by_sym[sym] = c
        except Exception as e:
            logger.warning(f"Error during Moneycontrol screening: {e}")

    # 2. yfinance Technical Scanning
    if source in ["all", "yfinance"]:
        try:
            # If Moneycontrol already ran, prioritize those symbols plus universe
            if source == "all" and all_candidates_by_sym:
                scan_list = list(set(symbols_to_scan + list(all_candidates_by_sym.keys())))
            else:
                scan_list = symbols_to_scan

            yf_candidates = scan_yfinance_universe(scan_list, config=config, offline=offline)
            total_scanned_count += len(scan_list)

            for yc in yf_candidates:
                sym = clean_symbol(yc.get("symbol", ""))
                if not sym:
                    continue

                if sym in all_candidates_by_sym:
                    # Merge data from both sources
                    existing = all_candidates_by_sym[sym]
                    merged_tags = list(set(existing.get("tags", []) + yc.get("tags", [])))
                    existing.update({
                        "ema_20": yc.get("ema_20"),
                        "ema_50": yc.get("ema_50"),
                        "ema_200": yc.get("ema_200"),
                        "rsi": yc.get("rsi"),
                        "volume_ratio": yc.get("volume_ratio"),
                        "avg_volume_20": yc.get("avg_volume_20"),
                        "high_52w": yc.get("high_52w"),
                        "distance_52w_high_pct": yc.get("distance_52w_high_pct"),
                        "breakout_20d": yc.get("breakout_20d", False),
                        "turnover_cr": yc.get("turnover_cr") or existing.get("turnover_cr"),
                        "tags": merged_tags
                    })
                    if "yfinance" not in existing.get("sources", []):
                        existing["sources"].append("yfinance")
                else:
                    yc["sources"] = ["yfinance"]
                    all_candidates_by_sym[sym] = yc
        except Exception as e:
            logger.warning(f"Error during yfinance screening: {e}")

    # 3. Apply Filters and Compute Scores
    scored_candidates: List[Dict[str, Any]] = []

    for sym, cand in all_candidates_by_sym.items():
        # Evaluate Liquidity
        liq_eval = evaluate_liquidity_criteria(cand, thresholds)
        if liq_eval["is_penny_stock"]:
            continue  # Exclude penny stocks outright

        # Compute Score
        score_data = compute_screening_score(cand, weights=weights, thresholds=thresholds)
        cand.update(score_data)

        # Minimum score filter
        if cand["screening_score"] >= min_score:
            scored_candidates.append(cand)

    # 4. Sort Candidates descending by score, then change_pct
    scored_candidates.sort(
        key=lambda x: (x.get("screening_score", 0), x.get("change_pct", 0.0) or 0.0),
        reverse=True
    )

    # 5. Take Top N
    top_candidates = scored_candidates[:top_n]

    return format_screening_output(
        candidates=top_candidates,
        total_scanned=max(total_scanned_count, len(all_candidates_by_sym)),
        universe_name=universe if not custom_symbols else "custom",
        scan_timestamp=datetime.now().isoformat(),
        market="NSE"
    )


def main():
    """Command-line interface for Agent 1 — Screening Agent."""
    parser = argparse.ArgumentParser(
        description="SwingTrade AI: Agent 1 — Screening Agent for Indian Equities (NSE)"
    )
    parser.add_argument(
        "--universe",
        type=str,
        default="nifty50",
        help="Universe preset: nifty50, nifty_next50, midcap_picks, or all (default: nifty50)"
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["all", "moneycontrol", "yfinance"],
        default="all",
        help="Data source: all, moneycontrol, or yfinance (default: all)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated custom symbols (e.g. RELIANCE,TCS,TRENT)"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=50,
        help="Minimum screening score to include (0-100, default: 50)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Maximum candidates to return (default: 10)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run offline using deterministic synthetic market data"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output raw canonical JSON only (suppresses table formatting)"
    )
    parser.add_argument(
        "--run-agents",
        action="store_true",
        help="Directly forward top screened candidates to Agent 2 and Agent 3"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Save JSON results to specified file path"
    )

    args = parser.parse_args()

    custom_syms = [s.strip().upper() for s in args.symbols.split(",")] if args.symbols else None

    # Run screening
    result = run_screening(
        universe=args.universe,
        source=args.source,
        min_score=args.min_score,
        top_n=args.top_n,
        offline=args.offline,
        custom_symbols=custom_syms
    )

    # Optional Multi-Agent Pipeline Dispatch
    if args.run_agents and result.get("candidates"):
        pipeline_results = pipe_to_agents(
            candidates=result["candidates"],
            top_n=min(args.top_n, 5),
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
            print(" MULTI-AGENT COMPOSITE VERDICTS (Agent 1 -> Agent 2 -> Agent 3)")
            print("=" * 90)
            print(f"{'Symbol':<12} {'A1 (Screen)':<12} {'A2 (Tech)':<12} {'A3 (Fund)':<12} {'Composite':<12} {'Verdict':<20}")
            print("-" * 90)
            for item in result["multi_agent_pipeline"]:
                sym = item["symbol"]
                a1 = f"{item['agent_1_score']}/100"
                a2 = f"{item.get('agent_2_score')}/100" if item.get('agent_2_score') is not None else "-"
                a3 = f"{item.get('agent_3_score')}/100" if item.get('agent_3_score') is not None else "-"
                comp = f"{item.get('composite_score')}/100"
                verdict = item.get("composite_verdict", "-")
                print(f"{sym:<12} {a1:<12} {a2:<12} {a3:<12} {comp:<12} {verdict:<20}")
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
