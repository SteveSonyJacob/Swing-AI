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
from src.decision.engine import evaluate_decision

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
    action = res.get("action", "N/A")
    confidence = res.get("confidence", "N/A")
    print(f"FINAL DECISION VERDICT  : {verdict} (Score: {score}/100 | Action: {action} | Confidence: {confidence})")
    print(f"RATIONALE               : {reason}")
    print("-" * 90)

    # Decision Engine 5-Dimension Scoring Rubrics
    rubrics = res.get("scoring_rubrics") or {}
    if rubrics:
        print("\n[DECISION ENGINE - 100-POINT SCORING RUBRICS]")
        names = {
            "technical_alignment": "1. Technical Foundation & Trend Alignment",
            "fundamental_quality": "2. Fundamental Quality & Growth Safety",
            "momentum_volume": "3. Momentum & Volume Institutional Surge",
            "risk_reward": "4. Risk-to-Reward Setup & Asymmetry",
            "valuation_catalyst": "5. Valuation Multiple & Catalyst Conviction"
        }
        for k, v in rubrics.items():
            title = names.get(k, k.replace('_', ' ').title())
            score_str = f"{v.get('score', 0)}/{v.get('max_points', 0)} pts ({v.get('percentage', 0)}%)"
            print(f"  * {title:<48} : {score_str}")
            for d in v.get("details", [])[:2]:
                print(f"      - {d}")

    # Execution Plan & Sizing
    plan = res.get("execution_plan") or {}
    if plan:
        print("\n[DECISION ENGINE - EXECUTION PLAN & RISK ALLOCATION]")
        print(f"  * Recommended Action  : {plan.get('action', 'N/A')} (Direction: {plan.get('direction', 'NONE')})")
        print(f"  * Capital Allocation  : {plan.get('position_sizing', 'N/A')}")
        print(f"  * Execution Range     : Entry: {plan.get('entry_zone', 'N/A')} | Stop: {plan.get('stop_loss', 'N/A')} | Target: {plan.get('target_1', 'N/A')} | R:R: {plan.get('risk_reward', 'N/A')}")

    # Status & Scores
    sc = res.get("screening", {})
    sc_status = "Eligible (NSE)" if sc.get("eligible") else "Unverified"
    a2_score = t.get("technical_score", "N/A")
    a3_score = f.get("fundamental_score", "N/A")
    print(f"\nAgent Evaluations       : Discovery: {sc_status} | Technical: {a2_score}/100 | Fundamental: {a3_score}/100")

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
    universe: str = "broad_market",
    symbols: Optional[List[str]] = None,
    max_symbols: int = 10,
    top_n: Optional[int] = None,
    refresh_universe: bool = False,
    offline: bool = False,
    enable_llm: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """Runs Agent 1 broad discovery, forwards eligible symbols to Agent 2 and Agent 3, and generates composite verdicts."""
    limit = top_n if top_n is not None else max_symbols
    screening_res = run_screening(
        universe=universe,
        offline=offline,
        custom_symbols=symbols,
        refresh_universe=refresh_universe,
        enable_llm=enable_llm
    )

    discovered_symbols = screening_res.get("symbols", [])
    pipeline_results = []
    if discovered_symbols:
        pipeline_results = pipe_to_agents(
            symbols_or_candidates=discovered_symbols,
            max_symbols_to_analyze=limit,
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


def run_single_stock(symbol: str, offline: bool = False, enable_llm: bool = False) -> Dict[str, Any]:
    """Runs all three agents and Decision Engine on a specific stock symbol."""
    sym = symbol.strip().upper().replace(".NS", "")

    # 1. Agent 1: Screening discovery verification
    screen_run = run_screening(
        universe="custom",
        offline=offline,
        custom_symbols=[sym],
        enable_llm=enable_llm
    )
    is_discovered = sym in screen_run.get("symbols", [])

    # 2. Agent 2: Technical Analysis
    tech_res = run_technical_analysis(symbol=sym, offline=offline)

    # 3. Agent 3: Fundamental Analysis
    fund_res = run_fundamental_analysis(symbol=sym, offline=offline)

    # 4. Decision Engine (5-Dimension Rubrics, Confirmation Gating & Execution Plan)
    decision = evaluate_decision(
        technical_data=tech_res,
        fundamental_data=fund_res,
        screening_data=screen_run,
        symbol=sym
    )

    return {
        "symbol": sym,
        "mode": "offline" if offline else "live",
        "composite_score": decision.get("composite_score"),
        "composite_verdict": decision.get("composite_verdict"),
        "verdict_reason": decision.get("verdict_reason"),
        "decision_score": decision.get("decision_score"),
        "action": decision.get("action"),
        "confidence": decision.get("confidence"),
        "scoring_rubrics": decision.get("scoring_rubrics"),
        "execution_plan": decision.get("execution_plan"),
        "confirmation_checks": decision.get("confirmation_checks"),
        "decision_engine": decision,
        "screening": {
            "eligible": is_discovered,
            "status": "discovered" if is_discovered else "not_found",
            "metadata": screen_run.get("metadata", {})
        },
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
        default="broad_market",
        help="Universe mode: broad_market (all NSE equities) or optional preset (default: broad_market)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated custom symbols to scan (e.g. RELIANCE,TCS,TRENT,HAL,BEL)"
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=10,
        help="Maximum number of discovered candidates to analyze through downstream agents (default: 10)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Alias for --max-symbols (backward compatibility)"
    )
    parser.add_argument(
        "--refresh-universe",
        action="store_true",
        help="Force re-fetch official NSE security master equity list from exchange archives"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=None,
        help="Deprecated: Agent 1 does not score or rank stocks"
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
        "--llm",
        action="store_true",
        help="Enable AI qualitative news and catalyst analysis for screened candidates"
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
    analysis_limit = args.top_n if args.top_n is not None else args.max_symbols

    # Single stock deep analysis
    if args.symbol:
        res = run_single_stock(args.symbol, offline=args.offline, enable_llm=args.llm)
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
        max_symbols=analysis_limit,
        refresh_universe=args.refresh_universe,
        offline=args.offline,
        enable_llm=args.llm
    )

    if args.json_only:
        print(json.dumps(results, indent=2))
    else:
        print_banner()
        print_screening_summary_table(results["screening"])

        pipeline_items = results.get("multi_agent_pipeline", [])
        if pipeline_items:
            print("\n" + "=" * 95)
            print(" MULTI-AGENT DECISION ENGINE VERDICTS (Agent 1 -> Agent 2 -> Agent 3 -> Decision Engine)")
            print("=" * 95)
            print(f"{'Symbol':<12} {'Discovery':<12} {'A2 (Tech)':<10} {'A3 (Fund)':<10} {'Score':<10} {'Action':<8} {'Verdict':<26} {'Conf':<6}")
            print("-" * 95)
            for item in pipeline_items:
                sym = item["symbol"]
                disc = "Eligible"
                a2 = f"{item.get('agent_2_score')}/100" if item.get('agent_2_score') is not None else "-"
                a3 = f"{item.get('agent_3_score')}/100" if item.get('agent_3_score') is not None else "-"
                comp = f"{item.get('composite_score')}/100" if item.get('composite_score') is not None else "-"
                act = item.get("action", "-")
                conf = item.get("confidence", "-")
                verdict = item.get("composite_verdict", "-")
                print(f"{sym:<12} {disc:<12} {a2:<10} {a3:<10} {comp:<10} {act:<8} {verdict:<26} {conf:<6}")
            print("=" * 95)

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
