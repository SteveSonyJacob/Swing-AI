# SwingTrade AI — Multi-Agent Trading System

Deterministic multi-agent trading system for Indian equities (NSE).

- **Agent 1 — Screening Agent**: Screens and ranks Indian equities from **Moneycontrol.com** (Top Gainers, Volume Shockers, 52-Week Highs, Most Active Value, Earnings Catalysts) and **yfinance** (Universe batch scanner for EMA trend alignment, RSI swing sweet-spot, 20-day volume surge, and 52W high proximity) using a deterministic 0–100 candidate score.
- **Agent 2 — Technical Analysis Engine**: Evaluates price trends across daily and hourly timeframes, momentum, volume, breakouts (zero look-ahead bias), key S/R levels, and risk/reward setups.
- **Agent 3 — Fundamental Analysis Engine**: Evaluates quarterly & annual financial statements, revenue/PAT growth, profitability (ROE, ROCE, margins), balance sheet leverage, cash flow quality (OCF, FCF, OCF/PAT), earnings quality, and valuation multiples relative to sector medians.

---

## 1. Project Layout

```text
SwingTrade AI/
├── config/
│   ├── settings.yaml                 # Agent 2 settings & weights
│   ├── fundamental_settings.yaml     # Agent 3 settings, sector medians & weights
│   └── screening_settings.yaml       # Agent 1 settings, universes, filters & weights
├── data/
│   ├── raw/                          # Cached market, screening & financial data
│   └── processed/
├── outputs/
│   └── examples/
│       ├── screening_candidates.json # Agent 1 Screening output
│       ├── reliance_analysis.json    # Agent 2 Technical output
│       └── reliance_fundamental.json # Agent 3 Fundamental output
├── src/
│   ├── screening/                    # Agent 1 modules
│   │   ├── main.py                   # Screening CLI and pipeline
│   │   ├── sources/                  # Moneycontrol scraper & yfinance batch scanner
│   │   ├── filters/                  # Technical, volume, liquidity, catalyst filters
│   │   ├── scoring/                  # 0-100 candidate scoring engine
│   │   └── output/                   # JSON formatter, table printer, pipeline dispatcher
│   ├── analysis/                     # Agent 2 technical analysis modules
│   ├── indicators/                   # Moving averages, momentum, volume, volatility
│   ├── scoring/                      # Agent 2 technical scoring
│   ├── risk/                         # Trade levels & stop-loss / targets
│   └── fundamental/                  # Agent 3 modules
│       ├── main.py                   # Fundamental CLI
│       ├── data/                     # Financial statements & valuation metrics
│       ├── ratios/                   # Financial ratios (ROE, ROCE, D/E)
│       ├── analysis/                 # Growth, profitability, balance sheet, cash flow
│       ├── scoring/                  # 100-point fundamental scoring
│       └── output/                   # JSON formatter & LLM explainer
├── tests/
│   ├── conftest.py
│   ├── screening/                    # Agent 1 screening tests (19 tests)
│   ├── test_*.py                     # Agent 2 technical tests (17 tests)
│   └── fundamental/                  # Agent 3 fundamental tests (17 tests)
├── run_screening.py                  # CLI runner for Agent 1
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

### Agent 1: Screening Agent
```bash
# Run market screening across Moneycontrol and yfinance for NIFTY 50
python run_screening.py --universe nifty50 --min-score 60

# Screen only from Moneycontrol (Volume Shockers, 52W Highs, Top Gainers)
python run_screening.py --source moneycontrol --top-n 10

# Screen only from yfinance
python run_screening.py --source yfinance --universe nifty_next50

# Run offline with deterministic synthetic market data
python run_screening.py --offline --min-score 50

# Output pure JSON
python run_screening.py --offline --json-only

# End-to-End Multi-Agent Pipeline:
# Screen candidates with Agent 1 and pipe top setups directly into Agent 2 & Agent 3
python run_screening.py --offline --run-agents --top-n 3
```

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

Run all 53 automated unit tests:
```bash
pytest -v tests/
```

Run only Agent 1 screening unit tests:
```bash
pytest -v tests/screening/
```

---

## 5. Continuous Integration (GitHub Actions)

Continuous integration is configured in [`.github/workflows/agent_1_ci.yml`](.github/workflows/agent_1_ci.yml) and runs on every push and pull request to `main`, as well as on manual dispatch:

- **Agent 1 Dedicated Job**: Runs all 19 unit tests in `tests/screening/` and offline CLI smoke tests (table format, pure JSON, and multi-agent pipeline forwarding).
- **Full System Matrix Job**: Runs the entire 53-test suite across Python 3.11 and Python 3.12 on `ubuntu-latest`.

