"""
Data Quality Validator Module for Nifty 100 Financial Intelligence Platform.
Implements DQ-01 through DQ-16 validation rules.
"""

import os
import re
import pandas as pd
from typing import Dict, List, Tuple


class DQValidator:
    def __init__(self):
        self.failures: List[Dict[str, str]] = []

    def log_failure(self, rule_id: str, company_id: str, year: str, field: str, issue: str, severity: str):
        self.failures.append({
            "rule_id": rule_id,
            "company_id": str(company_id) if company_id is not None else "N/A",
            "year": str(year) if year is not None else "N/A",
            "field": field,
            "issue": issue,
            "severity": severity
        })

    def validate_all(self, dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Runs all 16 Data Quality rules on the ingested DataFrames.
        Returns a DataFrame of all validation failures.
        """
        self.failures = []

        companies_df = dataframes.get("companies")
        pl_df = dataframes.get("profitandloss")
        bs_df = dataframes.get("balancesheet")
        cf_df = dataframes.get("cashflow")
        docs_df = dataframes.get("documents")
        sectors_df = dataframes.get("sectors")

        valid_company_ids = set()
        if companies_df is not None:
            valid_company_ids = set(companies_df['id'].astype(str).str.strip().str.upper())

        # DQ-01: Company PK Uniqueness
        if companies_df is not None:
            dup_companies = companies_df[companies_df['id'].duplicated(keep=False)]
            for _, row in dup_companies.iterrows():
                self.log_failure("DQ-01", row['id'], "N/A", "id", f"Duplicate company ticker: {row['id']}", "CRITICAL")

        # DQ-08: Ticker Format
        for name, df in dataframes.items():
            if df is None: continue
            col = 'id' if name == 'companies' else 'company_id'
            if col in df.columns:
                for idx, val in df[col].items():
                    val_str = str(val).strip().upper() if pd.notna(val) else ""
                    if len(val_str) < 2 or len(val_str) > 12:
                        y = df.at[idx, 'year'] if 'year' in df.columns else "N/A"
                        self.log_failure("DQ-08", val_str, y, col, f"Ticker length out of range [2-12]: '{val}'", "CRITICAL")

        # DQ-02: Annual PK Uniqueness in time-series tables
        ts_tables = {"profitandloss": pl_df, "balancesheet": bs_df, "cashflow": cf_df}
        for name, df in ts_tables.items():
            if df is not None and {'company_id', 'year'}.issubset(df.columns):
                dups = df[df.duplicated(subset=['company_id', 'year'], keep=False)]
                for _, row in dups.iterrows():
                    self.log_failure("DQ-02", row['company_id'], row['year'], "company_id,year", f"Duplicate annual record in {name}", "CRITICAL")

        # DQ-03: FK Integrity
        for name, df in dataframes.items():
            if name == 'companies' or df is None:
                continue
            col = 'company_id' if 'company_id' in df.columns else 'id'
            if col in df.columns and valid_company_ids:
                orphans = df[~df[col].astype(str).str.strip().str.upper().isin(valid_company_ids)]
                for _, row in orphans.iterrows():
                    y = row['year'] if 'year' in row.index else "N/A"
                    self.log_failure("DQ-03", row[col], y, col, f"Orphan record in table {name} not found in companies", "CRITICAL")

        # DQ-07: Year Format
        for name, df in dataframes.items():
            if df is not None and 'year' in df.columns:
                for idx, y_val in df['year'].items():
                    y_str = str(y_val)
                    if not re.match(r"^\d{4}-\d{2}$", y_str):
                        cid = df.at[idx, 'company_id'] if 'company_id' in df.columns else "N/A"
                        self.log_failure("DQ-07", cid, y_str, "year", f"Unparseable/invalid year format in {name}: '{y_val}'", "CRITICAL")

        # DQ-04: Balance Sheet Balance (|total_assets - total_liabilities| / total_assets < 0.01)
        # DQ-10: Non-negative fixed assets
        # DQ-15: BSE/ASE Strict Balance
        if bs_df is not None:
            for _, row in bs_df.iterrows():
                cid = row.get('company_id', 'N/A')
                yr = row.get('year', 'N/A')
                ta = row.get('total_assets', 0)
                tl = row.get('total_liabilities', 0)
                fa = row.get('fixed_assets', 0)

                if pd.notna(ta) and pd.notna(tl) and ta > 0:
                    diff_pct = abs(ta - tl) / ta
                    if diff_pct >= 0.01:
                        self.log_failure("DQ-04", cid, yr, "total_assets/total_liabilities", f"Balance sheet imbalance: assets={ta}, liab={tl} (diff={diff_pct:.2%})", "WARNING")
                    elif ta != tl:
                        self.log_failure("DQ-15", cid, yr, "total_assets/total_liabilities", f"Imbalance within 1% tolerance: assets={ta}, liab={tl}", "INFO")

                if pd.notna(fa) and fa < 0:
                    self.log_failure("DQ-10", cid, yr, "fixed_assets", f"Negative fixed assets: {fa}", "WARNING")

        # DQ-05: OPM Cross-Check
        # DQ-06: Positive Sales (non-banks)
        # DQ-11: Tax Rate Range
        # DQ-12: Dividend Payout Cap
        # DQ-14: EPS Sign Consistency
        financial_sectors = set()
        if sectors_df is not None:
            fin_rows = sectors_df[sectors_df['broad_sector'].astype(str).str.contains("Financial", case=False, na=False)]
            financial_sectors = set(fin_rows['company_id'].astype(str).str.strip().str.upper())

        if pl_df is not None:
            for _, row in pl_df.iterrows():
                cid = str(row.get('company_id', 'N/A')).strip().upper()
                yr = row.get('year', 'N/A')
                sales = row.get('sales', 0)
                op = row.get('operating_profit', 0)
                opm = row.get('opm_percentage', 0)
                tax = row.get('tax_percentage', 0)
                div = row.get('dividend_payout', 0)
                np_val = row.get('net_profit', 0)
                eps = row.get('eps', 0)

                # DQ-05
                if pd.notna(sales) and sales > 0 and pd.notna(op) and pd.notna(opm):
                    calc_opm = (op / sales) * 100
                    if abs(opm - calc_opm) > 1.0:
                        self.log_failure("DQ-05", cid, yr, "opm_percentage", f"OPM mismatch: reported {opm}%, computed {calc_opm:.2f}%", "WARNING")

                # DQ-06
                if cid not in financial_sectors:
                    if pd.notna(sales) and sales <= 0:
                        self.log_failure("DQ-06", cid, yr, "sales", f"Non-positive sales in non-financial company: {sales}", "WARNING")

                # DQ-11
                if pd.notna(tax) and (tax < 0 or tax > 60):
                    self.log_failure("DQ-11", cid, yr, "tax_percentage", f"Tax percentage out of range [0-60]: {tax}%", "WARNING")

                # DQ-12
                if pd.notna(div) and div > 200:
                    self.log_failure("DQ-12", cid, yr, "dividend_payout", f"Dividend payout > 200%: {div}%", "WARNING")

                # DQ-14
                if pd.notna(np_val) and np_val > 0 and pd.notna(eps) and eps <= 0:
                    self.log_failure("DQ-14", cid, yr, "eps", f"Positive net profit ({np_val}) but non-positive EPS ({eps})", "WARNING")

        # DQ-09: Net Cash Check (|net_cash_flow - (CFO+CFI+CFF)| <= 10)
        if cf_df is not None:
            for _, row in cf_df.iterrows():
                cid = row.get('company_id', 'N/A')
                yr = row.get('year', 'N/A')
                cfo = row.get('operating_activity', 0) or 0
                cfi = row.get('investing_activity', 0) or 0
                cff = row.get('financing_activity', 0) or 0
                ncf = row.get('net_cash_flow', 0) or 0

                calc_ncf = cfo + cfi + cff
                if abs(ncf - calc_ncf) > 10.0:
                    self.log_failure("DQ-09", cid, yr, "net_cash_flow", f"Net cash flow mismatch: reported {ncf}, computed sum {calc_ncf}", "WARNING")

        # DQ-13: URL Validity (documents)
        if docs_df is not None:
            url_col = 'Annual_Report' if 'Annual_Report' in docs_df.columns else 'annual_report'
            if url_col in docs_df.columns:
                for _, row in docs_df.iterrows():
                    cid = row.get('company_id', 'N/A')
                    yr = row.get('Year', row.get('year', 'N/A'))
                    url = str(row.get(url_col, ''))
                    if not (url.startswith("http://") or url.startswith("https://")):
                        self.log_failure("DQ-13", cid, yr, url_col, f"Invalid annual report URL format: '{url}'", "WARNING")

        # DQ-16: Coverage Check (>= 5 years of P&L, BS, CF)
        if valid_company_ids and pl_df is not None:
            for cid in valid_company_ids:
                pl_cnt = len(pl_df[pl_df['company_id'].astype(str).str.strip().str.upper() == cid])
                if pl_cnt < 5:
                    self.log_failure("DQ-16", cid, "N/A", "year_coverage", f"Company has less than 5 years of financial history ({pl_cnt} years)", "WARNING")

        df_failures = pd.DataFrame(self.failures)
        if df_failures.empty:
            df_failures = pd.DataFrame(columns=["rule_id", "company_id", "year", "field", "issue", "severity"])
        return df_failures
