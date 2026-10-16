"""Pipeline dispatcher feeding discovered NSE equity symbols to Agent 2 and Agent 3 with strict confirmation gating."""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from src.main import run_technical_analysis
from src.fundamental.main import run_fundamental_analysis

logger = logging.getLogger(__name__)


from src.decision.engine import evaluate_composite_verdict as engine_composite_verdict, evaluate_decision


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
    return engine_composite_verdict(
        agent_2_score=agent_2_score,
        agent_3_score=agent_3_score,
        daily_trend=daily_trend,
        tech_status=tech_status,
        fund_status=fund_status,
        agent_1_score=agent_1_score,
        *args,
        **kwargs
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
    - Decision Engine (5-Dimension Scoring Rubrics & Confirmation Gating)
    
    Selection policy is explicit and reproducible (first N discovered symbols).
    Returns combined evaluations with strictly gated composite verdicts and execution plans.
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
            "verdict_reason": None,
            "action": None,
            "confidence": None,
            "scoring_rubrics": None,
            "execution_plan": None,
            "confirmation_checks": None,
            "decision_engine": None
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

        # Execute Decision Engine with 5-dimension scoring rubrics & confirmation gating
        decision = evaluate_decision(
            technical_data=tech_res,
            fundamental_data=fund_res,
            symbol=sym
        )

        result["decision_engine"] = decision
        result["composite_score"] = decision.get("composite_score")
        result["composite_verdict"] = decision.get("composite_verdict")
        result["verdict_reason"] = decision.get("verdict_reason")
        result["action"] = decision.get("action")
        result["confidence"] = decision.get("confidence")
        result["scoring_rubrics"] = decision.get("scoring_rubrics")
        result["execution_plan"] = decision.get("execution_plan")
        result["confirmation_checks"] = decision.get("confirmation_checks")

        combined_results.append(result)

    return combined_results
