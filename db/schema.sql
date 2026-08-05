-- Nifty 100 Financial Intelligence Platform
-- SQLite Database Schema DDL (10+ tables)

PRAGMA foreign_keys = ON;

-- 1. Master Company Reference
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value NUMERIC,
    book_value NUMERIC,
    roce_percentage NUMERIC,
    roe_percentage NUMERIC
);

-- 2. Annual Profit & Loss Statements
CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales NUMERIC,
    expenses NUMERIC,
    operating_profit NUMERIC,
    opm_percentage NUMERIC,
    other_income NUMERIC,
    interest NUMERIC,
    depreciation NUMERIC,
    profit_before_tax NUMERIC,
    tax_percentage NUMERIC,
    net_profit NUMERIC,
    eps NUMERIC,
    dividend_payout NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 3. Annual Balance Sheet
CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital NUMERIC,
    reserves NUMERIC,
    borrowings NUMERIC,
    other_liabilities NUMERIC,
    total_liabilities NUMERIC,
    fixed_assets NUMERIC,
    cwip NUMERIC,
    investments NUMERIC,
    other_asset NUMERIC,
    total_assets NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 4. Annual Cash Flow Statements
CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_activity NUMERIC,
    investing_activity NUMERIC,
    financing_activity NUMERIC,
    net_cash_flow NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 5. Qualitative Growth Metrics (Partial Coverage)
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 6. Annual Report Documents Repository
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    annual_report TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 7. Qualitative Investment Insights
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 8. Company Sector Mapping
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER,
    company_id TEXT PRIMARY KEY,
    broad_sector TEXT NOT NULL,
    sub_sector TEXT NOT NULL,
    index_weight_pct NUMERIC,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 9. Monthly OHLCV Price History
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume INTEGER,
    adjusted_close NUMERIC,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 10. Computed Financial Ratios & KPI Table
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    net_profit_margin_pct NUMERIC,
    operating_profit_margin_pct NUMERIC,
    return_on_equity_pct NUMERIC,
    return_on_capital_employed_pct NUMERIC,
    return_on_assets_pct NUMERIC,
    debt_to_equity NUMERIC,
    high_leverage_flag INTEGER DEFAULT 0,
    interest_coverage NUMERIC,
    icr_label TEXT,
    icr_warning_flag INTEGER DEFAULT 0,
    net_debt_cr NUMERIC,
    asset_turnover NUMERIC,
    free_cash_flow_cr NUMERIC,
    capex_cr NUMERIC,
    capex_intensity_category TEXT,
    cfo_quality_score NUMERIC,
    cfo_quality_category TEXT,
    fcf_conversion_rate_pct NUMERIC,
    capital_allocation_pattern TEXT,
    earnings_per_share NUMERIC,
    book_value_per_share NUMERIC,
    dividend_payout_ratio_pct NUMERIC,
    total_debt_cr NUMERIC,
    cash_from_operations_cr NUMERIC,
    revenue_cagr_3yr NUMERIC,
    revenue_cagr_3yr_flag TEXT,
    revenue_cagr_5yr NUMERIC,
    revenue_cagr_5yr_flag TEXT,
    revenue_cagr_10yr NUMERIC,
    revenue_cagr_10yr_flag TEXT,
    pat_cagr_3yr NUMERIC,
    pat_cagr_3yr_flag TEXT,
    pat_cagr_5yr NUMERIC,
    pat_cagr_5yr_flag TEXT,
    pat_cagr_10yr NUMERIC,
    pat_cagr_10yr_flag TEXT,
    eps_cagr_3yr NUMERIC,
    eps_cagr_3yr_flag TEXT,
    eps_cagr_5yr NUMERIC,
    eps_cagr_5yr_flag TEXT,
    eps_cagr_10yr NUMERIC,
    eps_cagr_10yr_flag TEXT,
    composite_quality_score NUMERIC,
    UNIQUE(company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 11. Peer Comparison Groups
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 12. Valuation Multiples
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore NUMERIC,
    enterprise_value_crore NUMERIC,
    pe_ratio NUMERIC,
    pb_ratio NUMERIC,
    ev_ebitda NUMERIC,
    dividend_yield_pct NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 13. Peer Percentile Rankings Table
CREATE TABLE IF NOT EXISTS peer_percentiles (
    company_id TEXT NOT NULL,
    peer_group_name TEXT NOT NULL,
    metric TEXT NOT NULL,
    value NUMERIC,
    percentile_rank NUMERIC,
    year TEXT NOT NULL,
    PRIMARY KEY (company_id, peer_group_name, metric, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
