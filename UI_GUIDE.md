# Swing-AI — User Interface Guide

A minimal, professional, desktop-first research terminal for Indian equities (NSE), built with **FastAPI** and modern vanilla web technologies (HTML5, CSS3, ES6 JavaScript).

---

## 1. Quick Start

### Prerequisites
Make sure your Python environment has the required packages installed:
```bash
pip install fastapi uvicorn jinja2 requests pandas numpy pyyaml yfinance
```

### Starting the UI
Run the dedicated UI launcher from the project root:
```bash
python run_ui.py
```
Or specify a custom host or port:
```bash
python run_ui.py --host 127.0.0.1 --port 8000
```

Once running, navigate to:
- **Web UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 2. Architecture & Design Principles

- **True Backend Integration:** Directly calls real Python analysis pipelines (`run_single_stock()`, `run_pipeline()`, `run_screening()`, `pipe_to_agents()`). No mock calculations, no fake P&L, no fabricated data.
- **Market-Wide NSE Stock Discovery:** Agent 1 discovers ordinary equities across the entire National Stock Exchange (`EQ` and `BE` series, ~2,575 securities) without index constraints.
- **Decoupled Scoring:** In adherence to the system architecture, Agent 1 discovers stocks without computing screening scores or ranking candidates. Scoring and confirmation gates belong exclusively to:
  - **Agent 2:** Technical Swing Analysis Engine (Trend, Momentum, Volume, S/R, Breakouts)
  - **Agent 3:** Fundamental Analysis Engine (Growth, Margins, Health, Valuation, Ownership)
  - **Decision Engine:** Gated Confirmation Engine (Composite Score, Gated Verdicts)
- **Non-Blocking Background Execution:** Long-running market scans run asynchronously in background workers via `ScanManager`, with real-time status polling so the interface remains fast and responsive.
- **Local Persistence:** Completed analyses are saved locally in `data/analysis_history.json`, allowing instant reopening from the Analysis History view.

---

## 3. Application Views & Features

### A. Overview Dashboard
- **Key Metrics:** Discovered NSE equities, Universe coverage status (`COMPLETE` / `CACHED` / `PARTIAL`), number of analyzed stocks, and confirmed setup counts.
- **Quick Actions:** Instant shortcuts to run a broad market scan, analyze an individual stock, or refresh the official NSE master security list.
- **Recent Analysis Results:** Compact table of the most recent multi-agent evaluations with quick "Inspect" action.

### B. Market Scanner
- **Scanner Controls:**
  - Mode selection: `Offline` (deterministic synthetic market data) or `Live` (real exchange & Yahoo Finance data).
  - Configurable `max_symbols` to evaluate downstream through Agent 2 and Agent 3 (default: 10).
  - "Force Re-fetch Official NSE Master" toggle.
  - Background scan runner with real-time status and elapsed time indicators.
- **Universe Diagnostics:** Real-time summary of the data source, coverage status, cache age, allowed series (`EQ`, `BE`), and excluded non-equity instruments (debt, preference, ETFs/mutual funds).
- **Discovered Equities Browser:** Searchable and paginated table browsing through all 2,500+ discovered NSE equities, with one-click "Analyze Deeply" for any individual stock.
- **Downstream Multi-Agent Results:** Displays the pipeline evaluation results (Technical Score, Fundamental Score, Composite Score, Verdict, Entry Zone, Stop Loss, Target 1).

### C. Stock Analysis
- **Symbol Input:** Analyze any valid NSE symbol (e.g. `RELIANCE`, `INFY`, `TCS`, `360ONE`, `ZOMATO`).
- **Gated Composite Verdict Banner:**
  - Final Decision Engine Verdict badge (`STRONG_BUY_CANDIDATE`, `MODERATE_BUY_CANDIDATE`, `WATCHLIST_WAIT_FOR_SETUP`, `NOT_RECOMMENDED`, `SPECULATIVE_TECHNICAL_ONLY`, `REJECTED_BEARISH`, `INSUFFICIENT_DATA_HOLD`).
  - Action Badge: `BUY`, `WATCH`, `AVOID`, or `HOLD`.
  - Confidence Level: `HIGH`, `MEDIUM`, or `LOW`.
  - Setup Direction: `LONG` or `NONE`.
  - Composite Decision Score (`/100`).
  - Decision Engine Rationale explaining why confirmation rules passed or failed.
- **Agent Evaluations Bar:**
  - Agent 1: Discovery Status (`Eligible Ordinary Equity · NSE`).
  - Agent 2: Technical Swing Score (`/100`) and trend alignment.
  - Agent 3: Fundamental Quality Score (`/100`) and financial assessment.
- **Decision Engine 100-Point Scoring Rubrics Card:**
  - **1. Technical Foundation (30 pts):** Multi-timeframe trend synchronization, dual EMA stack alignment, and breakout confirmation.
  - **2. Fundamental Health & Safety (25 pts):** Revenue & PAT growth momentum, ROE/ROCE capital efficiency, solvency & D/E safety.
  - **3. Momentum & Volume (20 pts):** RSI in ideal swing zone (50-68), MACD dual alignment, and institutional RVOL volume surge.
  - **4. Risk / Reward Geometry (15 pts):** Setup asymmetry (>= 2.5:1, >= 2.0:1, >= 1.5:1) and ATR risk buffer.
  - **5. Valuation & Catalyst (10 pts):** Sector-relative multiple discount/fairness and corporate news catalyst sentiment.
  - **Capital Allocation Guidance:** Concrete position sizing recommendation (e.g. standard 2-3% risk, 1-1.5% conservative, 0.5% speculative, or 0% monitor).
  - **Confirmation Verification Gates:** Real-time checklist across 7 multi-agent gates (Daily trend, Hourly alignment, Volume surge, RSI sweet-spot, Fundamental health, R:R viability, Accounting cleanliness).
- **Interactive Price & Indicator Chart:**
  - Real daily price series with moving average overlays: **EMA 20** (blue), **EMA 50** (amber), **EMA 200** (red).
  - Subchart for **RSI (14)** with 30 and 70 overbought/oversold levels.
- **Detailed Two-Column Breakdown:**
  - **Agent 2 Technical Setup:** Daily and hourly trend, RSI, MACD, RVOL, Key Support/Resistance, Entry Zone, Stop Loss, Target 1 & 2, Risk/Reward ratio.
  - **Agent 3 Fundamental Quality:** Revenue & PAT YoY growth, ROE & ROCE, Operating Margin, Debt/Equity & Current Ratio, P/E vs Sector P/E, Promoter & Institutional ownership, and Risk warnings.
- **Catalyst & News Analysis:** Displays qualitative news and order-win analysis when enabled.

### D. Analysis History
- Persistent, searchable archive of past analyses saved in `data/analysis_history.json`.
- Displays Timestamp, Symbol, Action, Verdict, Technical Score, Fundamental Score, Decision Score, and Mode.
- One-click **"Reopen"** action loads that analysis record instantly without re-running.

---

## 4. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the HTML5 terminal interface |
| `GET` | `/api/health` | System health, universe cache status, and scanner status |
| `GET` | `/api/screening/universe` | Searchable & paginated discovered NSE equity symbols |
| `POST` | `/api/screening/refresh` | Force re-downloads official NSE security master archive |
| `POST` | `/api/screening/scan` | Initiates background multi-agent market scan |
| `GET` | `/api/screening/status` | Current scan progress and lifecycle state |
| `GET` | `/api/screening/results` | Results of the latest market scan |
| `POST` | `/api/analysis/{symbol}` | Executes multi-agent analysis for a specific symbol |
| `GET` | `/api/analysis/{symbol}/latest`| Retrieves latest saved analysis for symbol |
| `GET` | `/api/chart/{symbol}` | Returns daily OHLC and indicator series (EMA, RSI, MACD) |
| `GET` | `/api/history` | Returns saved analysis records list |
| `GET` | `/api/history/{id}` | Retrieves full analysis payload by record ID |

---

## 5. CLI Commands Reference

All existing CLI tools remain functional alongside the UI:

- **Launch UI:** `python run_ui.py`
- **Run Multi-Agent Pipeline:** `python run_all.py --offline --top-n 5`
- **Single Stock Deep Analysis:** `python run_all.py --symbol RELIANCE --offline`
- **Screening Discovery CLI:** `python run_screening.py --offline`
- **Technical Engine CLI:** `python run_technical.py --symbol INFY --offline`
- **Fundamental Engine CLI:** `python run_fundamental.py --symbol INFY --offline`
- **Automated Tests:** `python -m pytest -v` (100 tests passing)
