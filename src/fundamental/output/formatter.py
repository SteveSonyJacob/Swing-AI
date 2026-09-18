"""Canonical JSON output formatter conforming to Section 23 of plan.md."""

from typing import Dict, Any, List, Optional
import json


def format_fundamental_output(
    symbol: str,
    market: str,
    analysis_timestamp: str,
    fundamental_score: int,
    score_breakdown: Dict[str, int],
    growth: Dict[str, Any],
    profitability: Dict[str, Any],
    balance_sheet: Dict[str, Any],
    cash_flow: Dict[str, Any],
    earnings_quality: Dict[str, Any],
    valuation: Dict[str, Any],
    events: Dict[str, Any],
    warnings: List[str],
    data_quality: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Constructs the canonical JSON output dictionary matching Section 23.
    """
    output = {
        "status": "success",
        "symbol": symbol.upper().replace(".NS", ""),
        "market": market,
        "analysis_timestamp": analysis_timestamp,

        "fundamental_score": int(fundamental_score),

        "score_breakdown": {
            "growth": int(score_breakdown.get("growth", 0)),
            "profitability": int(score_breakdown.get("profitability", 0)),
            "balance_sheet": int(score_breakdown.get("balance_sheet", 0)),
            "cash_flow": int(score_breakdown.get("cash_flow", 0)),
            "earnings_quality": int(score_breakdown.get("earnings_quality", 0)),
            "valuation": int(score_breakdown.get("valuation", 0)),
            "consistency": int(score_breakdown.get("consistency", 0)),
            "sector_relative": int(score_breakdown.get("sector_relative", 0))
        },

        "growth": {
            "revenue_yoy": growth.get("revenue_yoy"),
            "pat_yoy": growth.get("pat_yoy"),
            "eps_yoy": growth.get("eps_yoy"),
            "revenue_cagr_3y": growth.get("revenue_cagr_3y"),
            "pat_cagr_3y": growth.get("pat_cagr_3y")
        },

        "profitability": {
            "roe": profitability.get("roe"),
            "roce": profitability.get("roce"),
            "operating_margin": profitability.get("operating_margin"),
            "net_margin": profitability.get("net_margin"),
            "margin_trend": str(profitability.get("margin_trend", "stable"))
        },

        "balance_sheet": {
            "debt_equity": balance_sheet.get("debt_equity"),
            "net_debt": balance_sheet.get("net_debt"),
            "interest_coverage": balance_sheet.get("interest_coverage"),
            "current_ratio": balance_sheet.get("current_ratio")
        },

        "cash_flow": {
            "operating_cash_flow": cash_flow.get("operating_cash_flow"),
            "free_cash_flow": cash_flow.get("free_cash_flow"),
            "ocf_pat_ratio": cash_flow.get("ocf_pat_ratio"),
            "cash_flow_trend": str(cash_flow.get("cash_flow_trend", "moderate"))
        },

        "earnings_quality": {
            "score": int(earnings_quality.get("score", 0)),
            "status": str(earnings_quality.get("status", "moderate")),
            "warnings": list(earnings_quality.get("warnings", []))
        },

        "valuation": {
            "pe": valuation.get("pe"),
            "pb": valuation.get("pb"),
            "ev_ebitda": valuation.get("ev_ebitda"),
            "sector_pe": valuation.get("sector_pe"),
            "pe_premium_to_sector": valuation.get("pe_premium_to_sector"),
            "valuation_assessment": str(valuation.get("valuation_assessment", "fair"))
        },

        "events": {
            "upcoming_results": bool(events.get("upcoming_results", False)),
            "days_to_results": events.get("days_to_results")
        },

        "warnings": list(warnings),

        "data_quality": {
            "status": str(data_quality.get("status", "complete")),
            "missing_metrics": list(data_quality.get("missing_metrics", []))
        }
    }

    return output


def format_fundamental_error(symbol: str, reason: str, status: str = "insufficient_data") -> Dict[str, Any]:
    """Constructs canonical error output."""
    return {
        "status": status,
        "symbol": symbol.upper().replace(".NS", ""),
        "reason": reason
    }
