# Agent 3 — Fundamental Analysis Engine
## Implementation Plan

## 1. Objective

Build a deterministic fundamental-analysis agent for the swing-trading system.

The agent receives a stock symbol and analysis date, collects the latest financial statements, ratios, valuation data, earnings history, and relevant company information, then produces:

- Fundamental metrics
- Growth analysis
- Profitability analysis
- Balance-sheet analysis
- Cash-flow analysis
- Earnings-quality analysis
- Valuation analysis
- Management/corporate-event context where reliable data is available
- A 0–100 fundamental score
- A structured JSON output
- Optional LLM-generated explanation

The fundamental agent should **not predict the stock price directly**. It should assess the company's underlying financial quality and valuation using information that was available as of the analysis date.

---

# 2. Important Design Principle

Fundamental analysis is different from technical analysis.

Technical Agent:

```text
"What is happening with the stock price?"
```

Fundamental Agent:

```text
"How financially healthy is the company,
how quickly is it growing, and how is it valued?"
```

The fundamental agent should therefore avoid using:

- RSI
- MACD
- EMA
- Chart patterns
- Short-term price momentum

Those belong to Agent 2.

The only market-price information needed here is primarily for valuation and relative valuation.

---

# 3. Scope

## V1 — Core Fundamental Analysis

Implement:

- Company identification
- Latest quarterly results
- Previous-quarter comparison
- Year-over-year comparison
- Annual financial statements
- Revenue growth
- EBITDA/operating-profit growth
- PAT growth
- EPS growth
- Operating margin
- Net profit margin
- ROE
- ROCE
- Debt/equity
- Interest coverage
- Operating cash flow
- Free cash flow
- Basic valuation
- Fundamental score
- Structured JSON output

## V2 — Advanced Fundamental Analysis

Add:

- 3Y/5Y CAGR
- Margin trend
- Cash-flow quality
- Working-capital analysis
- Promoter/institutional ownership changes
- Share dilution
- Pledged shares
- Sector-relative valuation
- Historical valuation
- Earnings consistency
- Dividend/buyback information
- Corporate actions
- Management guidance
- Order book/revenue visibility where applicable

## V3 — Fundamental Event Analysis

Integrate:

- Upcoming earnings
- Recent earnings announcement
- Earnings surprise
- Guidance changes
- Major contracts
- Capex announcements
- Acquisitions
- Regulatory approvals
- Demergers
- Fundraising
- Credit-rating changes

## V4 — Historical Backtesting

Determine whether the fundamental score contains useful information for the overall swing-trading system.

---

# 4. Architecture

```text
                    Stock Symbol
                         |
                         v
                +-------------------+
                | Company Resolver  |
                +---------+---------+
                          |
                          v
                +-------------------+
                | Financial Data    |
                | Acquisition       |
                +---------+---------+
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
     Income Statement  Balance Sheet   Cash Flow
          |               |                |
          +---------------+----------------+
                          |
                          v
                +-------------------+
                | Ratio Calculator  |
                +---------+---------+
                          |
                          v
                +-------------------+
                | Growth Analysis   |
                +---------+---------+
                          |
                          v
                +-------------------+
                | Earnings Quality  |
                +---------+---------+
                          |
                          v
                +-------------------+
                | Valuation Engine  |
                +---------+---------+
                          |
                          v
                +-------------------+
                | Sector Comparison |
                +---------+---------+
                          |
                          v
                +-------------------+
                | Scoring Engine    |
                +---------+---------+
                          |
                          v
                +-------------------+
                | JSON Formatter    |
                +---------+---------+
                          |
                          v
                  Agent 3 Output
```

Optional:

```text
Agent 3 JSON
      |
      v
LLM Explanation Layer
      |
      v
Human-readable fundamental analysis
```

---

# 5. Recommended Project Structure

```text
fundamental-agent/
│
├── README.md
├── plan.md
├── requirements.txt
├── .env
├── .gitignore
│
├── config/
│   └── settings.yaml
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── main.py
│   │
│   ├── data/
│   │   ├── company_data.py
│   │   ├── financial_data.py
│   │   ├── market_data.py
│   │   └── validator.py
│   │
│   ├── analysis/
│   │   ├── growth.py
│   │   ├── profitability.py
│   │   ├── balance_sheet.py
│   │   ├── cash_flow.py
│   │   ├── earnings_quality.py
│   │   ├── valuation.py
│   │   └── ownership.py
│   │
│   ├── ratios/
│   │   └── financial_ratios.py
│   │
│   ├── scoring/
│   │   └── fundamental_score.py
│   │
│   ├── events/
│   │   └── corporate_events.py
│   │
│   └── output/
│       └── formatter.py
│
├── tests/
│   ├── test_data.py
│   ├── test_ratios.py
│   ├── test_growth.py
│   ├── test_profitability.py
│   ├── test_cash_flow.py
│   ├── test_valuation.py
│   └── test_scoring.py
│
└── outputs/
    └── examples/
```

---

# 6. Data Acquisition

The agent needs reliable financial data.

## Required

### Income statement

At minimum:

- Revenue
- EBITDA / operating profit
- EBIT
- PBT
- PAT
- EPS
- Interest expense
- Depreciation

### Balance sheet

At minimum:

- Total assets
- Total liabilities
- Equity
- Total debt
- Cash
- Current assets
- Current liabilities
- Receivables
- Inventory

### Cash flow

At minimum:

- Operating cash flow
- Investing cash flow
- Financing cash flow
- Capital expenditure
- Free cash flow

### Market/valuation data

- Current share price
- Shares outstanding
- Market capitalization
- P/E
- P/B
- EV/EBITDA
- Dividend yield where available

### Company information

- Sector
- Industry
- Market capitalization category
- Business description

---

# 7. Data Sources

Use reliable and legally accessible sources.

For an Indian-stock implementation, possible data sources include:

- Exchange/company filings
- Official company investor-relations pages
- SEBI-related filings
- NSE/BSE data
- Licensed market-data APIs
- Financial-data providers

Prefer **primary company filings** for financial statements and earnings announcements.

Avoid making a low-quality scraped website the sole source for important financial information.

The system should store the source and reporting period for every metric.

---

# 8. Point-in-Time Data

This is critical.

If the analysis date is:

```text
2026-09-18
```

the engine must not use financial information published after:

```text
2026-09-18
```

For historical backtesting, use:

```text
publication date
```

rather than simply:

```text
financial period end date
```

Example:

```text
Quarter ended:       30 Jun 2025
Results published:   14 Aug 2025
```

The result should not be available to a simulated analysis dated:

```text
01 Aug 2025
```

This prevents look-ahead bias.

---

# 9. Quarterly Growth Analysis

Calculate year-over-year growth.

## Revenue

```text
Revenue Growth =
(Current Quarter Revenue - Same Quarter Previous Year Revenue)
/
Same Quarter Previous Year Revenue × 100
```

## PAT

```text
PAT Growth =
(Current PAT - Same Quarter Previous Year PAT)
/
Same Quarter Previous Year PAT × 100
```

## EPS

Calculate similarly.

Also calculate sequential growth:

```text
Current Quarter vs Previous Quarter
```

Do not confuse:

```text
QoQ
```

with:

```text
YoY
```

Both should be stored separately.

---

# 10. Long-Term Growth

Calculate:

- 3-year revenue CAGR
- 5-year revenue CAGR
- 3-year PAT CAGR
- 5-year PAT CAGR
- 3-year EPS CAGR
- 5-year EPS CAGR

CAGR:

```text
CAGR =
(Ending Value / Beginning Value)^(1 / Years) - 1
```

Growth should be considered alongside profitability and cash flow.

High revenue growth with deteriorating margins should not receive the same treatment as profitable growth.

---

# 11. Profitability Analysis

Calculate:

## Operating margin

```text
Operating Margin =
Operating Profit / Revenue × 100
```

## Net margin

```text
Net Margin =
PAT / Revenue × 100
```

## ROE

```text
ROE =
Net Income / Average Shareholders' Equity × 100
```

## ROCE

Use a consistent definition throughout the system.

For example:

```text
ROCE =
EBIT / Capital Employed × 100
```

Track both:

```text
Current margin
Historical margin
Margin trend
```

Example:

```text
Operating Margin

2024: 15.2%
2025: 17.1%
2026: 18.4%

→ Improving
```

Do not judge a margin without considering the company's industry.

---

# 12. Balance-Sheet Analysis

Calculate:

### Debt/equity

```text
Debt / Equity
```

### Net debt

```text
Total Debt - Cash
```

### Interest coverage

```text
EBIT / Interest Expense
```

### Current ratio

```text
Current Assets / Current Liabilities
```

Also inspect:

- Debt trend
- Cash trend
- Receivables trend
- Inventory trend
- Equity trend

A company becoming more profitable while debt and receivables are growing unusually quickly should trigger an earnings-quality review.

---

# 13. Cash-Flow Analysis

This should be a major part of the agent.

Calculate:

- Operating cash flow
- Free cash flow
- OCF / PAT
- FCF margin
- OCF growth

## Earnings-to-cash conversion

```text
OCF / PAT
```

Example:

```text
PAT = ₹1,000 Cr
OCF = ₹1,100 Cr

OCF/PAT = 1.10
```

Compare this over multiple years.

Potential warning:

```text
PAT consistently rising
but
OCF consistently weak/negative
```

This should reduce the earnings-quality score and generate a warning, not automatically label the company as fraudulent or poor-quality.

---

# 14. Earnings Quality

Create a dedicated module.

Check:

- PAT growth vs OCF growth
- Revenue growth vs receivables growth
- Margin changes
- One-time gains
- Exceptional items
- Tax-rate changes
- Other income contribution
- Debt-funded growth
- Working-capital changes

Example:

```text
Revenue       +20%
PAT           +35%
OCF           +32%
Receivables   +8%

→ Stronger earnings-quality profile
```

versus:

```text
Revenue       +8%
PAT           +30%
OCF           -15%
Receivables   +35%

→ Earnings-quality warning
```

The system should surface the underlying numbers so the user can inspect them.

---

# 15. Valuation Engine

Calculate:

- P/E
- Forward P/E where reliable forward estimates exist
- P/B
- EV/EBITDA
- PEG where meaningful
- Dividend yield

Valuation must be compared against:

### Historical valuation

Example:

```text
Current P/E = 28
5Y median P/E = 22

Premium = 27%
```

### Sector valuation

Example:

```text
Company P/E = 28
Sector median P/E = 24

Premium = 16.7%
```

Do not automatically interpret a premium valuation as bad.

A high-quality, fast-growing company can trade at a premium.

The score should consider:

```text
Growth + Profitability + Valuation
```

together.

---

# 16. Sector-Aware Analysis

Fundamental metrics differ significantly across sectors.

For example:

```text
Bank
→ ROA
→ ROE
→ NIM
→ GNPA
→ NNPA
→ Capital adequacy

IT
→ Revenue growth
→ EBIT margin
→ Deal wins
→ Utilization
→ Attrition

Manufacturing
→ ROCE
→ Debt
→ Capacity utilization
→ Order book
→ Operating margin
```

V1 should use a common cross-sector framework.

V2 should introduce sector-specific metrics.

Do not compare raw financial ratios across unrelated industries without normalization.

---

# 17. Upcoming Results / Earnings Context

Agent 1 may identify:

```text
Results in 2 days
```

Agent 3 should provide the **fundamental context** for that event.

Analyze:

- Previous 4 quarters
- Revenue trend
- PAT trend
- EPS trend
- Margin trend
- Management guidance
- Previous earnings surprises where reliable
- Current valuation
- Expectations if reliable data is available

Example:

```text
Previous 4 quarters:

Revenue: +12%, +15%, +18%, +20%
PAT:     +10%, +13%, +19%, +24%
Margin:  improving

Upcoming result:
2 days

Fundamental context:
Positive historical growth trend
```

Do not predict the exact result unless a separate forecasting model is explicitly developed and validated.

---

# 18. Corporate Events

Track relevant events:

- Major contracts
- Acquisitions
- Divestitures
- Capex
- Fundraising
- Buybacks
- Dividends
- Stock splits
- Bonus issues
- Regulatory approvals
- Credit-rating changes
- Promoter transactions

These events can be passed from Agent 1 or independently retrieved.

Avoid double-counting the same catalyst in both the fundamental and news scores.

---

# 19. Ownership Analysis — V2

For Indian stocks, optionally calculate:

- Promoter holding
- Promoter holding change
- Promoter pledged shares
- FII holding
- DII holding
- Institutional holding change

Example:

```text
Promoter holding:
Q1 → 52.1%
Q2 → 52.4%
Q3 → 52.7%
```

Store the trend rather than treating one-quarter changes as definitive signals.

---

# 20. Fundamental Score

Initial scoring:

| Component | Points |
|---|---:|
| Revenue/Earnings Growth | 20 |
| Profitability | 15 |
| Balance Sheet | 15 |
| Cash Flow | 15 |
| Earnings Quality | 10 |
| Valuation | 15 |
| Consistency | 5 |
| Sector-relative position | 5 |
| **Total** | **100** |

## Suggested breakdown

### Growth — 20

Consider:

- Revenue growth
- PAT growth
- EPS growth
- Long-term CAGR

### Profitability — 15

Consider:

- ROE
- ROCE
- Operating margin
- Net margin
- Margin trend

### Balance Sheet — 15

Consider:

- Debt/equity
- Net debt
- Interest coverage
- Liquidity

### Cash Flow — 15

Consider:

- OCF
- FCF
- OCF/PAT
- Cash-flow trend

### Earnings Quality — 10

Consider:

- OCF vs PAT
- Receivables
- One-time items
- Other income
- Working capital

### Valuation — 15

Consider:

- P/E
- EV/EBITDA
- P/B
- Historical valuation
- Sector valuation

### Consistency — 5

Consider:

- Consistent revenue growth
- Consistent earnings
- Stable/improving margins
- Consistent cash generation

### Sector-relative — 5

Compare relevant metrics against the company's sector.

---

# 21. Valuation Should Not Dominate the Score

Avoid simplistic rules such as:

```text
P/E < 20 = good
P/E > 30 = bad
```

Instead:

```text
Growth
+
Profitability
+
Balance Sheet
+
Cash Flow
+
Valuation
```

should be considered together.

Example:

```text
Company A
Growth:          Very strong
ROCE:            Very strong
Debt:            Low
Cash flow:       Strong
P/E:             High

→ Expensive valuation should be reflected
  without automatically eliminating the company.
```

---

# 22. Missing Data Handling

Financial datasets often contain missing or differently defined metrics.

Never substitute:

```text
missing = 0
```

Instead:

```json
{
  "roe": null,
  "roe_status": "unavailable"
}
```

The scoring engine should normalize scores based on available components or mark the analysis as incomplete.

Every metric should also have:

```text
value
period
source
definition
```

where practical.

---

# 23. Output Schema

Example:

```json
{
  "status": "success",
  "symbol": "XYZ",
  "market": "NSE",
  "analysis_timestamp": "2026-09-18T00:00:00+05:30",

  "fundamental_score": 82,

  "score_breakdown": {
    "growth": 18,
    "profitability": 13,
    "balance_sheet": 14,
    "cash_flow": 13,
    "earnings_quality": 8,
    "valuation": 8,
    "consistency": 4,
    "sector_relative": 4
  },

  "growth": {
    "revenue_yoy": 18.2,
    "pat_yoy": 31.4,
    "eps_yoy": 29.8,
    "revenue_cagr_3y": 15.7,
    "pat_cagr_3y": 21.3
  },

  "profitability": {
    "roe": 21.3,
    "roce": 24.8,
    "operating_margin": 18.4,
    "net_margin": 12.7,
    "margin_trend": "improving"
  },

  "balance_sheet": {
    "debt_equity": 0.18,
    "net_debt": 120,
    "interest_coverage": 12.4,
    "current_ratio": 1.72
  },

  "cash_flow": {
    "operating_cash_flow": 1100,
    "free_cash_flow": 820,
    "ocf_pat_ratio": 1.10,
    "cash_flow_trend": "strong"
  },

  "earnings_quality": {
    "score": 8,
    "status": "strong",
    "warnings": []
  },

  "valuation": {
    "pe": 28.0,
    "pb": 4.1,
    "ev_ebitda": 18.2,
    "sector_pe": 24.0,
    "pe_premium_to_sector": 16.7,
    "valuation_assessment": "premium"
  },

  "events": {
    "upcoming_results": true,
    "days_to_results": 2
  },

  "warnings": [],

  "data_quality": {
    "status": "complete",
    "missing_metrics": []
  }
}
```

---

# 24. LLM Explanation Layer

After the deterministic engine is working, optionally send the JSON to an LLM.

The LLM prompt should be restrictive:

```text
You are a financial-analysis explanation assistant.

Use ONLY the supplied structured data.

Do not invent financial metrics.
Do not modify scores.
Do not predict a stock price.
Do not issue a guaranteed buy/sell recommendation.

Explain:
1. Growth
2. Profitability
3. Balance sheet
4. Cash flow
5. Earnings quality
6. Valuation
7. Important warnings
8. Upcoming earnings context

Clearly distinguish facts from interpretation.
```

Example output:

```text
Fundamental Score: 82/100

Growth:
Revenue and PAT have grown strongly over the recent periods.

Profitability:
ROE and ROCE are healthy, with operating margins improving.

Balance Sheet:
Debt remains relatively low and interest coverage is strong.

Cash Flow:
Operating cash flow is broadly consistent with reported earnings.

Valuation:
The company trades above its sector's median P/E, so valuation is a consideration despite the company's growth profile.

Upcoming Event:
Results are expected in 2 days.
```

---

# 25. Agent 3 API

A simple interface:

```text
POST /fundamental-analysis
```

Input:

```json
{
  "symbol": "RELIANCE",
  "market": "NSE",
  "analysis_date": "2026-09-18"
}
```

Output:

```json
{
  "status": "success",
  "symbol": "RELIANCE",
  "fundamental_score": 78,
  "...": "..."
}
```

This allows the orchestrator to call Agent 3 independently.

---

# 26. Integration With Agent 1 and Agent 2

The eventual system:

```text
                    Candidate Scanner
                          |
                    Candidate List
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
     Agent 1          Agent 2          Agent 3
     Catalyst         Technical       Fundamental
          |               |               |
          |          Technical Score     |
          |               |          Fundamental Score
          |               |               |
          +---------------+---------------+
                          |
                          v
                    Score Engine
                          |
                          v
                    Risk Engine
                          |
                          v
                 Final Opportunities
```

Avoid double counting.

For example:

```text
Agent 1:
Positive earnings announcement = catalyst

Agent 3:
Revenue/PAT growth = fundamental quality
```

These are related but represent different information.

---

# 27. Database Design

Store historical analyses.

Suggested table:

```text
fundamental_analysis
--------------------
id
symbol
analysis_timestamp
financial_period
revenue
revenue_growth
pat
pat_growth
eps
eps_growth
roe
roce
operating_margin
net_margin
debt_equity
interest_coverage
operating_cash_flow
free_cash_flow
ocf_pat_ratio
pe
pb
ev_ebitda
fundamental_score
growth_score
profitability_score
balance_sheet_score
cash_flow_score
earnings_quality_score
valuation_score
consistency_score
sector_relative_score
data_quality
source_metadata
```

This makes historical analysis and backtesting possible.

---

# 28. Testing Strategy

Unit-test every calculation.

Test:

- Revenue growth
- PAT growth
- CAGR
- ROE
- ROCE
- Debt/equity
- Interest coverage
- OCF/PAT
- Free cash flow
- P/E
- EV/EBITDA
- Sector premium
- Score calculation

Test edge cases:

```text
Negative earnings
Negative equity
Zero revenue
Zero interest expense
Negative free cash flow
Missing quarterly results
Stock splits
Bonus issues
Large one-time gains
Different fiscal years
Different sector accounting conventions
```

---

# 29. Backtesting

Backtest fundamental scores using only information available at the time.

For every historical analysis date:

```text
Fundamental data available at T
            |
            v
      Fundamental Score
            |
            v
    Future performance
```

Measure:

- 1-week return
- 2-week return
- 1-month return
- 3-month return
- Maximum drawdown
- Maximum favorable excursion
- Maximum adverse excursion

Do not optimize and evaluate on the same period.

Use:

```text
Training
Validation
Out-of-sample Test
```

---

# 30. Fundamental Score Calibration

The initial weights are hypotheses.

Do not assume:

```text
Growth = 20
Valuation = 15
```

is optimal.

After collecting historical results, test alternative weighting schemes.

Example:

```text
Configuration A
Growth 20
Profitability 15
...

Configuration B
Growth 25
Profitability 15
...

Configuration C
Growth 15
Cash Flow 20
...
```

Evaluate them on unseen data.

Do not select weights solely because they perform well on historical data; guard against overfitting.

---

# 31. Development Milestones

## Milestone 1 — Data Layer

- [ ] Choose financial-data sources
- [ ] Implement company lookup
- [ ] Implement quarterly financial retrieval
- [ ] Implement annual financial retrieval
- [ ] Implement market/valuation retrieval
- [ ] Store source metadata
- [ ] Add data validation

## Milestone 2 — Core Metrics

- [ ] Revenue growth
- [ ] PAT growth
- [ ] EPS growth
- [ ] CAGR
- [ ] ROE
- [ ] ROCE
- [ ] Operating margin
- [ ] Net margin
- [ ] Debt/equity
- [ ] Interest coverage
- [ ] Current ratio
- [ ] OCF
- [ ] FCF
- [ ] OCF/PAT

## Milestone 3 — Analysis

- [ ] Growth analysis
- [ ] Profitability analysis
- [ ] Balance-sheet analysis
- [ ] Cash-flow analysis
- [ ] Earnings-quality analysis
- [ ] Valuation analysis
- [ ] Sector comparison

## Milestone 4 — Scoring

- [ ] Implement 100-point score
- [ ] Implement component scores
- [ ] Make weights configurable
- [ ] Add data-quality adjustment
- [ ] Add warnings

## Milestone 5 — Events

- [ ] Upcoming earnings
- [ ] Previous earnings
- [ ] Guidance
- [ ] Corporate events
- [ ] Ownership changes

## Milestone 6 — Output/API

- [ ] JSON schema
- [ ] API endpoint
- [ ] Logging
- [ ] Error handling
- [ ] LLM explanation layer

## Milestone 7 — Backtesting

- [ ] Point-in-time dataset
- [ ] Historical scoring
- [ ] Forward-return calculation
- [ ] Score calibration
- [ ] Out-of-sample validation

---

# 32. Definition of Done

Agent 3 is ready for integration when:

- [ ] A stock symbol can be submitted programmatically
- [ ] Latest available financial data can be retrieved
- [ ] Historical quarterly and annual data are available
- [ ] Core financial ratios are calculated deterministically
- [ ] Growth, profitability, balance-sheet, cash-flow and valuation analyses are available
- [ ] Earnings quality is evaluated
- [ ] Sector context is included where data is available
- [ ] Fundamental score is reproducible
- [ ] Missing data is handled explicitly
- [ ] Every important metric has a reporting period/source
- [ ] No future information leaks into historical analysis
- [ ] JSON output follows a fixed schema
- [ ] Unit tests pass
- [ ] Historical backtesting is possible

---

# 33. Final Role of Agent 3

Agent 3 should produce:

```text
                FUNDAMENTAL QUALITY
                       |
        +--------------+--------------+
        |              |              |
      Growth       Financial       Valuation
                    Health
        |              |              |
        +--------------+--------------+
                       |
                       v
              Fundamental Score
                    /100
```

The score should answer:

> "How strong are the company's underlying fundamentals and how reasonable is its valuation, based on currently available information?"

It should then pass the structured result to the final system:

```text
Catalyst Score
      +
Technical Score
      +
Fundamental Score
      +
Risk Assessment
      |
      v
Final Opportunity Ranking
```

The final system should treat the fundamental score as **one component of a trading decision**, not as a standalone prediction of future returns.
