-- Nifty 100 Financial Intelligence Platform
-- Day 07 Exploratory SQL Queries (10 Analytical Queries)

-- Query 1: Total Master Companies Count Check (Expects 92)
SELECT COUNT(*) AS total_companies FROM companies;

-- Query 2: Annual Financial Year Coverage per Company
SELECT company_id, COUNT(*) AS pnl_years_count
FROM profitandloss
GROUP BY company_id
ORDER BY pnl_years_count ASC, company_id ASC;

-- Query 3: Companies with Less Than 5 Years of Financial History (Coverage Check)
SELECT c.id, c.company_name, COUNT(p.year) AS years_available
FROM companies c
LEFT JOIN profitandloss p ON c.id = p.company_id
GROUP BY c.id, c.company_name
HAVING years_available < 5
ORDER BY years_available ASC;

-- Query 4: Top 10 Sales / Revenue Companies in Latest Financial Year per Company
WITH latest_pnl AS (
    SELECT p.*, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) AS rn
    FROM profitandloss p
)
SELECT lp.company_id, c.company_name, lp.year, lp.sales, lp.operating_profit, lp.net_profit
FROM latest_pnl lp
JOIN companies c ON lp.company_id = c.id
WHERE lp.rn = 1
ORDER BY lp.sales DESC
LIMIT 10;

-- Query 5: Zero-Debt (Debt-Free) Companies Identification
WITH latest_ratios AS (
    SELECT r.*, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) AS rn
    FROM financial_ratios r
)
SELECT lr.company_id, c.company_name, lr.year, lr.debt_to_equity, lr.total_debt_cr
FROM latest_ratios lr
JOIN companies c ON lr.company_id = c.id
WHERE lr.rn = 1 AND lr.debt_to_equity = 0
ORDER BY c.company_name ASC;

-- Query 6: Companies Generating Consistently Positive Free Cash Flow (Last 5 Years)
SELECT company_id, COUNT(*) AS positive_fcf_years, SUM(free_cash_flow_cr) AS total_fcf_5yr_cr
FROM financial_ratios
WHERE free_cash_flow_cr > 0
GROUP BY company_id
HAVING positive_fcf_years >= 5
ORDER BY total_fcf_5yr_cr DESC;

-- Query 7: Sector-wise Company Breakdown & Weightage
SELECT s.broad_sector, COUNT(s.company_id) AS company_count, ROUND(SUM(s.index_weight_pct), 2) AS total_sector_weight_pct
FROM sectors s
GROUP BY s.broad_sector
ORDER BY company_count DESC;

-- Query 8: Average Operating Profit Margin (OPM) by Sector (Latest Financial Year)
WITH latest_pnl AS (
    SELECT p.*, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) AS rn
    FROM profitandloss p
)
SELECT s.broad_sector, ROUND(AVG(lp.opm_percentage), 2) AS avg_opm_pct, COUNT(lp.company_id) AS company_count
FROM latest_pnl lp
JOIN sectors s ON lp.company_id = s.company_id
WHERE lp.rn = 1
GROUP BY s.broad_sector
ORDER BY avg_opm_pct DESC;

-- Query 9: Document Repository Audit — Missing Annual Report Links Count
SELECT c.id, c.company_name, (2024 - 2010 + 1) - COUNT(d.year) AS missing_report_years
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id
GROUP BY c.id, c.company_name
ORDER BY missing_report_years DESC;

-- Query 10: Foreign Key Integrity Check (Must Return 0 Rows)
SELECT * FROM (
    SELECT 'profitandloss' AS tbl, company_id FROM profitandloss WHERE company_id NOT IN (SELECT id FROM companies)
    UNION ALL
    SELECT 'balancesheet' AS tbl, company_id FROM balancesheet WHERE company_id NOT IN (SELECT id FROM companies)
    UNION ALL
    SELECT 'cashflow' AS tbl, company_id FROM cashflow WHERE company_id NOT IN (SELECT id FROM companies)
    UNION ALL
    SELECT 'sectors' AS tbl, company_id FROM sectors WHERE company_id NOT IN (SELECT id FROM companies)
    UNION ALL
    SELECT 'stock_prices' AS tbl, company_id FROM stock_prices WHERE company_id NOT IN (SELECT id FROM companies)
);
