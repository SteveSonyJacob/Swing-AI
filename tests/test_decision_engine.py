"""Comprehensive unit and integration test suite for the Decision Engine and Scoring Rubrics."""

import pytest
from src.decision.rubrics import (
    score_technical_alignment,
    score_fundamental_quality,
    score_momentum_volume,
    score_risk_reward,
    score_valuation_catalyst,
    calculate_rubric_composite
)
from src.decision.engine import DecisionEngine, evaluate_decision, evaluate_composite_verdict
from run_all import run_single_stock
from src.screening.output.pipeline import pipe_to_agents


class TestDecisionRubrics:
    """Tests for each of the 5 scoring rubric dimensions."""

    def test_score_technical_alignment_bullish(self):
        tech_data = {
            "status": "success",
            "trend": {
                "daily": "bullish",
                "hourly": "bullish",
                "daily_ema_alignment": True,
                "hourly_ema_alignment": True,
                "market_structure": "higher_highs_higher_lows"
            },
            "breakout": {
                "detected": True,
                "type": "52_week_high",
                "volume_confirmed": True
            }
        }
        res = score_technical_alignment(tech_data, max_points=30)
        assert res["score"] == 30
        assert res["max_points"] == 30
        assert res["percentage"] == 100.0
        assert any("bullish" in d.lower() for d in res["details"])

    def test_score_technical_alignment_bearish(self):
        tech_data = {
            "status": "success",
            "trend": {
                "daily": "bearish",
                "hourly": "bearish",
                "daily_ema_alignment": False,
                "hourly_ema_alignment": False,
                "market_structure": "lower_highs_lower_lows"
            },
            "breakout": {"detected": False}
        }
        res = score_technical_alignment(tech_data, max_points=30)
        assert res["score"] == 0
        assert res["percentage"] == 0.0

    def test_score_technical_alignment_missing_data(self):
        res = score_technical_alignment(None, max_points=30)
        assert res["score"] == 0
        res_err = score_technical_alignment({"status": "insufficient_data"}, max_points=30)
        assert res_err["score"] == 0

    def test_score_fundamental_quality_healthy(self):
        fund_data = {
            "status": "success",
            "fundamental_score": 85,
            "growth": {"revenue_yoy": 22.0, "pat_yoy": 28.0},
            "profitability": {"roe": 24.0, "roce": 22.0},
            "balance_sheet": {"debt_equity": 0.25, "current_ratio": 1.8},
            "cash_flow": {"ocf_pat_ratio": 1.2},
            "earnings_quality": {"status": "strong"},
            "warnings": []
        }
        res = score_fundamental_quality(fund_data, max_points=25)
        assert res["score"] >= 22
        assert res["max_points"] == 25
        assert res["available_weight"] == 25

    def test_score_fundamental_quality_financial_exemption(self):
        fund_data = {
            "status": "success",
            "fundamental_score": 75,
            "growth": {"revenue_yoy": 16.0, "pat_yoy": 18.0},
            "profitability": {"roe": 19.0, "roce": 15.0},
            "balance_sheet": {"is_financial": True, "debt_equity": 6.5},  # High D/E normal for banks
            "cash_flow": {},
            "earnings_quality": {"status": "strong"},
            "warnings": []
        }
        res = score_fundamental_quality(fund_data, max_points=25)
        assert any("financial institution" in d.lower() for d in res["details"])
        assert res["score"] >= 18

    def test_score_fundamental_quality_accounting_warning(self):
        fund_data = {
            "status": "success",
            "fundamental_score": 60,
            "growth": {"revenue_yoy": 10.0, "pat_yoy": 10.0},
            "profitability": {"roe": 12.0, "roce": 12.0},
            "balance_sheet": {"debt_equity": 1.5, "current_ratio": 1.1},
            "earnings_quality": {"status": "warning"},
            "warnings": ["Significant divergence between reported PAT and operating cash flow"]
        }
        res = score_fundamental_quality(fund_data, max_points=25)
        assert any("deduction" in d.lower() for d in res["details"])

    def test_score_fundamental_quality_unavailable(self):
        res = score_fundamental_quality(None, max_points=25)
        assert res["score"] == 0
        assert res["available_weight"] == 0  # Dynamic normalization flag

    def test_score_momentum_volume_optimal(self):
        tech_data = {
            "status": "success",
            "momentum": {
                "daily_rsi": 62.5,
                "daily_macd": "bullish",
                "hourly_macd": "bullish"
            },
            "volume": {
                "relative_volume": 2.2,
                "confirmation": True
            }
        }
        res = score_momentum_volume(tech_data, max_points=20)
        assert res["score"] == 20
        assert res["percentage"] == 100.0

    def test_score_momentum_volume_overbought_contracted(self):
        tech_data = {
            "status": "success",
            "momentum": {
                "daily_rsi": 78.0,
                "daily_macd": "bullish",
                "hourly_macd": "bearish"
            },
            "volume": {
                "relative_volume": 0.6,
                "confirmation": False
            }
        }
        res = score_momentum_volume(tech_data, max_points=20)
        assert res["score"] < 12

    def test_score_risk_reward_asymmetric(self):
        tech_data = {
            "status": "success",
            "trade_setup": {
                "direction": "long",
                "entry_zone": "2400.00 - 2420.00",
                "stop_loss": 2350.00,
                "target_1": 2580.00,
                "target_2": 2650.00,
                "risk_reward": 2.6
            },
            "volatility": {"atr_percent": 2.4}
        }
        res = score_risk_reward(tech_data, max_points=15)
        assert res["score"] == 15
        assert any("exceptional" in d.lower() for d in res["details"])

    def test_score_risk_reward_unviable(self):
        tech_data = {
            "status": "success",
            "trade_setup": {
                "direction": "none",
                "risk_reward": 0.8
            }
        }
        res = score_risk_reward(tech_data, max_points=15)
        assert res["score"] == 0

    def test_score_valuation_catalyst_discount_and_bullish(self):
        fund_data = {
            "valuation": {
                "pe": 16.0,
                "sector_pe": 24.0,
                "valuation_assessment": "undervalued"
            }
        }
        screen_data = {
            "llm_catalyst": {
                "sentiment": "BULLISH",
                "summary": "Major new multi-million export order win"
            }
        }
        res = score_valuation_catalyst(fund_data, screen_data, max_points=10)
        assert res["score"] == 10
        assert any("undervalued" in d.lower() for d in res["details"])
        assert any("bullish" in d.lower() for d in res["details"])

    def test_calculate_rubric_composite_normalization(self):
        rubrics = {
            "r1": {"score": 25, "max_points": 30, "available_weight": 30},
            "r2": {"score": 0, "max_points": 25, "available_weight": 0},  # Missing dimension
            "r3": {"score": 18, "max_points": 20, "available_weight": 20},
            "r4": {"score": 12, "max_points": 15, "available_weight": 15},
            "r5": {"score": 8, "max_points": 10, "available_weight": 10}
        }
        score, _ = calculate_rubric_composite(rubrics)
        # Total raw = 63, Total available = 75 -> 63/75 * 100 = 84
        assert score == 84


class TestDecisionEngineGating:
    """Tests for multi-agent confirmation gating, vetoes, and trade action generation."""

    def setup_method(self):
        self.engine = DecisionEngine()

    def test_gate_1_missing_technical_data(self):
        res = self.engine.evaluate(technical_data=None, fundamental_data={"fundamental_score": 80})
        assert res["verdict"] == "INSUFFICIENT_DATA_HOLD"
        assert res["action"] == "HOLD"
        assert res["execution_plan"]["direction"] == "NONE"

    def test_gate_2_bearish_veto_with_strong_fundamentals(self):
        """Crucial requirement: High fundamentals must NEVER override bearish technicals for a BUY."""
        tech = {
            "status": "success",
            "technical_score": 40,
            "trend": {"daily": "bearish", "hourly": "bearish"},
            "trade_setup": {"direction": "none"}
        }
        fund = {
            "status": "success",
            "fundamental_score": 88,
            "growth": {"revenue_yoy": 25.0, "pat_yoy": 30.0}
        }
        res = self.engine.evaluate(technical_data=tech, fundamental_data=fund)
        assert res["verdict"] == "WATCHLIST_WAIT_FOR_SETUP"
        assert res["action"] == "WATCH"
        assert "bearish" in res["verdict_reason"].lower()

    def test_gate_2_bearish_veto_with_weak_fundamentals(self):
        tech = {
            "status": "success",
            "technical_score": 35,
            "trend": {"daily": "bearish", "hourly": "bearish"},
            "trade_setup": {"direction": "none"}
        }
        fund = {
            "status": "success",
            "fundamental_score": 42
        }
        res = self.engine.evaluate(technical_data=tech, fundamental_data=fund)
        assert res["verdict"] == "REJECTED_BEARISH"
        assert res["action"] == "AVOID"

    def test_gate_3_below_minimum_technical_threshold(self):
        tech = {
            "status": "success",
            "technical_score": 50,  # Below 55 min threshold
            "trend": {"daily": "neutral", "hourly": "neutral"},
            "trade_setup": {"direction": "long"}
        }
        fund = {"status": "success", "fundamental_score": 65}
        res = self.engine.evaluate(technical_data=tech, fundamental_data=fund)
        assert res["verdict"] == "NOT_RECOMMENDED"
        assert res["action"] == "AVOID"

    def test_gate_4_strong_tech_poor_fundamentals_speculative(self):
        tech = {
            "status": "success",
            "technical_score": 75,
            "trend": {"daily": "bullish", "hourly": "bullish"},
            "momentum": {"daily_rsi": 62.0, "daily_macd": "bullish"},
            "volume": {"relative_volume": 1.8, "confirmation": True},
            "trade_setup": {
                "direction": "long",
                "entry_zone": "100 - 102",
                "stop_loss": 95,
                "target_1": 112,
                "risk_reward": 2.0
            }
        }
        fund = {
            "status": "success",
            "fundamental_score": 32  # Poor/distressed
        }
        res = self.engine.evaluate(technical_data=tech, fundamental_data=fund)
        assert res["verdict"] == "SPECULATIVE_TECHNICAL_ONLY"
        assert res["action"] == "BUY"
        assert "speculative" in res["execution_plan"]["position_sizing"].lower()

    def test_gate_5_strong_buy_mutual_confirmation(self):
        tech = {
            "status": "success",
            "technical_score": 82,
            "trend": {
                "daily": "bullish",
                "hourly": "bullish",
                "daily_ema_alignment": True,
                "hourly_ema_alignment": True,
                "market_structure": "higher_highs_higher_lows"
            },
            "momentum": {"daily_rsi": 64.0, "daily_macd": "bullish"},
            "volume": {"relative_volume": 1.9, "confirmation": True},
            "trade_setup": {
                "direction": "long",
                "entry_zone": "2450.00 - 2470.00",
                "stop_loss": 2380.00,
                "target_1": 2620.00,
                "target_2": 2710.00,
                "risk_reward": 2.1
            }
        }
        fund = {
            "status": "success",
            "fundamental_score": 80,
            "growth": {"revenue_yoy": 18.0, "pat_yoy": 22.0},
            "profitability": {"roe": 22.0, "roce": 20.0},
            "balance_sheet": {"debt_equity": 0.3, "current_ratio": 1.6},
            "valuation": {"pe": 22.0, "sector_pe": 25.0, "valuation_assessment": "fair"}
        }
        res = self.engine.evaluate(technical_data=tech, fundamental_data=fund, symbol="RELIANCE")
        assert res["verdict"] == "STRONG_BUY_CANDIDATE"
        assert res["action"] == "BUY"
        assert res["confidence"] == "HIGH"
        assert res["execution_plan"]["direction"] == "LONG"
        assert "standard swing" in res["execution_plan"]["position_sizing"].lower()
        assert res["confirmation_checks"]["daily_trend_bullish"] is True
        assert res["confirmation_checks"]["volume_confirmed"] is True

    def test_gate_6_moderate_buy_confirmation(self):
        tech = {
            "status": "success",
            "technical_score": 60,
            "trend": {"daily": "bullish", "hourly": "neutral"},
            "momentum": {"daily_rsi": 54.0, "daily_macd": "bullish"},
            "volume": {"relative_volume": 1.3, "confirmation": True},
            "trade_setup": {
                "direction": "long",
                "entry_zone": "500 - 505",
                "stop_loss": 485,
                "target_1": 535,
                "risk_reward": 1.7
            }
        }
        fund = {
            "status": "success",
            "fundamental_score": 52,
            "growth": {"revenue_yoy": 9.0, "pat_yoy": 10.0},
            "balance_sheet": {"debt_equity": 0.8}
        }
        res = self.engine.evaluate(technical_data=tech, fundamental_data=fund)
        assert res["verdict"] == "MODERATE_BUY_CANDIDATE"
        assert res["action"] == "BUY"


class TestDecisionPipelineIntegration:
    """Tests integrating DecisionEngine with run_single_stock and pipe_to_agents."""

    def test_run_single_stock_offline(self):
        res = run_single_stock("RELIANCE", offline=True)
        assert res["symbol"] == "RELIANCE"
        assert "composite_verdict" in res
        assert "composite_score" in res
        assert "scoring_rubrics" in res
        assert "execution_plan" in res
        assert "action" in res
        assert "confidence" in res
        assert res["action"] in ["BUY", "WATCH", "AVOID", "HOLD"]

        # Check all 5 rubric categories exist
        rubrics = res["scoring_rubrics"]
        assert "technical_alignment" in rubrics
        assert "fundamental_quality" in rubrics
        assert "momentum_volume" in rubrics
        assert "risk_reward" in rubrics
        assert "valuation_catalyst" in rubrics

    def test_pipe_to_agents_offline_includes_decision_rubrics(self):
        piped = pipe_to_agents(["RELIANCE", "TCS"], max_symbols_to_analyze=2, offline=True)
        assert len(piped) == 2
        for item in piped:
            assert "decision_engine" in item
            assert "scoring_rubrics" in item
            assert "execution_plan" in item
            assert "action" in item
            assert item["action"] in ["BUY", "WATCH", "AVOID", "HOLD"]
            assert item["composite_score"] is not None
            assert item["composite_score"] >= 0
