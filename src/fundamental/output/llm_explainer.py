"""LLM prompt generator and rule-based explanation layer conforming to Section 24."""

from typing import Dict, Any


def generate_explanation_text(data: Dict[str, Any]) -> str:
    """
    Generates a structured, fact-grounded natural language explanation
    matching the format specified in Section 24.
    """
    score = data.get("fundamental_score", 0)
    growth = data.get("growth", {})
    prof = data.get("profitability", {})
    bs = data.get("balance_sheet", {})
    cf = data.get("cash_flow", {})
    val = data.get("valuation", {})
    events = data.get("events", {})
    warnings = data.get("warnings", [])

    lines = [
        f"Fundamental Score: {score}/100",
        "",
        "Growth:",
        f"Revenue YoY: {growth.get('revenue_yoy')}% | PAT YoY: {growth.get('pat_yoy')}% | EPS YoY: {growth.get('eps_yoy')}%.",
        f"3-Year Revenue CAGR: {growth.get('revenue_cagr_3y')}% | PAT CAGR: {growth.get('pat_cagr_3y')}%.",
        "",
        "Profitability:",
        f"ROE: {prof.get('roe')}% | ROCE: {prof.get('roce')}%.",
        f"Operating Margin: {prof.get('operating_margin')}% | Net Margin: {prof.get('net_margin')}%. Margin trend is {prof.get('margin_trend')}.",
        "",
        "Balance Sheet:",
        f"Debt/Equity: {bs.get('debt_equity')} | Interest Coverage: {bs.get('interest_coverage')}x | Current Ratio: {bs.get('current_ratio')}.",
        "",
        "Cash Flow:",
        f"Operating Cash Flow: {cf.get('operating_cash_flow')} | Free Cash Flow: {cf.get('free_cash_flow')}.",
        f"Cash conversion (OCF/PAT): {cf.get('ocf_pat_ratio')}x ({cf.get('cash_flow_trend')} cash flow trend).",
        "",
        "Valuation:",
        f"P/E: {val.get('pe')} vs Sector P/E: {val.get('sector_pe')} (Assessment: {val.get('valuation_assessment')}).",
    ]

    if events.get("upcoming_results"):
        lines.extend([
            "",
            "Upcoming Event:",
            f"Earnings results are expected in {events.get('days_to_results')} days."
        ])

    if warnings:
        lines.extend([
            "",
            "Warnings:",
            *[f"- {w}" for w in warnings]
        ])

    return "\n".join(lines)
