"""LLM and heuristic qualitative catalyst analyzer for Agent 1 candidate screening."""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

# Heuristic keyword weights for deterministic evaluation
BULLISH_KEYWORDS = [
    ("order worth", 4, "ORDER_WIN"),
    ("secures order", 4, "ORDER_WIN"),
    ("wins order", 4, "ORDER_WIN"),
    ("contract", 3, "ORDER_WIN"),
    ("profit surges", 4, "EARNINGS"),
    ("profit jumps", 4, "EARNINGS"),
    ("profit up", 3, "EARNINGS"),
    ("revenue surge", 3, "EARNINGS"),
    ("beats estimates", 4, "EARNINGS"),
    ("record high", 3, "EXPANSION"),
    ("expansion", 3, "EXPANSION"),
    ("adds stores", 3, "EXPANSION"),
    ("expands", 2, "EXPANSION"),
    ("rbi lifts", 4, "REGULATORY_LEGAL"),
    ("approval", 3, "REGULATORY_LEGAL"),
    ("target price", 3, "UPGRADE"),
    ("overweight", 2, "UPGRADE"),
    ("upgrade", 3, "UPGRADE"),
    ("dividend", 2, "CORPORATE_ACTION")
]

BEARISH_KEYWORDS = [
    ("probe", -5, "REGULATORY_LEGAL"),
    ("raid", -5, "REGULATORY_LEGAL"),
    ("fraud", -6, "REGULATORY_LEGAL"),
    ("penalty", -4, "REGULATORY_LEGAL"),
    ("sebi notice", -5, "REGULATORY_LEGAL"),
    ("tax notice", -3, "REGULATORY_LEGAL"),
    ("litigation", -3, "REGULATORY_LEGAL"),
    ("loss widens", -4, "EARNINGS"),
    ("profit drops", -4, "EARNINGS"),
    ("slumps", -3, "EARNINGS"),
    ("misses estimates", -3, "EARNINGS"),
    ("downgrade", -3, "DOWNGRADE"),
    ("resigns", -3, "MANAGEMENT"),
    ("strike", -3, "OPERATIONAL"),
    ("curbs", -3, "REGULATORY_LEGAL")
]


def heuristic_catalyst_evaluation(
    symbol: str,
    headlines: List[Dict[str, str]],
    corporate_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Deterministic rule-based qualitative catalyst analysis.
    Evaluates news headlines and corporate context to produce a 0-10 score.
    """
    base_score = 5
    detected_types = []
    reasons = []

    joined_text = " ".join([h.get("title", "") for h in headlines]).lower()

    # Check bullish keywords
    for kw, delta, ctype in BULLISH_KEYWORDS:
        if kw in joined_text:
            base_score += delta
            detected_types.append(ctype)
            reasons.append(f"Positive news trigger: '{kw}'")

    # Check bearish keywords
    for kw, delta, ctype in BEARISH_KEYWORDS:
        if kw in joined_text:
            base_score += delta
            detected_types.append(ctype)
            reasons.append(f"Negative news headwind: '{kw}'")

    # Corporate context boost
    if corporate_context:
        days = corporate_context.get("days_to_results")
        if days is not None and 0 <= days <= 14:
            base_score += 2
            detected_types.append("EARNINGS")
            reasons.append(f"Quarterly earnings catalyst in {days} days")

    final_score = max(0, min(10, base_score))

    if final_score >= 7:
        sentiment = "BULLISH"
    elif final_score <= 3:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"

    main_type = detected_types[0] if detected_types else "GENERAL"

    if reasons:
        summary = "; ".join(reasons[:2]) + "."
    elif headlines:
        summary = f"Recent news for {symbol}: {headlines[0].get('title', '')}."
    else:
        summary = f"No major qualitative catalysts detected for {symbol}."

    return {
        "catalyst_score": final_score,
        "sentiment": sentiment,
        "catalyst_type": main_type,
        "confidence": 0.85,
        "summary": summary,
        "headlines_count": len(headlines),
        "provider": "heuristic"
    }


def call_gemini_api(
    symbol: str,
    headlines_text: str,
    corporate_context: Optional[Dict[str, Any]],
    api_key: str,
    model: str = "gemini-1.5-flash",
    timeout: int = 6
) -> Optional[Dict[str, Any]]:
    """Calls Google Gemini REST API to evaluate news catalyst."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
You are an expert Indian equity (NSE) analyst. Analyze the following news headlines and corporate context for stock '{symbol}' to assess its near-term swing catalyst (1-3 weeks).

Headlines:
{headlines_text}

Corporate Context:
{json.dumps(corporate_context or {})}

Evaluate the catalyst impact. Respond ONLY in valid JSON matching this schema:
{{
  "catalyst_score": <integer from 0 to 10, where 0 is catastrophic negative, 5 is neutral, 10 is transformative positive>,
  "sentiment": "<BULLISH, NEUTRAL, or BEARISH>",
  "catalyst_type": "<ORDER_WIN, EARNINGS, EXPANSION, REGULATORY_LEGAL, MANAGEMENT, or GENERAL>",
  "confidence": <float between 0.5 and 1.0>,
  "summary": "<1-sentence factual explanation of the catalyst driver>"
}}
"""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            cleaned = re.sub(r"```json\s*", "", raw_text).replace("```", "").strip()
            parsed = json.loads(cleaned)
            parsed["provider"] = "gemini"
            parsed["catalyst_score"] = max(0, min(10, int(parsed.get("catalyst_score", 5))))
            return parsed
    except Exception as e:
        logger.warning(f"Gemini API request failed for {symbol}: {e}")
    return None


def call_openai_api(
    symbol: str,
    headlines_text: str,
    corporate_context: Optional[Dict[str, Any]],
    api_key: str,
    model: str = "gpt-4o-mini",
    timeout: int = 6
) -> Optional[Dict[str, Any]]:
    """Calls OpenAI REST API to evaluate news catalyst."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    prompt = f"""
Analyze the news headlines for Indian equity '{symbol}' for swing trading catalyst:
{headlines_text}
Corporate Context: {json.dumps(corporate_context or {})}

Return JSON only:
{{
  "catalyst_score": <int 0 to 10>,
  "sentiment": "<BULLISH, NEUTRAL, or BEARISH>",
  "catalyst_type": "<ORDER_WIN, EARNINGS, EXPANSION, REGULATORY_LEGAL, MANAGEMENT, or GENERAL>",
  "confidence": <float 0.5 to 1.0>,
  "summary": "<one sentence explanation>"
}}
"""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_text)
            parsed["provider"] = "openai"
            parsed["catalyst_score"] = max(0, min(10, int(parsed.get("catalyst_score", 5))))
            return parsed
    except Exception as e:
        logger.warning(f"OpenAI API request failed for {symbol}: {e}")
    return None


def analyze_catalyst_with_llm(
    symbol: str,
    headlines: List[Dict[str, str]],
    corporate_context: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for qualitative catalyst evaluation.
    Tries configured LLM API (Gemini or OpenAI) if available and not offline.
    Gracefully falls back to heuristic evaluation with zero downtime or hallucination risk.
    """
    sym = symbol.strip().upper().replace(".NS", "")

    if offline:
        res = heuristic_catalyst_evaluation(sym, headlines, corporate_context)
        res["headlines_count"] = len(headlines)
        return res

    llm_cfg = (config or {}).get("llm", {})
    provider = llm_cfg.get("provider", "gemini").lower()
    headlines_text = "\n".join([f"- [{h.get('source', 'News')}] {h.get('title', '')}" for h in headlines])

    # 1. Try Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if (provider == "gemini" or not os.environ.get("OPENAI_API_KEY")) and gemini_key:
        model = llm_cfg.get("model", "gemini-1.5-flash")
        parsed = call_gemini_api(sym, headlines_text, corporate_context, gemini_key, model=model)
        if parsed:
            parsed["headlines_count"] = len(headlines)
            return parsed

    # 2. Try OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        model = llm_cfg.get("model", "gpt-4o-mini")
        parsed = call_openai_api(sym, headlines_text, corporate_context, openai_key, model=model)
        if parsed:
            parsed["headlines_count"] = len(headlines)
            return parsed

    # 3. Deterministic heuristic fallback
    res = heuristic_catalyst_evaluation(sym, headlines, corporate_context)
    res["headlines_count"] = len(headlines)
    return res
