"""Decision Engine Scoring Rubrics for Multi-Agent Swing Trading.

Evaluates 5 orthogonal dimensions after Agent 2 (Technical) and Agent 3 (Fundamental):
1. Technical Foundation & Trend Alignment (30 pts)
2. Fundamental Quality & Growth Safety (25 pts)
3. Momentum & Volume Institutional Confirmation (20 pts)
4. Risk-Reward & Trade Asymmetry (15 pts)
5. Valuation & Catalyst Conviction (10 pts)

Total Maximum Score: 100 points
"""

from typing import Dict, Any, Optional, Tuple, List
import math


def score_technical_alignment(tech_data: Optional[Dict[str, Any]], max_points: int = 30) -> Dict[str, Any]:
    """
    Evaluates multi-timeframe trend alignment, EMA stack synchronization,
    and market structure from Agent 2.
    """
    if not tech_data or tech_data.get("status") in ["error", "insufficient_data"]:
        return {
            "score": 0,
            "max_points": max_points,
            "available_weight": max_points,
            "percentage": 0.0,
            "details": ["Technical analysis data unavailable or failed"]
        }

    points = 0.0
    details = []

    trend = tech_data.get("trend", {}) or {}
    daily_trend = trend.get("daily", "neutral")
    hourly_trend = trend.get("hourly", "neutral")
    daily_ema = trend.get("daily_ema_alignment", False)
    hourly_ema = trend.get("hourly_ema_alignment", False)
    structure = trend.get("market_structure", "")
    breakout = tech_data.get("breakout", {}) or {}

    # 1. Daily Trend (up to 12 pts)
    if daily_trend == "bullish":
        points += 12.0
        details.append("Daily trend is confirmed bullish (+12)")
    elif daily_trend == "neutral":
        points += 6.0
        details.append("Daily trend is neutral/consolidating (+6)")
    else:
        details.append("Daily trend is bearish (+0)")

    # 2. Hourly Trend Synchronization (up to 8 pts)
    if hourly_trend == "bullish":
        points += 8.0
        details.append("Hourly trend aligned bullish (+8)")
    elif hourly_trend == "neutral":
        points += 4.0
        details.append("Hourly trend is neutral (+4)")
    else:
        details.append("Hourly trend is bearish (+0)")

    # 3. EMA Stack Synchronization (up to 5 pts)
    if daily_ema and hourly_ema:
        points += 5.0
        details.append("Dual timeframe EMA stack aligned (+5)")
    elif daily_ema:
        points += 3.0
        details.append("Daily EMA stack aligned (+3)")
    elif hourly_ema:
        points += 2.0
        details.append("Hourly EMA stack aligned (+2)")
    else:
        details.append("EMA stack not aligned (+0)")

    # 4. Breakout & Market Structure (up to 5 pts)
    if breakout.get("detected"):
        b_pts = 3.0
        if breakout.get("volume_confirmed"):
            b_pts = 5.0
            details.append(f"Volume-confirmed {breakout.get('type', 'price')} breakout (+5)")
        else:
            details.append(f"Price breakout detected ({breakout.get('type', 'unconfirmed')}) (+3)")
        points += b_pts
    elif structure == "higher_highs_higher_lows":
        points += 4.0
        details.append("Bullish structure: Higher highs and higher lows (+4)")
    elif structure in ("higher_highs_lower_lows", "lower_highs_higher_lows"):
        points += 2.0
        details.append("Mixed swing pivot structure (+2)")

    final_score = min(int(round(points)), max_points)
    pct = round((final_score / max_points) * 100, 1) if max_points > 0 else 0.0

    return {
        "score": final_score,
        "max_points": max_points,
        "available_weight": max_points,
        "percentage": pct,
        "details": details
    }


def score_fundamental_quality(fund_data: Optional[Dict[str, Any]], max_points: int = 25) -> Dict[str, Any]:
    """
    Evaluates business quality, revenue/PAT growth, profitability,
    balance sheet safety, and earnings quality from Agent 3.
    """
    if not fund_data or fund_data.get("status") in ["error", "insufficient_data"]:
        # When fundamentals are completely unavailable, flag zero weight for dynamic normalization
        return {
            "score": 0,
            "max_points": max_points,
            "available_weight": 0,
            "percentage": 0.0,
            "details": ["Fundamental data unavailable (weight dynamically redistributed)"]
        }

    points = 0.0
    details = []

    fund_score = fund_data.get("fundamental_score")
    growth = fund_data.get("growth", {}) or {}
    prof = fund_data.get("profitability", {}) or {}
    bs = fund_data.get("balance_sheet", {}) or {}
    cf = fund_data.get("cash_flow", {}) or {}
    eq = fund_data.get("earnings_quality", {}) or {}

    # 1. Base Fundamental Quality Rating (up to 10 pts)
    if fund_score is not None:
        scaled_base = (fund_score / 100.0) * 10.0
        points += scaled_base
        details.append(f"Agent 3 base score ({fund_score}/100) -> +{round(scaled_base, 1)} pts")

    # 2. Earnings & Revenue Growth Momentum (up to 6 pts)
    rev_yoy = growth.get("revenue_yoy")
    pat_yoy = growth.get("pat_yoy")
    if rev_yoy is not None and rev_yoy >= 15.0:
        points += 3.0
        details.append(f"Robust revenue expansion: {rev_yoy}% YoY (+3)")
    elif rev_yoy is not None and rev_yoy >= 8.0:
        points += 1.5
        details.append(f"Moderate revenue expansion: {rev_yoy}% YoY (+1.5)")

    if pat_yoy is not None and pat_yoy >= 15.0:
        points += 3.0
        details.append(f"Strong profit expansion: {pat_yoy}% YoY (+3)")
    elif pat_yoy is not None and pat_yoy >= 8.0:
        points += 1.5
        details.append(f"Moderate profit expansion: {pat_yoy}% YoY (+1.5)")

    # 3. Capital Efficiency & Profitability (up to 5 pts)
    roe = prof.get("roe")
    roce = prof.get("roce")
    if roe is not None and roe >= 18.0:
        points += 3.0
        details.append(f"High Return on Equity: {roe}% (+3)")
    elif roe is not None and roe >= 12.0:
        points += 1.5
        details.append(f"Acceptable Return on Equity: {roe}% (+1.5)")

    if roce is not None and roce >= 18.0:
        points += 2.0
        details.append(f"Strong ROCE capital efficiency: {roce}% (+2)")
    elif roce is not None and roce >= 12.0:
        points += 1.0
        details.append(f"Healthy ROCE: {roce}% (+1)")

    # 4. Solvency & Balance Sheet Health (up to 4 pts)
    if bs.get("is_financial"):
        points += 4.0
        details.append("Financial institution: Corporate D/E exempt (+4)")
    else:
        de = bs.get("debt_equity")
        cr = bs.get("current_ratio")
        if de is not None and de <= 0.5:
            points += 2.5
            details.append(f"Low leverage: D/E {de} (+2.5)")
        elif de is not None and de <= 1.0:
            points += 1.5
            details.append(f"Moderate leverage: D/E {de} (+1.5)")
        elif de is not None and de > 2.0:
            details.append(f"Elevated leverage: D/E {de} (+0)")

        if cr is not None and cr >= 1.3:
            points += 1.5
            details.append(f"Healthy liquidity: Current ratio {cr} (+1.5)")
        elif cr is not None and cr >= 1.0:
            points += 0.8
            details.append(f"Adequate liquidity: Current ratio {cr} (+0.8)")

    # Accounting Quality Check (deduction if divergence)
    if eq.get("status") == "warning" or fund_data.get("warnings"):
        points = max(0.0, points - 3.0)
        details.append("Deduction applied for accounting anomaly or fundamental warning (-3)")

    final_score = min(int(round(points)), max_points)
    pct = round((final_score / max_points) * 100, 1) if max_points > 0 else 0.0

    return {
        "score": final_score,
        "max_points": max_points,
        "available_weight": max_points,
        "percentage": pct,
        "details": details
    }


def score_momentum_volume(tech_data: Optional[Dict[str, Any]], max_points: int = 20) -> Dict[str, Any]:
    """
    Evaluates swing momentum indicators (RSI, MACD) and institutional
    volume confirmation (RVOL) from Agent 2.
    """
    if not tech_data or tech_data.get("status") in ["error", "insufficient_data"]:
        return {
            "score": 0,
            "max_points": max_points,
            "available_weight": max_points,
            "percentage": 0.0,
            "details": ["Momentum & volume data unavailable"]
        }

    points = 0.0
    details = []

    mom = tech_data.get("momentum", {}) or {}
    vol = tech_data.get("volume", {}) or {}

    rsi = mom.get("daily_rsi")
    daily_macd = mom.get("daily_macd")
    hourly_macd = mom.get("hourly_macd")
    rvol = vol.get("relative_volume")
    vol_conf = vol.get("confirmation", False)

    # 1. RSI Swing Sweet-Spot (up to 7 pts)
    # Ideal swing momentum is between 50 and 68. Over 70 is overbought; under 40 is weak.
    if rsi is not None:
        if 55.0 <= rsi <= 68.0:
            points += 7.0
            details.append(f"RSI in optimal swing sweet-spot: {rsi} (+7)")
        elif 50.0 <= rsi < 55.0:
            points += 5.0
            details.append(f"RSI in positive momentum territory: {rsi} (+5)")
        elif 68.0 < rsi <= 75.0:
            points += 4.0
            details.append(f"RSI strong but approaching overbought: {rsi} (+4)")
        elif 40.0 <= rsi < 50.0:
            points += 2.0
            details.append(f"RSI neutral/subdued: {rsi} (+2)")
        else:
            details.append(f"RSI unfavorable for swing entry: {rsi} (+0)")

    # 2. MACD Bullish Alignment (up to 6 pts)
    if daily_macd == "bullish" and hourly_macd == "bullish":
        points += 6.0
        details.append("Dual timeframe MACD bullish alignment (+6)")
    elif daily_macd == "bullish":
        points += 4.0
        details.append("Daily MACD bullish (+4)")
    elif hourly_macd == "bullish":
        points += 2.0
        details.append("Hourly MACD bullish (+2)")
    else:
        details.append("MACD neutral or bearish (+0)")

    # 3. Institutional Volume Confirmation (up to 7 pts)
    if rvol is not None:
        if rvol >= 2.0 or (vol_conf and rvol >= 1.5):
            points += 7.0
            details.append(f"Institutional volume surge: RVOL {rvol}x (+7)")
        elif rvol >= 1.2 or vol_conf:
            points += 5.0
            details.append(f"Above-average volume expansion: RVOL {rvol}x (+5)")
        elif rvol >= 0.9:
            points += 2.0
            details.append(f"Normal trading volume: RVOL {rvol}x (+2)")
        else:
            details.append(f"Contracted volume: RVOL {rvol}x (+0)")

    final_score = min(int(round(points)), max_points)
    pct = round((final_score / max_points) * 100, 1) if max_points > 0 else 0.0

    return {
        "score": final_score,
        "max_points": max_points,
        "available_weight": max_points,
        "percentage": pct,
        "details": details
    }


def score_risk_reward(tech_data: Optional[Dict[str, Any]], max_points: int = 15) -> Dict[str, Any]:
    """
    Evaluates the trade setup geometry: Risk/Reward asymmetry,
    stop-loss tightness, and target clearance.
    """
    if not tech_data or tech_data.get("status") in ["error", "insufficient_data"]:
        return {
            "score": 0,
            "max_points": max_points,
            "available_weight": max_points,
            "percentage": 0.0,
            "details": ["Trade setup parameters unavailable"]
        }

    points = 0.0
    details = []

    setup = tech_data.get("trade_setup", {}) or {}
    direction = setup.get("direction", "none")
    rr = setup.get("risk_reward")
    entry_zone = setup.get("entry_zone")
    stop_loss = setup.get("stop_loss")
    target_1 = setup.get("target_1")

    if direction != "long" or not entry_zone or not stop_loss or not target_1:
        return {
            "score": 0,
            "max_points": max_points,
            "available_weight": max_points,
            "percentage": 0.0,
            "details": ["No actionable long trade setup defined"]
        }

    # 1. Risk-to-Reward Ratio (up to 12 pts)
    if rr is not None:
        if rr >= 2.5:
            points += 12.0
            details.append(f"Exceptional Risk/Reward asymmetry: {rr}:1 (+12)")
        elif rr >= 2.0:
            points += 9.5
            details.append(f"Favorable Risk/Reward ratio: {rr}:1 (+9.5)")
        elif rr >= 1.5:
            points += 7.0
            details.append(f"Acceptable Risk/Reward ratio: {rr}:1 (+7)")
        elif rr >= 1.2:
            points += 3.0
            details.append(f"Marginal Risk/Reward ratio: {rr}:1 (+3)")
        else:
            details.append(f"Unfavorable Risk/Reward ratio: {rr}:1 (+0)")

    # 2. Execution Setup Completeness (up to 3 pts)
    volatility = tech_data.get("volatility", {}) or {}
    atr_pct = volatility.get("atr_percent")
    if atr_pct is not None and 1.5 <= atr_pct <= 4.5:
        points += 3.0
        details.append(f"Optimal swing volatility buffer (ATR {atr_pct}%) (+3)")
    elif atr_pct is not None:
        points += 1.5
        details.append(f"Viable volatility buffer (ATR {atr_pct}%) (+1.5)")
    else:
        points += 1.0

    final_score = min(int(round(points)), max_points)
    pct = round((final_score / max_points) * 100, 1) if max_points > 0 else 0.0

    return {
        "score": final_score,
        "max_points": max_points,
        "available_weight": max_points,
        "percentage": pct,
        "details": details
    }


def score_valuation_catalyst(
    fund_data: Optional[Dict[str, Any]],
    screening_data: Optional[Dict[str, Any]] = None,
    max_points: int = 10
) -> Dict[str, Any]:
    """
    Evaluates sector-relative valuation multiples and qualitative
    catalyst sentiment.
    """
    points = 0.0
    details = []
    available_weight = max_points

    val = fund_data.get("valuation", {}) if fund_data else {}
    pe = val.get("pe")
    sector_pe = val.get("sector_pe")
    val_assessment = val.get("valuation_assessment", "fair")

    # 1. Valuation Multiple Assessment (up to 6 pts)
    if pe is not None and sector_pe is not None:
        if val_assessment == "undervalued" or pe <= sector_pe * 0.85:
            points += 6.0
            details.append(f"Undervalued vs sector multiple (P/E {pe} vs Sector {sector_pe}) (+6)")
        elif val_assessment in ["fair", "reasonable"] or pe <= sector_pe * 1.15:
            points += 4.5
            details.append(f"Fairly valued vs sector benchmark (P/E {pe} vs Sector {sector_pe}) (+4.5)")
        elif pe <= sector_pe * 1.4:
            points += 2.5
            details.append(f"Trading at manageable growth premium (P/E {pe} vs Sector {sector_pe}) (+2.5)")
        else:
            details.append(f"Trading at steep valuation premium (P/E {pe} vs Sector {sector_pe}) (+0)")
    else:
        # Neutral baseline for missing valuation
        points += 3.0
        details.append("Sector multiple comparison unavailable; baseline neutral applied (+3)")

    # 2. Qualitative Catalyst / News Sentiment (up to 4 pts)
    cat = None
    if screening_data:
        cat = screening_data.get("llm_catalyst") or screening_data.get("catalyst")

    if cat and isinstance(cat, dict):
        sentiment = (cat.get("sentiment") or "NEUTRAL").upper()
        if sentiment == "BULLISH":
            points += 4.0
            details.append("Bullish corporate or news catalyst confirmed (+4)")
        elif sentiment == "NEUTRAL":
            points += 2.0
            details.append("Neutral news catalyst background (+2)")
        else:
            details.append("Bearish news catalyst or headline headwind (+0)")
    else:
        # Baseline neutral if no catalyst analysis requested
        points += 2.0
        details.append("No active news catalyst flagged; neutral baseline applied (+2)")

    final_score = min(int(round(points)), max_points)
    pct = round((final_score / max_points) * 100, 1) if max_points > 0 else 0.0

    return {
        "score": final_score,
        "max_points": max_points,
        "available_weight": available_weight,
        "percentage": pct,
        "details": details
    }


def calculate_rubric_composite(rubrics: Dict[str, Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
    """
    Computes the total composite score across all rubric dimensions.
    Gracefully normalizes score to 100 points if any optional dimension
    is missing available weight.
    """
    total_raw_points = sum(r.get("score", 0) for r in rubrics.values())
    total_max_points = sum(r.get("max_points", 0) for r in rubrics.values())
    total_available_weight = sum(r.get("available_weight", r.get("max_points", 0)) for r in rubrics.values())

    if total_available_weight <= 0:
        return 0, rubrics

    if total_available_weight < total_max_points:
        # Scale dynamically based on available weights
        normalized = (total_raw_points / float(total_available_weight)) * 100.0
    else:
        normalized = total_raw_points

    composite_score = min(100, max(0, int(round(normalized))))
    return composite_score, rubrics
