# SwingTrade AI — Multi-Agent Trading System

Deterministic multi-agent trading system for Indian equities (NSE).

- **Agent 2 — Technical Analysis Engine**: Evaluates price trends across daily and hourly timeframes, momentum, volume, breakouts (zero look-ahead bias), key S/R levels, and risk/reward setups.
- **Agent 3 — Fundamental Analysis Engine**: Evaluates quarterly & annual financial statements, revenue/PAT growth, profitability (ROE, ROCE, margins), balance sheet leverage, cash flow quality (OCF, FCF, OCF/PAT), earnings quality, and valuation multiples relative to sector medians.

---

## 1. Project Layout

```text
SwingTrade AI/
├── config/
│   ├── settings.yaml                 # Agent 2 settings & weights
│   └── fundamental_settings.yaml     # Agent 3 settings, sector medians & weights
├── data/
│   ├── raw/                          # Cached market & financial data
│   └── processed/
├── outputs/
│   └── examples/
│       ├── reliance_analysis.json    # Agent 2 Technical output
│       └── reliance_fundamental.json # Agent 3 Fundamental output
├── src/
│   ├── main.py                       # Technical analysis CLI (legacy/default)
│   ├── technical/                    # Agent 2 modules
│   └── fundamental/                  # Agent 3 modules
│       ├── main.py                   # Fundamental CLI
│       ├── data/
│       │   ├── company_data.py       # Profile & market cap tier
│       │   ├── financial_data.py     # Income Statement, Balance Sheet, Cash Flow
│       │   ├── market_data.py        # Valuation ratios (PE, PB, EV/EBITDA)
│       │   └── validator.py          # Missing data & quality tracker
│       ├── ratios/
│       │   └── financial_ratios.py   # ROE, ROCE, Margins, D/E, Interest Coverage
│       ├── analysis/
│       │   ├── growth.py             # YoY, QoQ, 3Y CAGR
│       │   ├── profitability.py      # Margins & margin trend
│       │   ├── balance_sheet.py      # Solvency & liquidity
│       │   ├── cash_flow.py          # OCF, FCF, cash conversion
│       │   ├── earnings_quality.py   # Red flag and accounting warning checks
│       │   ├── valuation.py          # Sector premium & valuation assessment
│       │   └── ownership.py          # Ownership structure
│       ├── events/
│       │   └── corporate_events.py   # Upcoming earnings calendar
│       ├── scoring/
│       │   └── fundamental_score.py  # 100-point scoring with missing-data normalization
│       └── output/
│           ├── formatter.py          # Section 23 JSON formatter
│           └── llm_explainer.py      # Natural language explanation generator
├── tests/
│   ├── conftest.py
│   ├── test_*.py                     # Agent 2 technical tests
│   └── fundamental/                  # Agent 3 fundamental tests
│       ├── test_financial_ratios.py
│       ├── test_growth.py
│       ├── test_cash_flow.py
│       ├── test_earnings_quality.py
│       ├── test_valuation.py
│       └── test_fundamental_score.py
├── run_technical.py                  # CLI runner for Agent 2
├── run_fundamental.py                # CLI runner for Agent 3
├── requirements.txt
└── README.md
```

---

## 2. Installation

```bash
pip install -r requirements.txt
```

---

## 3. Usage

### Agent 3: Fundamental Analysis Engine
```bash
# Run fundamental analysis for RELIANCE
python run_fundamental.py --symbol RELIANCE

# Run offline with cached/synthetic financials
python run_fundamental.py --symbol RELIANCE --offline

# Generate natural-language explanation
python run_fundamental.py --symbol RELIANCE --offline --explain

# Output pure JSON conforming to Section 23
python run_fundamental.py --symbol RELIANCE --offline --json-only
```

### Agent 2: Technical Analysis Engine
```bash
# Run technical analysis for RELIANCE
python run_technical.py --symbol RELIANCE

# Output pure JSON conforming to Section 19
python run_technical.py --symbol RELIANCE --offline --json-only
```

---

## 4. Testing

Run all 34 automated unit tests:
```bash
pytest -v tests/
```
