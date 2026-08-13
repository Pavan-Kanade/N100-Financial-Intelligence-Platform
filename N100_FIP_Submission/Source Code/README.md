# Nifty 100 Financial Intelligence Platform

A production-grade financial analytics, stock screener, peer comparison, and valuation platform built for the Nifty 100 universe of companies.

---

## 🚀 Quick Start & Dashboard Execution

### 1. Environment Setup & Dependencies
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Data Pipeline (ETL, Ratios, Peer Engine, Valuation)
```bash
python -m src.etl.loader
python -m src.analytics.engine
python -m src.analytics.peer
python -m src.analytics.valuation
```

### 3. Launch Streamlit Web Dashboard
```bash
streamlit run src/dashboard/app.py
```
*The interactive dashboard will automatically open in your browser at `http://localhost:8501`.*

---

## 📊 Dashboard Modules & Screen Guide

| Screen # | Name | Description | Key Features |
| :---: | :--- | :--- | :--- |
| **01** | **Home Overview** | Executive summary & market vitals | 6 summary KPI tiles, Plotly sector donut chart, Top 5 quality compounder table, year selector (2019-2024). |
| **02** | **Company Profile** | 10-year deep dive per company | Ticker search/autocomplete, profile card, 6 KPI tiles, Revenue/PAT dual bars, ROE/ROCE trajectory lines, pros & cons badges. |
| **03** | **Financial Screener** | Multi-criteria stock filtering | 10 metric sliders, 6 preset templates (Quality, Value, Growth, Dividend, Debt-Free, Turnaround), live result count, CSV download. |
| **04** | **Peer Comparison** | Sector peer benchmark engine | 11 peer group selector, Scatterpolar radar chart overlay vs peer average, side-by-side KPI table with gold benchmark highlight. |
| **05** | **Trend Analysis** | Multi-year metric trajectory | Overlay up to 3 metrics on 10-year line chart with YoY % change data point annotations. |
| **06** | **Sector Analysis** | Industry-level benchmarking | Bubble chart (Revenue vs ROE, size = Market Cap, color = Sub-sector), sector median KPI bar chart. |
| **07** | **Capital Allocation** | 8-pattern capital classifier | Treemap of all 92 companies by capital allocation pattern with interactive drill-down. |
| **08** | **Annual Reports** | Annual report PDF repository | Ticker search, annual report archive links to BSE PDFs with status badges. |

---

## 💎 Valuation Module (`src/analytics/valuation.py`)

Computes FCF Yield %, 5-Year Historical Median P/E, Broad Sector Median P/E, and assigns valuation status flags:
- **Caution**: `P/E > 1.5x Sector Median`
- **Discount**: `P/E < 0.7x Sector Median`
- **Fair**: Normal valuation range

### Valuation Deliverables:
- `output/valuation_summary.xlsx` — 92 companies with complete valuation multiples & color-coded flags.
- `output/valuation_flags.csv` — Filtered list of Caution and Discount flagged stocks.

---

## 🧪 Running Automated Tests

Run the full pytest suite across ETL, KPI, Screener, Peer, Valuation, and Dashboard modules:
```bash
pytest tests/ -v --tb=short
```

Expected output: **100+ tests passing (0 failures)**.
