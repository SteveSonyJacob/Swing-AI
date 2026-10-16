"""Deterministic Decision Engine orchestrating multi-agent evaluations into actionable verdicts.

Synthesizes Agent 2 (Technical) and Agent 3 (Fundamental) through a structured
100-point scoring rubric, enforces strict confirmation gating, and produces
concrete execution parameters.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import yaml
import logging

from src.decision.rubrics import (
    score_technical_alignment,
    score_fundamental_quality,
    score_momentum_volume,
    score_risk_reward,
    score_valuation_catalyst,
    calculate_rubric_composite
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "decision_settings.yaml"


def load_decision_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Loads decision engine configuration with fallbacks."""
    target_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not parse {target_path}, using defaults: {e}")

    # Sensible defaults
    return {
        "scoring": {
            "rubric_weights": {
                "technical_alignment": 30,
                "fundamental_quality": 25,
                "momentum_volume": 20,
                "risk_reward": 15,
                "valuation_catalyst": 10
            }
        },
        "thresholds": {
            "technical": {"veto_threshold": 45, "minimum_threshold": 55, "strong_threshold": 65},
            "fundamental": {"distressed_threshold": 40, "adequate_threshold": 45, "strong_threshold": 60},
            "decision": {"strong_buy_min": 65, "moderate_buy_min": 55},
            "risk_reward": {"minimum_rr": 1.5, "preferred_rr": 2.0}
        },
        "execution": {
            "position_sizing": {
                "strong_buy": "Standard swing allocation (2.0% - 3.0% capital risk)",
                "moderate_buy": "Conservative swing allocation (1.0% - 1.5% capital risk)",
                "speculative": "Reduced speculative allocation (0.5% capital risk)",
                "watchlist": "No capital allocation (Monitor for confirmed technical breakout/reversal)",
                "avoid": "No capital allocation (Setup does not satisfy risk parameters)",
                "hold": "No capital allocation (Insufficient data)"
            }
        }
    }


class DecisionEngine:
    """Multi-Agent Decision Engine implementing confirmation rubrics and trade gating."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config = load_decision_config(config_path)
        self.weights = self.config.get("scoring", {}).get("rubric_weights", {
            "technical_alignment": 30,
            "fundamental_quality": 25,
            "momentum_volume": 20,
            "risk_reward": 15,
            "valuation_catalyst": 10
        })
        self.thresholds = self.config.get("thresholds", {})
        self.sizing_map = self.config.get("execution", {}).get("position_sizing", {})

    def evaluate(
        self,
        technical_data: Optional[Dict[str, Any]] = None,
        fundamental_data: Optional[Dict[str, Any]] = None,
        screening_data: Optional[Dict[str, Any]] = None,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the full 5-dimension scoring rubric and applies strict
        confirmation gates to deliver a definitive trade verdict and execution plan.
        """
        tech = technical_data if isinstance(technical_data, dict) else {}
        fund = fundamental_data if isinstance(fundamental_data, dict) else {}
        screen = screening_data if isinstance(screening_data, dict) else {}

        # 1. Compute 5-part scoring rubrics
        r_tech = score_technical_alignment(tech, max_points=self.weights.get("technical_alignment", 30))
        r_fund = score_fundamental_quality(fund, max_points=self.weights.get("fundamental_quality", 25))
        r_mom = score_momentum_volume(tech, max_points=self.weights.get("momentum_volume", 20))
        r_rr = score_risk_reward(tech, max_points=self.weights.get("risk_reward", 15))
        r_val = score_valuation_catalyst(fund, screen, max_points=self.weights.get("valuation_catalyst", 10))

        rubrics = {
            "technical_alignment": r_tech,
            "fundamental_quality": r_fund,
            "momentum_volume": r_mom,
            "risk_reward": r_rr,
            "valuation_catalyst": r_val
        }

        # Calculate composite decision score
        decision_score, rubrics = calculate_rubric_composite(rubrics)

        # 2. Extract key agent state indicators for confirmation gating
        a2_score = tech.get("technical_score")
        a3_score = fund.get("fundamental_score")
        daily_trend = tech.get("trend", {}).get("daily") if isinstance(tech.get("trend"), dict) else None
        hourly_trend = tech.get("trend", {}).get("hourly") if isinstance(tech.get("trend"), dict) else None
        tech_status = tech.get("status")
        fund_status = fund.get("status")
        trade_setup = tech.get("trade_setup", {}) if isinstance(tech.get("trade_setup"), dict) else {}
        direction = trade_setup.get("direction", "none")
        rr = trade_setup.get("risk_reward")

        # Thresholds
        t_veto = self.thresholds.get("technical", {}).get("veto_threshold", 45)
        t_min = self.thresholds.get("technical", {}).get("minimum_threshold", 55)
        t_strong = self.thresholds.get("technical", {}).get("strong_threshold", 65)
        f_distressed = self.thresholds.get("fundamental", {}).get("distressed_threshold", 40)
        f_adequate = self.thresholds.get("fundamental", {}).get("adequate_threshold", 45)
        f_strong = self.thresholds.get("fundamental", {}).get("strong_threshold", 60)
        d_strong = self.thresholds.get("decision", {}).get("strong_buy_min", 65)
        d_moderate = self.thresholds.get("decision", {}).get("moderate_buy_min", 55)

        # 3. Apply Multi-Agent Confirmation Gating
        verdict = "NEUTRAL_WAIT"
        action = "WATCH"
        confidence = "LOW"
        reason = "Setup does not meet required entry thresholds across all agents."
        sizing_key = "watchlist"

        # Gate 1: Insufficient technical data or error
        if a2_score is None or tech_status in ["insufficient_data", "error"] or not tech:
            verdict = "INSUFFICIENT_DATA_HOLD"
            action = "HOLD"
            confidence = "LOW"
            reason = "Technical analysis data is unavailable or insufficient"
            sizing_key = "hold"

        # Gate 2: Clear Bearish Technical Trend or failing technical score (< 45)
        # Fundamental health must NEVER override clearly bearish technicals for swing long
        elif daily_trend == "bearish" or a2_score < t_veto:
            if a3_score is not None and a3_score >= f_strong:
                verdict = "WATCHLIST_WAIT_FOR_SETUP"
                action = "WATCH"
                confidence = "MEDIUM"
                reason = "Strong company fundamentals, but technical trend is bearish/failing. Wait for confirmed technical reversal."
                sizing_key = "watchlist"
            else:
                verdict = "REJECTED_BEARISH"
                action = "AVOID"
                confidence = "HIGH"
                reason = "Technical trend is bearish and below viable swing parameters."
                sizing_key = "avoid"

        # Gate 3: Weak / Below-Threshold Technical Setup (< 55)
        elif a2_score < t_min:
            verdict = "NOT_RECOMMENDED"
            action = "AVOID"
            confidence = "HIGH"
            reason = f"Technical score ({a2_score}/100) is below the minimum required threshold ({t_min}) for trade entry."
            sizing_key = "avoid"

        # Gate 4: Technically Bullish but Fundamentally Distressed / Very Weak (< 40)
        elif daily_trend == "bullish" and a2_score >= t_strong and a3_score is not None and a3_score < f_distressed:
            verdict = "SPECULATIVE_TECHNICAL_ONLY"
            action = "BUY"
            confidence = "MEDIUM"
            reason = f"Strong technical momentum, but company fundamental health is poor ({a3_score}/100). Higher risk."
            sizing_key = "speculative"

        # Gate 5: Strong Buy Setup (Mutual confirmation across technical & fundamental engines)
        elif (
            daily_trend == "bullish"
            and a2_score >= t_strong
            and (a3_score is not None and a3_score >= f_strong)
            and (decision_score >= d_strong or (a2_score + a3_score) / 2 >= d_strong)
        ):
            verdict = "STRONG_BUY_CANDIDATE"
            action = "BUY"
            confidence = "HIGH"
            reason = "Mutual multi-agent confirmation: Confirmed bullish technical setup and solid fundamental quality."
            sizing_key = "strong_buy"

        # Gate 6: Moderate Buy Setup (Acceptable technicals & adequate fundamentals)
        elif (
            a2_score >= t_min
            and daily_trend in ["bullish", "neutral"]
            and (a3_score is None or a3_score >= f_adequate)
            and (decision_score >= d_moderate or (a2_score + (a3_score or a2_score)) / 2 >= d_moderate)
        ):
            verdict = "MODERATE_BUY_CANDIDATE"
            action = "BUY"
            confidence = "MEDIUM"
            reason = "Acceptable technical setup with supportive fundamental metrics."
            sizing_key = "moderate_buy"

        # Gate 7: Default Fallback
        else:
            verdict = "NEUTRAL_WAIT"
            action = "WATCH"
            confidence = "LOW"
            reason = "Setup does not meet required entry thresholds across all agents."
            sizing_key = "watchlist"

        # 4. Confirmation Checks Summary
        mom_data = tech.get("momentum", {}) if isinstance(tech.get("momentum"), dict) else {}
        vol_data = tech.get("volume", {}) if isinstance(tech.get("volume"), dict) else {}
        rsi_val = mom_data.get("daily_rsi")
        rvol_val = vol_data.get("relative_volume")
        eq_data = fund.get("earnings_quality", {}) if isinstance(fund.get("earnings_quality"), dict) else {}

        confirmation_checks = {
            "daily_trend_bullish": daily_trend == "bullish",
            "hourly_trend_aligned": hourly_trend == "bullish",
            "volume_confirmed": bool(vol_data.get("confirmation") or (rvol_val is not None and rvol_val >= 1.2)),
            "rsi_in_sweet_spot": bool(rsi_val is not None and 50.0 <= rsi_val <= 68.0),
            "fundamental_health_sound": bool(a3_score is not None and a3_score >= f_adequate),
            "risk_reward_viable": bool(rr is not None and rr >= self.thresholds.get("risk_reward", {}).get("minimum_rr", 1.5)),
            "no_critical_accounting_red_flags": not bool(eq_data.get("status") == "warning" or fund.get("warnings"))
        }

        # 5. Concrete Execution Plan
        pos_sizing = self.sizing_map.get(sizing_key, "No capital allocation")
        execution_plan = {
            "action": action,
            "direction": direction.upper() if action == "BUY" else "NONE",
            "confidence": confidence,
            "entry_zone": trade_setup.get("entry_zone", "N/A"),
            "stop_loss": trade_setup.get("stop_loss", "N/A"),
            "target_1": trade_setup.get("target_1", "N/A"),
            "target_2": trade_setup.get("target_2", "N/A"),
            "risk_reward": trade_setup.get("risk_reward", "N/A"),
            "position_sizing": pos_sizing
        }

        return {
            "symbol": symbol,
            "decision_score": decision_score,
            "composite_score": decision_score,  # canonical alias
            "verdict": verdict,
            "composite_verdict": verdict,        # canonical alias
            "verdict_reason": reason,
            "action": action,
            "confidence": confidence,
            "scoring_rubrics": rubrics,
            "confirmation_checks": confirmation_checks,
            "execution_plan": execution_plan
        }


# Singleton default engine instance
_default_engine = DecisionEngine()


def evaluate_decision(
    technical_data: Optional[Dict[str, Any]] = None,
    fundamental_data: Optional[Dict[str, Any]] = None,
    screening_data: Optional[Dict[str, Any]] = None,
    symbol: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function evaluating decisions with scoring rubrics."""
    return _default_engine.evaluate(
        technical_data=technical_data,
        fundamental_data=fundamental_data,
        screening_data=screening_data,
        symbol=symbol
    )


def evaluate_composite_verdict(
    agent_2_score: Optional[int] = None,
    agent_3_score: Optional[int] = None,
    daily_trend: Optional[str] = None,
    tech_status: Optional[str] = None,
    fund_status: Optional[str] = None,
    agent_1_score: Optional[int] = None,
    *args,
    **kwargs
) -> Tuple[int, str, str]:
    """
    Backward-compatible adapter matching the historical evaluate_composite_verdict signature.
    Returns (composite_score, verdict, reason).
    """
    # Handle legacy positional calls: (agent_1_score, agent_2_score, agent_3_score, daily_trend, ...)
    if len(args) >= 2 and isinstance(agent_2_score, int) and isinstance(agent_3_score, int):
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

    # Build synthetic structures for the full decision engine
    synth_tech = None
    if agent_2_score is not None or tech_status:
        synth_tech = {
            "status": tech_status or "success",
            "technical_score": agent_2_score,
            "trend": {
                "daily": daily_trend or "neutral",
                "hourly": daily_trend or "neutral",
                "daily_ema_alignment": daily_trend == "bullish",
                "hourly_ema_alignment": daily_trend == "bullish"
            },
            "momentum": {
                "daily_rsi": 60.0 if daily_trend == "bullish" else 45.0,
                "daily_macd": "bullish" if daily_trend == "bullish" else "bearish"
            },
            "volume": {
                "relative_volume": 1.5 if daily_trend == "bullish" else 0.8,
                "confirmation": daily_trend == "bullish"
            },
            "trade_setup": {
                "direction": "long" if daily_trend == "bullish" and (agent_2_score or 0) >= 55 else "none",
                "risk_reward": 2.0 if (agent_2_score or 0) >= 65 else 1.5,
                "entry_zone": "Confirmed Setup",
                "stop_loss": "ATR Buffered",
                "target_1": "Target 1"
            }
        }

    synth_fund = None
    if agent_3_score is not None or fund_status:
        synth_fund = {
            "status": fund_status or "success",
            "fundamental_score": agent_3_score,
            "growth": {"revenue_yoy": 15.0 if (agent_3_score or 0) >= 60 else 5.0, "pat_yoy": 15.0 if (agent_3_score or 0) >= 60 else 5.0},
            "profitability": {"roe": 18.0 if (agent_3_score or 0) >= 60 else 10.0, "roce": 18.0 if (agent_3_score or 0) >= 60 else 10.0},
            "balance_sheet": {"debt_equity": 0.5 if (agent_3_score or 0) >= 60 else 1.5},
            "valuation": {"pe": 20.0, "sector_pe": 22.0, "valuation_assessment": "fair"}
        }

    res = _default_engine.evaluate(
        technical_data=synth_tech,
        fundamental_data=synth_fund
    )

    valid_scores = [s for s in [agent_2_score, agent_3_score] if s is not None]
    composite_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else (agent_2_score or 0)

    return composite_score, res["verdict"], res["verdict_reason"]

