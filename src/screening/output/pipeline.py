"""Pipeline dispatcher feeding Agent 1 screened candidates to Agent 2 and Agent 3."""

import logging
from typing import Dict, Any, List, Optional
from src.main import run_technical_analysis
from src.fundamental.main import run_fundamental_analysis

logger = logging.getLogger(__name__)


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
    Returns combined evaluations.
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
            "composite_verdict": None
        }

        # Run Agent 2 (Technical)
        if run_technical:
            try:
                tech_res = run_technical_analysis(symbol=sym, offline=offline)
                result["agent_2_technical"] = tech_res
                result["agent_2_score"] = tech_res.get("technical_score")
            except Exception as e:
                logger.warning(f"Error running Agent 2 for {sym}: {e}")
                result["agent_2_technical"] = {"status": "error", "error": str(e)}
                result["agent_2_score"] = None

        # Run Agent 3 (Fundamental)
        if run_fundamental:
            try:
                fund_res = run_fundamental_analysis(symbol=sym, offline=offline)
                result["agent_3_fundamental"] = fund_res
                result["agent_3_score"] = fund_res.get("fundamental_score")
            except Exception as e:
                logger.warning(f"Error running Agent 3 for {sym}: {e}")
                result["agent_3_fundamental"] = {"status": "error", "error": str(e)}
                result["agent_3_score"] = None

        # Compute composite verdict
        a1 = result.get("agent_1_score", 0)
        a2 = result.get("agent_2_score")
        a3 = result.get("agent_3_score")

        valid_scores = [s for s in [a1, a2, a3] if s is not None]
        composite_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else a1

        if composite_score >= 75 and (a2 is None or a2 >= 60) and (a3 is None or a3 >= 60):
            verdict = "STRONG_BUY_CANDIDATE"
        elif composite_score >= 60:
            verdict = "MODERATE_BUY_CANDIDATE"
        else:
            verdict = "NEUTRAL_WAIT"

        result["composite_verdict"] = verdict
        result["composite_score"] = composite_score

        combined_results.append(result)

    return combined_results
