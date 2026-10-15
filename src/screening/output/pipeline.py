"""Pipeline dispatcher feeding discovered NSE equity symbols to Agent 2 and Agent 3 with strict confirmation gating."""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from src.main import run_technical_analysis
from src.fundamental.main import run_fundamental_analysis

logger = logging.getLogger(__name__)


def evaluate_composite_verdict(
    agent_2_score: Optional[int] = None,
    agent_3_score: Optional[int] = None,
    daily_trend: Optional[str] = None,
    tech_status: Optional[str] = None,
    fund_status: Optional[str] = None,
    agent_1_score: Optional[int] = None,  # Kept as optional for backward compatibility
    *args,
    **kwargs
) -> Tuple[int, str, str]:
    """
    Evaluates multi-agent confirmation gates before issuing trade verdicts.
    Strict rule: Strong fundamentals must NEVER override clearly bearish technical conditions for a swing-trading BUY.
    
    Composite evaluation is derived strictly from Technical Analysis (Agent 2) and Fundamental Analysis (Agent 3),
    independent of any screening score or ranking.

    Returns:
        (composite_score, verdict, reason)
    """
    # Handle legacy positional calls: (agent_1_score, agent_2_score, agent_3_score, daily_trend, ...)
    if len(args) >= 2 and isinstance(agent_2_score, int) and isinstance(agent_3_score, int):
        # 3 initial integer arguments were passed positionally
        a2 = agent_3_score
        a3 = daily_trend if isinstance(daily_trend, int) else None
        trend = tech_status if isinstance(tech_status, str) else None
        t_status = fund_status if isinstance(fund_status, str) else None
        f_status = agent_1_score if isinstance(agent_1_score, str) else None
        agent_2_score = a2
        agent_3_score = a3
        daily_trend = trend
        tech_status = t_status
        fund_status = f_status

    valid_scores = [s for s in [agent_2_score, agent_3_score] if s is not None]
    composite_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else (agent_2_score or 0)

    # Gate 1: Insufficient technical data or technical execution failure
    if agent_2_score is None or tech_status in ["insufficient_data", "error"]:
        return composite_score, "INSUFFICIENT_DATA_HOLD", "Technical analysis data is unavailable or insufficient"

    # Gate 2: Clear Bearish Technical Trend or failing technical score (< 45)
    # Regardless of fundamentals, never recommend a swing-trading BUY on a bearish trend.
    if daily_trend == "bearish" or agent_2_score < 45:
        if agent_3_score is not None and agent_3_score >= 60:
            return (
                composite_score,
                "WATCHLIST_WAIT_FOR_SETUP",
                "Strong company fundamentals, but technical trend is bearish/failing. Wait for confirmed technical reversal."
            )
        else:
            return (
                composite_score,
                "REJECTED_BEARISH",
                "Technical trend is bearish and below viable swing parameters."
            )

    # Gate 3: Weak / Below-Threshold Technical Setup (< 55)
    if agent_2_score < 55:
        return (
            composite_score,
            "NOT_RECOMMENDED",
            f"Technical score ({agent_2_score}/100) is below the minimum required threshold (55) for trade entry."
        )

    # Gate 4: Technically Bullish but Fundamentally Distressed / Very Weak (< 40)
    if daily_trend == "bullish" and agent_2_score >= 65 and agent_3_score is not None and agent_3_score < 40:
        return (
            composite_score,
            "SPECULATIVE_TECHNICAL_ONLY",
            f"Strong technical momentum, but company fundamental health is poor ({agent_3_score}/100). Higher risk."
        )

    # Gate 5: Strong Buy Setup (Mutual Confirmation across Technical and Fundamental Engines)
    if (
        daily_trend == "bullish"
        and agent_2_score >= 65
        and (agent_3_score is not None and agent_3_score >= 60)
        and composite_score >= 65
    ):
        return (
            composite_score,
            "STRONG_BUY_CANDIDATE",
            "Mutual multi-agent confirmation: Confirmed bullish technical setup and solid fundamental quality."
        )

    # Gate 6: Moderate Buy Setup (Confirmed technical viability and adequate fundamental metrics)
    if (
        agent_2_score >= 55
        and daily_trend in ["bullish", "neutral"]
        and (agent_3_score is None or agent_3_score >= 45)
        and composite_score >= 55
    ):
        return (
            composite_score,
            "MODERATE_BUY_CANDIDATE",
            "Acceptable technical setup with supportive fundamental metrics."
        )

    # Default fallback
    return (
        composite_score,
        "NEUTRAL_WAIT",
        "Setup does not meet required entry thresholds across all agents."
    )


def pipe_to_agents(
    symbols_or_candidates: Union[List[str], List[Dict[str, Any]], Dict[str, Any]],
    max_symbols_to_analyze: Optional[int] = None,
    run_technical: bool = True,
    run_fundamental: bool = True,
    offline: bool = False,
    top_n: Optional[int] = None,  # Backward compatibility alias
    candidates: Optional[List[Any]] = None  # Backward compatibility keyword
) -> List[Dict[str, Any]]:
    """
    Takes discovered equity symbols from Agent 1 and evaluates them through:
    - Agent 2 (Technical Analysis Engine)
    - Agent 3 (Fundamental Analysis Engine)
    
    Selection policy is explicit and reproducible (first N discovered symbols).
    Returns combined evaluations with strictly gated composite verdicts.
    """
    raw_input = symbols_or_candidates if symbols_or_candidates is not None else candidates

    # Extract symbol strings from various input representations
    symbols: List[str] = []
    if isinstance(raw_input, dict) and "symbols" in raw_input:
        symbols = [str(s).strip().upper().replace(".NS", "") for s in raw_input["symbols"] if s]
    elif isinstance(raw_input, list):
        for item in raw_input:
            if isinstance(item, str):
                s = item.strip().upper().replace(".NS", "")
                if s:
                    symbols.append(s)
            elif isinstance(item, dict):
                s = str(item.get("symbol", "")).strip().upper().replace(".NS", "")
                if s:
                    symbols.append(s)

    # Deduplicate symbols preserving order
    clean_symbols: List[str] = []
    for s in symbols:
        if s and s not in clean_symbols:
            clean_symbols.append(s)

    limit = max_symbols_to_analyze if max_symbols_to_analyze is not None else (top_n or 10)
    selected_symbols = clean_symbols[:limit]

    combined_results: List[Dict[str, Any]] = []

    for sym in selected_symbols:
        result: Dict[str, Any] = {
            "symbol": sym,
            "agent_2_technical": None,
            "agent_3_fundamental": None,
            "agent_2_score": None,
            "agent_3_score": None,
            "composite_score": None,
            "composite_verdict": None,
            "verdict_reason": None
        }

        # Run Agent 2 (Technical)
        tech_res = None
        if run_technical:
            try:
                tech_res = run_technical_analysis(symbol=sym, offline=offline)
                result["agent_2_technical"] = tech_res
                result["agent_2_score"] = tech_res.get("technical_score")
            except Exception as e:
                logger.warning(f"Error running Agent 2 for {sym}: {e}")
                tech_res = {"status": "error", "error": str(e)}
                result["agent_2_technical"] = tech_res
                result["agent_2_score"] = None

        # Run Agent 3 (Fundamental)
        fund_res = None
        if run_fundamental:
            try:
                fund_res = run_fundamental_analysis(symbol=sym, offline=offline)
                result["agent_3_fundamental"] = fund_res
                result["agent_3_score"] = fund_res.get("fundamental_score")
            except Exception as e:
                logger.warning(f"Error running Agent 3 for {sym}: {e}")
                fund_res = {"status": "error", "error": str(e)}
                result["agent_3_fundamental"] = fund_res
                result["agent_3_score"] = None

        # Extract agent signals for gated composite evaluation
        a2 = result.get("agent_2_score")
        a3 = result.get("agent_3_score")
        daily_trend = tech_res.get("trend", {}).get("daily") if isinstance(tech_res, dict) else None
        tech_status = tech_res.get("status") if isinstance(tech_res, dict) else None
        fund_status = fund_res.get("status") if isinstance(fund_res, dict) else None

        composite_score, verdict, reason = evaluate_composite_verdict(
            agent_2_score=a2,
            agent_3_score=a3,
            daily_trend=daily_trend,
            tech_status=tech_status,
            fund_status=fund_status
        )

        result["composite_score"] = composite_score
        result["composite_verdict"] = verdict
        result["verdict_reason"] = reason

        combined_results.append(result)

    return combined_results
