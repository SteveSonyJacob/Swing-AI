"""Master unified runner for SwingTrade AI multi-agent trading system.

Executes:
  - Agent 1: Stock Screening Engine (Momentum, RVOL, 52W Proximity, Liquidity)
  - Agent 2: Technical Swing Analysis Engine (EMAs, RSI, MACD, S/R, Risk Levels)
  - Agent 3: Fundamental Analysis Engine (Growth, ROE, Cash Flow, Valuation)
  - Decision Engine: Gated Composite Verdicts (Strong Buy, Moderate Buy, Watchlist, Speculative)
"""

import sys
import os
from pathlib import Path
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure safe UTF-8 output with replacement on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.screening.main import run_screening
from src.screening.output.formatter import print_screening_summary_table
from src.screening.output.pipeline import pipe_to_agents, evaluate_composite_verdict
from src.main import run_technical_analysis
from src.fundamental.main import run_fundamental_analysis

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")


def print_banner():
    banner = """
==========================================================================================
                 SWINGTRADE AI -- MULTI-AGENT TRADING ANALYSIS SYSTEM                    
             Agent 1 (Screening) | Agent 2 (Technical) | Agent 3 (Fundamental)            
==========================================================================================
"""
    print(banner.strip())


def print_single_stock_summary(symbol: str, res: Dict[str, Any]):
    sym = symbol.upper().replace(".NS", "")
    t = res.get("technical", {})
    f = res.get("fundamental", {})
    s = res.get("screening", {})

    print("\n" + "=" * 90)
    print(f" COMPREHENSIVE MULTI-AGENT REPORT: {sym}")
    print("=" * 90)

    # Verdict Box
    verdict = res.get("composite_verdict", "N/A")
    score = res.get("composite_score", "N/A")
    reason = res.get("verdict_reason", "")
    print(f"FINAL COMPOSITE VERDICT : {verdict} (Composite Score: {score}/100)")
    print(f"RATIONALE               : {reason}")
    print("-" * 90)

    # Scores
    a1_score = s.get("screening_score", "N/A")
    a2_score = t.get("technical_score", "N/A")
    a3_score = f.get("fundamental_score", "N/A")
    print(f"Agent Scores            : Screening: {a1_score}/100 | Technical: {a2_score}/100 | Fundamental: {a3_score}/100")

    # Technical Details
    print("\n[AGENT 2 - TECHNICAL SWING SETUP]")
    trend = t.get("trend", {})
    daily_trend = trend.get("daily", "N/A")
    hourly_trend = trend.get("hourly", "N/A")
    mom = t.get("momentum", {})
    rsi = mom.get("daily_rsi", "N/A")
    macd = mom.get("daily_macd", "N/A")
    vol = t.get("volume", {})
    rvol = vol.get("relative_volume", "N/A")
    levels = t.get("levels", {})
    sup = levels.get("support", "N/A")
    res_lvl = levels.get("resistance", "N/A")
    setup = t.get("trade_setup", {})

    print(f"  * Trend Alignment     : Daily: {daily_trend} | Hourly: {hourly_trend}")
    print(f"  * Momentum            : Daily RSI(14): {rsi} | MACD: {macd}")
    print(f"  * Volume Confirmation : RVOL: {rvol}x (Confirmed: {vol.get('confirmation', False)})")
    print(f"  * Support / Resist    : Support: {sup} | Resistance: {res_lvl}")
    print(f"  * Trade Setup         : Direction: {setup.get('direction', 'none').upper()}")
    print(f"    - Entry Zone        : {setup.get('entry_zone', 'N/A')}")
    print(f"    - Stop Loss         : {setup.get('stop_loss', 'N/A')}")
    print(f"    - Target 1 / 2      : {setup.get('target_1', 'N/A')} / {setup.get('target_2', 'N/A')}")
    print(f"    - Risk/Reward       : {setup.get('risk_reward', 'N/A')}")

    # Fundamental Details
    print("\n[AGENT 3 - FUNDAMENTAL QUALITY]")
    growth = f.get("growth", {})
    prof = f.get("profitability", {})
    bs = f.get("balance_sheet", {})
    val = f.get("valuation", {})
    own = f.get("ownership", {})

    print(f"  * Growth              : Revenue YoY: {growth.get('revenue_yoy')}% | PAT YoY: {growth.get('pat_yoy')}%")
    print(f"  * Profitability       : ROE: {prof.get('roe')}% | ROCE: {prof.get('roce')}% | Operating Margin: {prof.get('operating_margin')}%")
    if bs.get("is_financial"):
        print("  * Balance Sheet       : Financial Institution (Corporate D/E exempt)")
    else:
        print(f"  * Balance Sheet       : Debt/Equity: {bs.get('debt_equity')} | Current Ratio: {bs.get('current_ratio')} | Net Debt: {bs.get('net_debt')}")
    print(f"  * Valuation           : P/E: {val.get('pe')} (Sector: {val.get('sector_pe')}) | Assessment: {val.get('valuation_assessment')}")
    print(f"  * Ownership           : Promoters: {own.get('insider_holding')}% | Institutions: {own.get('institutional_holding')}%")

    if f.get("warnings"):
        print("\n[WARNINGS & RISKS]")
        for w in f["warnings"]:
            print(f"  [!] {w}")

    print("=" * 90 + "\n")


def run_pipeline(
    universe: str = "nifty50",
    symbols: Optional[List[str]] = None,
    top_n: int = 5,
    min_score: int = 50,
    offline: bool = False
) -> Dict[str, Any]:
    """Runs Agent 1 screening, forwards to Agent 2 and Agent 3, and generates composite verdicts."""
    screening_res = run_screening(
        universe=universe,
        source="all",
        min_score=min_score,
        top_n=top_n,
        offline=offline,
        custom_symbols=symbols
    )

    candidates = screening_res.get("candidates", [])
    pipeline_results = []
    if candidates:
        pipeline_results = pipe_to_agents(
            candidates=candidates,
            top_n=top_n,
            offline=offline
        )

    return {
        "status": "success",
        "market": "NSE",
        "execution_timestamp": datetime.now().isoformat(),
        "mode": "offline" if offline else "live",
        "screening": screening_res,
        "multi_agent_pipeline": pipeline_results
    }


def run_single_stock(symbol: str, offline: bool = False) -> Dict[str, Any]:
    """Runs all three agents on a specific stock symbol."""
    sym = symbol.strip().upper().replace(".NS", "")

    # 1. Screening evaluation
    screen_run = run_screening(
        universe="custom",
        source="all",
        min_score=0,
        top_n=1,
        offline=offline,
        custom_symbols=[sym]
    )
    screening_cand = screen_run["candidates"][0] if screen_run.get("candidates") else {}
    a1_score = screening_cand.get("screening_score", 50)

    # 2. Agent 2 Technical
    tech_res = run_technical_analysis(symbol=sym, offline=offline)
    a2_score = tech_res.get("technical_score")
    daily_trend = tech_res.get("trend", {}).get("daily")

    # 3. Agent 3 Fundamental
    fund_res = run_fundamental_analysis(symbol=sym, offline=offline)
    a3_score = fund_res.get("fundamental_score")

    # 4. Gated Composite Verdict
    comp_score, verdict, reason = evaluate_composite_verdict(
        agent_1_score=a1_score,
        agent_2_score=a2_score,
        agent_3_score=a3_score,
        daily_trend=daily_trend,
        tech_status=tech_res.get("status"),
        fund_status=fund_res.get("status")
    )

    return {
        "symbol": sym,
        "mode": "offline" if offline else "live",
        "composite_score": comp_score,
        "composite_verdict": verdict,
        "verdict_reason": reason,
        "screening": screening_cand,
        "technical": tech_res,
        "fundamental": fund_res
    }


def main():
    parser = argparse.ArgumentParser(
        description="SwingTrade AI: Unified Multi-Agent Runner (Agent 1 + Agent 2 + Agent 3)"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Analyze a specific single stock through all 3 agents (e.g. RELIANCE, TCS, TRENT)"
    )
    parser.add_argument(
        "--universe",
        type=str,
        default="nifty50",
        help="Universe preset: nifty50, nifty_next50, midcap_picks, or all (default: nifty50)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated custom symbols to scan (e.g. RELIANCE,TCS,TRENT,HAL,BEL)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of top candidates to evaluate through the pipeline (default: 5)"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=50,
        help="Minimum Agent 1 screening score (default: 50)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run offline using deterministic synthetic market data (no external APIs)"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output raw canonical JSON only to stdout"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Save complete analysis JSON to specified path"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run pytest automated test suite verification first"
    )

    args = parser.parse_args()

    # Optional test suite verification
    if args.test:
        import subprocess
        print("[*] Running automated test suite verification...")
        ret = subprocess.call([sys.executable, "-m", "pytest", "-q"])
        if ret != 0:
            print("[!] Tests failed. Aborting execution.")
            sys.exit(ret)
        print("[+] All unit and integration tests passed.\n")

    custom_syms = [s.strip().upper() for s in args.symbols.split(",")] if args.symbols else None

    # Single stock deep analysis
    if args.symbol:
        res = run_single_stock(args.symbol, offline=args.offline)
        if args.json_only:
            print(json.dumps(res, indent=2))
        else:
            print_banner()
            print_single_stock_summary(args.symbol, res)
        if args.output_file:
            out_p = Path(args.output_file)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            if not args.json_only:
                print(f"Results saved to: {out_p}")
        return

    # Full screening and pipeline execution
    results = run_pipeline(
        universe=args.universe,
        symbols=custom_syms,
        top_n=args.top_n,
        min_score=args.min_score,
        offline=args.offline
    )

    if args.json_only:
        print(json.dumps(results, indent=2))
    else:
        print_banner()
        print_screening_summary_table(results["screening"])

        pipeline_items = results.get("multi_agent_pipeline", [])
        if pipeline_items:
            print("\n" + "=" * 90)
            print(" MULTI-AGENT COMPOSITE VERDICTS (Agent 1 -> Agent 2 -> Agent 3)")
            print("=" * 90)
            print(f"{'Symbol':<12} {'A1 (Screen)':<12} {'A2 (Tech)':<12} {'A3 (Fund)':<12} {'Composite':<12} {'Verdict':<25}")
            print("-" * 90)
            for item in pipeline_items:
                sym = item["symbol"]
                a1 = f"{item['agent_1_score']}/100"
                a2 = f"{item.get('agent_2_score')}/100" if item.get('agent_2_score') is not None else "-"
                a3 = f"{item.get('agent_3_score')}/100" if item.get('agent_3_score') is not None else "-"
                comp = f"{item.get('composite_score')}/100"
                verdict = item.get("composite_verdict", "-")
                print(f"{sym:<12} {a1:<12} {a2:<12} {a3:<12} {comp:<12} {verdict:<25}")
            print("=" * 90)

            print("\n" + "=" * 90)
            print(" CONFIRMED TRADE SETUPS (Agent 2 Technical Execution Zones)")
            print("=" * 90)
            for item in pipeline_items:
                t = item.get("agent_2_technical") or {}
                setup = t.get("trade_setup") or {}
                direction = setup.get("direction", "none").upper()
                sym = item["symbol"]
                verdict = item.get("composite_verdict", "-")
                entry = setup.get("entry_zone", "N/A")
                stop = setup.get("stop_loss", "N/A")
                t1 = setup.get("target_1", "N/A")
                rr = setup.get("risk_reward", "N/A")
                reason = item.get("verdict_reason", "")
                print(f"[{sym}] Verdict: {verdict} | Action: {direction}")
                print(f"  Entry: {entry} | Stop: {stop} | Target 1: {t1} | R:R: {rr}")
                print(f"  Rationale: {reason}")
                print("-" * 90)
            print("=" * 90 + "\n")

    if args.output_file:
        out_p = Path(args.output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        if not args.json_only:
            print(f"Results saved to: {out_p}")


if __name__ == "__main__":
    main()
