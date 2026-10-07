"""Agent 3 — Fundamental Analysis Engine execution pipeline and CLI."""

import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime
from typing import Dict, Any, Optional
import yaml
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.fundamental.data.company_data import fetch_company_profile
from src.fundamental.data.financial_data import fetch_financial_statements
from src.fundamental.data.market_data import fetch_valuation_metrics
from src.fundamental.data.validator import FundamentalDataQuality
from src.fundamental.analysis.growth import analyze_growth
from src.fundamental.analysis.profitability import analyze_profitability
from src.fundamental.analysis.balance_sheet import analyze_balance_sheet
from src.fundamental.analysis.cash_flow import analyze_cash_flow
from src.fundamental.analysis.earnings_quality import analyze_earnings_quality
from src.fundamental.analysis.valuation import analyze_valuation
from src.fundamental.analysis.ownership import analyze_ownership
from src.fundamental.events.corporate_events import check_upcoming_results
from src.fundamental.scoring.fundamental_score import compute_fundamental_score
from src.fundamental.output.formatter import format_fundamental_output, format_fundamental_error
from src.fundamental.output.llm_explainer import generate_explanation_text


def load_fundamental_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads fundamental_settings.yaml."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "fundamental_settings.yaml"

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_fundamental_analysis(
    symbol: str,
    as_of_date: Optional[str] = None,
    offline: bool = False,
    market: str = "NSE",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes the end-to-end fundamental analysis pipeline for a company symbol.
    """
    if config is None:
        config = load_fundamental_config()

    weights = config.get("scoring", {}).get("weights")
    sector_benchmarks = config.get("sector_benchmarks", {})

    quality_tracker = FundamentalDataQuality()

    try:
        # 1. Company Profile
        profile = fetch_company_profile(symbol, offline=offline)
        sector = profile.get("sector", "Default")
        is_financial = sector.lower() in ["financial services", "banking", "finance", "bank"]

        # 2. Valuation & Market Multiples
        market_metrics = fetch_valuation_metrics(symbol, offline=offline)

        # 3. Financial Statements
        financials = fetch_financial_statements(symbol, as_of_date=as_of_date, offline=offline)
        q_is = financials.get("quarterly_is", {})
        q_bs = financials.get("quarterly_bs", {})
        q_cf = financials.get("quarterly_cf", {})
        a_is = financials.get("annual_is", {})
        a_bs = financials.get("annual_bs", {})
        a_cf = financials.get("annual_cf", {})

        if not q_is and not a_is:
            return format_fundamental_error(symbol, "No quarterly or annual income statements available")

        # 4. Growth Analysis
        growth = analyze_growth(q_is, a_is)
        for k, v in growth.items():
            quality_tracker.register(k, v)

        # 5. Profitability Analysis
        profitability = analyze_profitability(q_is, q_bs, a_is, a_bs)
        for k, v in profitability.items():
            if k != "margin_trend":
                quality_tracker.register(k, v)

        # 6. Balance Sheet Analysis
        balance_sheet = analyze_balance_sheet(q_is, q_bs, a_is, a_bs, is_financial=is_financial)
        for k, v in balance_sheet.items():
            if k != "is_financial":
                quality_tracker.register(k, v)

        # 7. Cash Flow Analysis with strict period matching
        cash_flow = analyze_cash_flow(q_cf, a_cf, quarterly_is=q_is, annual_is=a_is)
        quality_tracker.register("operating_cash_flow", cash_flow.get("operating_cash_flow"))
        quality_tracker.register("free_cash_flow", cash_flow.get("free_cash_flow"))
        quality_tracker.register("ocf_pat_ratio", cash_flow.get("ocf_pat_ratio"))

        # 8. Earnings Quality
        earnings_quality = analyze_earnings_quality(growth, cash_flow, balance_sheet, q_is, q_bs)

        # 9. Valuation vs Sector
        valuation = analyze_valuation(market_metrics, sector, sector_benchmarks)
        quality_tracker.register("pe", valuation.get("pe"))
        quality_tracker.register("pb", valuation.get("pb"))

        # 10. Ownership Analysis
        ownership = analyze_ownership(profile)

        # 11. Corporate Events
        events = check_upcoming_results(symbol, as_of_date=as_of_date)

        # 12. Scoring Engine
        scoring_res = compute_fundamental_score(
            growth_data=growth,
            profitability_data=profitability,
            balance_sheet_data=balance_sheet,
            cash_flow_data=cash_flow,
            earnings_quality_data=earnings_quality,
            valuation_data=valuation,
            weights=weights
        )

        fundamental_score = scoring_res["fundamental_score"]
        score_breakdown = scoring_res["score_breakdown"]

        # Aggregate warnings
        all_warnings = list(earnings_quality.get("warnings", []))
        if not is_financial and balance_sheet.get("debt_equity") and balance_sheet["debt_equity"] > 1.8:
            all_warnings.append("High debt-to-equity ratio")
        if valuation.get("valuation_assessment") == "expensive":
            all_warnings.append("Valuation is at a substantial premium to sector median")

        analysis_ts = datetime.now().isoformat()
        if as_of_date:
            analysis_ts = f"{as_of_date}T00:00:00"

        # 13. Format Canonical Output
        final_json = format_fundamental_output(
            symbol=symbol,
            market=market,
            analysis_timestamp=analysis_ts,
            fundamental_score=fundamental_score,
            score_breakdown=score_breakdown,
            growth=growth,
            profitability=profitability,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow,
            earnings_quality=earnings_quality,
            valuation=valuation,
            events=events,
            warnings=all_warnings,
            data_quality=quality_tracker.to_dict(),
            ownership=ownership
        )

        return final_json

    except Exception as e:
        return format_fundamental_error(symbol, str(e))


def main():
    parser = argparse.ArgumentParser(description="Agent 3 — Fundamental Analysis Engine")
    parser.add_argument("--symbol", type=str, required=True, help="Stock symbol (e.g. RELIANCE, TCS, INFY)")
    parser.add_argument("--date", type=str, default=None, help="Analysis as-of date (YYYY-MM-DD) for backtesting")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode using cached or synthetic data")
    parser.add_argument("--json-only", action="store_true", help="Output pure JSON to stdout")
    parser.add_argument("--explain", action="store_true", help="Print structured natural-language summary")
    parser.add_argument("--output", type=str, default=None, help="Save JSON output to specified file path")
    args = parser.parse_args()

    result = run_fundamental_analysis(
        symbol=args.symbol,
        as_of_date=args.date,
        offline=args.offline
    )

    json_str = json.dumps(result, indent=2)

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(json_str)

    if args.json_only:
        print(json_str)
    else:
        print("\n=======================================================")
        print(f" AGENT 3 - FUNDAMENTAL ANALYSIS: {result.get('symbol')} ({result.get('status')})")
        print("=======================================================")
        if result.get("status") == "success":
            print(f"Fundamental Score : {result.get('fundamental_score')}/100")
            print(f"Data Completeness : {result.get('data_quality', {}).get('status')}")
            print("\nScore Breakdown:")
            for k, v in result.get("score_breakdown", {}).items():
                print(f"  - {k:<20}: {v} pts")
            print("\nGrowth Metrics:")
            for k, v in result.get("growth", {}).items():
                print(f"  - {k:<20}: {v}")
            print("\nProfitability:")
            for k, v in result.get("profitability", {}).items():
                print(f"  - {k:<20}: {v}")
            print("\nBalance Sheet:")
            for k, v in result.get("balance_sheet", {}).items():
                print(f"  - {k:<20}: {v}")
            print("\nCash Flow:")
            for k, v in result.get("cash_flow", {}).items():
                print(f"  - {k:<20}: {v}")
            print("\nValuation:")
            for k, v in result.get("valuation", {}).items():
                print(f"  - {k:<20}: {v}")
            if result.get("warnings"):
                print("\nWarnings:")
                for w in result["warnings"]:
                    print(f"  [!] {w}")

            if args.explain:
                print("\n-------------------------------------------------------")
                print(" NATURAL LANGUAGE EXPLANATION")
                print("-------------------------------------------------------")
                print(generate_explanation_text(result))
        else:
            print(f"Reason: {result.get('reason')}")
        print("=======================================================\n")


if __name__ == "__main__":
    main()
