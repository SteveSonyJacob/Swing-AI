"""Decision Engine package for SwingTrade AI.

Synthesizes Agent 2 (Technical) and Agent 3 (Fundamental) through a structured
100-point scoring rubric, enforces strict confirmation gating, and produces
concrete execution parameters.
"""

from src.decision.rubrics import (
    score_technical_alignment,
    score_fundamental_quality,
    score_momentum_volume,
    score_risk_reward,
    score_valuation_catalyst,
    calculate_rubric_composite
)
from src.decision.engine import (
    DecisionEngine,
    evaluate_decision,
    evaluate_composite_verdict,
    load_decision_config
)

__all__ = [
    "DecisionEngine",
    "evaluate_decision",
    "evaluate_composite_verdict",
    "load_decision_config",
    "score_technical_alignment",
    "score_fundamental_quality",
    "score_momentum_volume",
    "score_risk_reward",
    "score_valuation_catalyst",
    "calculate_rubric_composite"
]
