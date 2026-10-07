"""Pipeline dispatcher feeding Agent 1 screened candidates to Agent 2 and Agent 3 with strict confirmation gating."""

import logging
from typing import Dict, Any, List, Optional, Tuple
from src.main import run_technical_analysis
from src.fundamental.main import run_fundamental_analysis

logger = logging.getLogger(__name__)


def evaluate_composite_verdict(
    agent_1_score: int,
    agent_2_score: Optional[int],
    agent_3_score: Optional[int],
    daily_trend: Optional[str] = None,
    tech_status: Optional[str] = None,
    fund_status: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Evaluates multi-agent confirmation gates before issuing trade verdicts.
    Strict rule: Strong fundamentals must NEVER override clearly bearish technical conditions for a swing-trading BUY.

    Returns:
        (composite_score, verdict, reason)
    """
    valid_scores = [s for s in [agent_1_score, agent_2_score, agent_3_score] if s is not None]
    composite_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else agent_1_score

    # Gate 1: Insufficient technical data or technical execution failure
    if agent_2_score is None or tech_status in ["insufficient_data", "error"]:
        return composite_score, "INSUFFICIENT_DATA_HOLD", "Technical analysis data is unavailable or insufficient"

    # Gate 2: Clear Bearish Technical Trend or failing technical score (< 45)
    # Regardless of fundamentals or screening scores, never recommend a swing-trading BUY.
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

    # Gate 5: Strong Buy Setup (Mutual Confirmation across all 3 Agents)
    if (
        daily_trend == "bullish"
        and agent_2_score >= 65
        and agent_1_score >= 65
        and (agent_3_score is not None and agent_3_score >= 60)
        and composite_score >= 70
    ):
        return (
            composite_score,
            "STRONG_BUY_CANDIDATE",
            "Mutual multi-agent confirmation: High screening momentum, confirmed bullish technical setup, and solid fundamental quality."
        )

    # Gate 6: Moderate Buy Setup (Confirmed technical viability and adequate composite score)
    if (
        agent_2_score >= 55
        and daily_trend in ["bullish", "neutral"]
        and agent_1_score >= 50
        and (agent_3_score is None or agent_3_score >= 45)
        and composite_score >= 58
    ):
        return (
            composite_score,
            "MODERATE_BUY_CANDIDATE",
            "Acceptable technical setup with supportive screening/fundamental metrics."
        )

    # Default fallback
    return (
        composite_score,
        "NEUTRAL_WAIT",
        "Setup does not meet required entry thresholds across all agents."
    )


def pipe_to_agents(
    candidates: List[Dict[str, Any]],
    top_n: int = 3,
    run_technical: bool = True,
    run_fundamental: bool = True,
    offline: bool = False
) -> List[Dict[str, Any]]:
    """
    Takes top screened candidates from Agent 1 and evaluates them through:
    - Agent 2 (Technical Analysis Engine)
    - Agent 3 (Fundamental Analysis Engine)
    Returns combined evaluations with strictly gated composite verdicts.
    """
    combined_results: List[Dict[str, Any]] = []
    selected = candidates[:top_n]

    for cand in selected:
        sym = cand.get("symbol", "").upper().replace(".NS", "")
        if not sym:
            continue

        result: Dict[str, Any] = {
            "symbol": sym,
            "screening_candidate": cand,
            "agent_1_score": cand.get("screening_score", 0),
            "agent_2_technical": None,
            "agent_3_fundamental": None,
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
        a1 = result.get("agent_1_score", 0)
        a2 = result.get("agent_2_score")
        a3 = result.get("agent_3_score")
        daily_trend = tech_res.get("trend", {}).get("daily") if isinstance(tech_res, dict) else None
        tech_status = tech_res.get("status") if isinstance(tech_res, dict) else None
        fund_status = fund_res.get("status") if isinstance(fund_res, dict) else None

        composite_score, verdict, reason = evaluate_composite_verdict(
            agent_1_score=a1,
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
