"""
Master Financial Ratio Engine Orchestrator for Nifty 100 Financial Intelligence Platform.
Computes 50+ KPIs across all companies and years, populates financial_ratios SQLite table,
and generates capital_allocation.csv and ratio_edge_cases.log.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

from src.analytics.ratios import (
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_return_on_equity,
    compute_return_on_capital_employed,
    compute_return_on_assets,
    compute_debt_to_equity,
    check_high_leverage_flag,
    compute_interest_coverage,
    get_icr_label_and_warning,
    compute_net_debt,
    compute_asset_turnover,
)
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    compute_free_cash_flow,
    compute_cfo_quality_score,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
    classify_capital_allocation,
)


class RatioEngine:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = output_dir
        self.schema_path = "db/schema.sql"
        os.makedirs(self.output_dir, exist_ok=True)
        self.edge_case_logs: List[str] = []

    def log_edge_case(self, category: str, ticker: str, year: str, message: str):
        log_entry = f"[{category.upper()}] Company: {ticker} | Year: {year} | {message}"
        self.edge_case_logs.append(log_entry)

    def init_ratio_table(self, conn: sqlite3.Connection):
        """Drops and recreates financial_ratios table from db/schema.sql."""
        conn.execute("DROP TABLE IF EXISTS financial_ratios;")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            ddl = f.read()
        conn.executescript(ddl)

    def run(self) -> pd.DataFrame:
        """
        Executes full ratio engine:
        1. Reads data from SQLite DB
        2. Computes all ratios, CAGR metrics, cash flow KPIs, and capital allocation
        3. Writes to financial_ratios table in SQLite
        4. Saves output/capital_allocation.csv & output/ratio_edge_cases.log
        """
        conn = sqlite3.connect(self.db_path)

        # Re-create table schema
        self.init_ratio_table(conn)

        # 1. Read input tables
        pnl_df = pd.read_sql("SELECT * FROM profitandloss", conn)
        bs_df = pd.read_sql("SELECT * FROM balancesheet", conn)
        cf_df = pd.read_sql("SELECT * FROM cashflow", conn)
        comp_df = pd.read_sql("SELECT * FROM companies", conn)
        sec_df = pd.read_sql("SELECT * FROM sectors", conn)

        comp_face_map = comp_df.set_index("id")["face_value"].to_dict()
        comp_roce_map = comp_df.set_index("id")["roce_percentage"].to_dict()
        comp_roe_map = comp_df.set_index("id")["roe_percentage"].to_dict()
        sector_map = sec_df.set_index("company_id")["broad_sector"].to_dict()

        # 2. Outer join financial statements per company-year
        df = pd.merge(pnl_df, bs_df, on=["company_id", "year"], how="outer", suffixes=("", "_bs"))
        df = pd.merge(df, cf_df, on=["company_id", "year"], how="outer", suffixes=("", "_cf"))

        # Sort by company_id and year
        df = df.sort_values(by=["company_id", "year"]).reset_index(drop=True)

        calculated_rows = []
        cap_alloc_rows = []

        # Process per company
        grouped = df.groupby("company_id")

        for company_id, comp_group in grouped:
            comp_rows = comp_group.to_dict("records")
            broad_sector = sector_map.get(company_id, "Other")
            face_val = comp_face_map.get(company_id, 1.0)
            if face_val is None or face_val <= 0:
                face_val = 1.0

            # Pre-extract CFO & PAT series for 5Y CFO Quality Score
            cfo_list = [r.get("operating_activity") for r in comp_rows]
            pat_list = [r.get("net_profit") for r in comp_rows]

            cfo_quality_score, cfo_quality_cat = compute_cfo_quality_score(cfo_list, pat_list)

            for idx, r in enumerate(comp_rows):
                yr = r["year"]
                sales = r.get("sales")
                op = r.get("operating_profit")
                opm_src = r.get("opm_percentage")
                other_inc = r.get("other_income")
                interest = r.get("interest")
                dep = r.get("depreciation")
                net_profit = r.get("net_profit")
                eps = r.get("eps")
                div_payout = r.get("dividend_payout")

                eq_cap = r.get("equity_capital")
                reserves = r.get("reserves")
                borrowings = r.get("borrowings")
                total_liab = r.get("total_liabilities")
                tot_assets = r.get("total_assets")
                investments = r.get("investments")

                cfo = r.get("operating_activity")
                cfi = r.get("investing_activity")
                cff = r.get("financing_activity")

                # Profitability
                npm = compute_net_profit_margin(net_profit, sales)
                opm = compute_operating_profit_margin(op, sales)

                # OPM Cross-check vs source
                if opm is not None and opm_src is not None:
                    try:
                        if abs(opm - float(opm_src)) > 1.0:
                            self.log_failure_check(
                                "formula_discrepancy",
                                company_id,
                                yr,
                                f"OPM computed ({opm}%) diff > 1% vs source ({opm_src}%)",
                            )
                    except ValueError:
                        pass

                roe = compute_return_on_equity(net_profit, eq_cap, reserves)
                roce = compute_return_on_capital_employed(op, dep, eq_cap, reserves, borrowings)
                roa = compute_return_on_assets(net_profit, tot_assets)

                # Leverage & Efficiency
                de = compute_debt_to_equity(borrowings, eq_cap, reserves)
                high_lev_flag = check_high_leverage_flag(de, broad_sector)
                icr = compute_interest_coverage(op, other_inc, interest)
                icr_label, icr_warn_flag = get_icr_label_and_warning(icr, interest)
                net_debt = compute_net_debt(borrowings, investments)
                asset_turnover = compute_asset_turnover(sales, tot_assets)

                # Cash Flow KPIs
                fcf = compute_free_cash_flow(cfo, cfi)
                capex_cr = abs(float(cfi)) if cfi is not None else 0.0
                capex_int, capex_cat = compute_capex_intensity(cfi, sales)
                fcf_conv = compute_fcf_conversion_rate(fcf, op)

                # Capital Allocation
                cfo_s, cfi_s, cff_s, cap_pattern = classify_capital_allocation(
                    cfo, cfi, cff, cfo_quality_score
                )
                cap_alloc_rows.append({
                    "company_id": company_id,
                    "year": yr,
                    "cfo_sign": cfo_s,
                    "cfi_sign": cfi_s,
                    "cff_sign": cff_s,
                    "pattern_label": cap_pattern,
                })

                # Book Value Per Share: (equity + reserves) / (equity_capital / face_value)
                bvps = None
                if eq_cap is not None and reserves is not None and face_val > 0:
                    try:
                        tot_eq = float(eq_cap) + float(reserves)
                        shares = float(eq_cap) / float(face_val)
                        if shares > 0:
                            bvps = round(tot_eq / shares, 2)
                    except (ValueError, ZeroDivisionError):
                        pass

                # Multi-window CAGR calculations (3Y, 5Y, 10Y)
                def get_cagr_for_window(metric_key: str, n_yrs: int):
                    if idx >= n_yrs:
                        start_r = comp_rows[idx - n_yrs]
                        return calculate_cagr(start_r.get(metric_key), r.get(metric_key), n_yrs)
                    return None, "INSUFFICIENT"

                rev_3_val, rev_3_flg = get_cagr_for_window("sales", 3)
                rev_5_val, rev_5_flg = get_cagr_for_window("sales", 5)
                rev_10_val, rev_10_flg = get_cagr_for_window("sales", 10)

                pat_3_val, pat_3_flg = get_cagr_for_window("net_profit", 3)
                pat_5_val, pat_5_flg = get_cagr_for_window("net_profit", 5)
                pat_10_val, pat_10_flg = get_cagr_for_window("net_profit", 10)

                eps_3_val, eps_3_flg = get_cagr_for_window("eps", 3)
                eps_5_val, eps_5_flg = get_cagr_for_window("eps", 5)
                eps_10_val, eps_10_flg = get_cagr_for_window("eps", 10)

                row_dict = {
                    "company_id": company_id,
                    "year": yr,
                    "net_profit_margin_pct": npm,
                    "operating_profit_margin_pct": opm,
                    "return_on_equity_pct": roe,
                    "return_on_capital_employed_pct": roce,
                    "return_on_assets_pct": roa,
                    "debt_to_equity": de,
                    "high_leverage_flag": 1 if high_lev_flag else 0,
                    "interest_coverage": icr,
                    "icr_label": icr_label,
                    "icr_warning_flag": 1 if icr_warn_flag else 0,
                    "net_debt_cr": net_debt,
                    "asset_turnover": asset_turnover,
                    "free_cash_flow_cr": fcf,
                    "capex_cr": capex_cr,
                    "capex_intensity_category": capex_cat,
                    "cfo_quality_score": cfo_quality_score,
                    "cfo_quality_category": cfo_quality_cat,
                    "fcf_conversion_rate_pct": fcf_conv,
                    "capital_allocation_pattern": cap_pattern,
                    "earnings_per_share": eps,
                    "book_value_per_share": bvps,
                    "dividend_payout_ratio_pct": div_payout,
                    "total_debt_cr": borrowings,
                    "cash_from_operations_cr": cfo,
                    "revenue_cagr_3yr": rev_3_val,
                    "revenue_cagr_3yr_flag": rev_3_flg,
                    "revenue_cagr_5yr": rev_5_val,
                    "revenue_cagr_5yr_flag": rev_5_flg,
                    "revenue_cagr_10yr": rev_10_val,
                    "revenue_cagr_10yr_flag": rev_10_flg,
                    "pat_cagr_3yr": pat_3_val,
                    "pat_cagr_3yr_flag": pat_3_flg,
                    "pat_cagr_5yr": pat_5_val,
                    "pat_cagr_5yr_flag": pat_5_flg,
                    "pat_cagr_10yr": pat_10_val,
                    "pat_cagr_10yr_flag": pat_10_flg,
                    "eps_cagr_3yr": eps_3_val,
                    "eps_cagr_3yr_flag": eps_3_flg,
                    "eps_cagr_5yr": eps_5_val,
                    "eps_cagr_5yr_flag": eps_5_flg,
                    "eps_cagr_10yr": eps_10_val,
                    "eps_cagr_10yr_flag": eps_10_flg,
                }
                calculated_rows.append(row_dict)

                # Day 13: Cross-check ROCE & ROE vs companies master
                if yr in ["2023-03", "2024-03"]:
                    src_roce = comp_roce_map.get(company_id)
                    src_roe = comp_roe_map.get(company_id)

                    if roce is not None and src_roce is not None:
                        try:
                            if abs(roce - float(src_roce)) > 5.0:
                                self.log_failure_check(
                                    "version_difference",
                                    company_id,
                                    yr,
                                    f"ROCE computed ({roce:.1f}%) vs companies.xlsx ({src_roce:.1f}%) diff > 5%",
                                )
                        except ValueError:
                            pass

                    if roe is not None and src_roe is not None:
                        try:
                            # Note: TCS source ROE 0.52 anomaly
                            if abs(roe - float(src_roe)) > 5.0:
                                self.log_failure_check(
                                    "data_source_issue",
                                    company_id,
                                    yr,
                                    f"ROE computed ({roe:.1f}%) vs companies.xlsx ({src_roe:.1f}%) anomaly",
                                )
                        except ValueError:
                            pass

        df_ratios = pd.DataFrame(calculated_rows)

        # Compute Composite Quality Score (0-100)
        df_ratios["composite_quality_score"] = self.compute_composite_score(df_ratios)

        # 5. Populate SQLite table financial_ratios
        print(f"Populating financial_ratios table with {len(df_ratios)} rows...")
        df_ratios.to_sql("financial_ratios", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()

        # 6. Save output/capital_allocation.csv
        df_cap = pd.DataFrame(cap_alloc_rows)
        cap_csv_path = os.path.join(self.output_dir, "capital_allocation.csv")
        df_cap.to_csv(cap_csv_path, index=False)
        print(f"Saved {len(df_cap)} capital allocation records to {cap_csv_path}")

        # 7. Save output/ratio_edge_cases.log
        log_path = os.path.join(self.output_dir, "ratio_edge_cases.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for item in self.edge_case_logs:
                f.write(item + "\n")
        print(f"Saved {len(self.edge_case_logs)} anomaly log entries to {log_path}")

        return df_ratios

    def log_failure_check(self, category: str, ticker: str, year: str, msg: str):
        self.log_edge_case(category, ticker, year, msg)

    def compute_composite_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Computes Composite Quality Score (0-100) based on weighted metrics:
        0.35 * ROE + 0.30 * FCF + 0.20 * Growth + 0.15 * Leverage
        Normalised using P10/P90 winsorisation.
        """
        def norm_series(s: pd.Series, ascending=True) -> pd.Series:
            clean_s = s.dropna()
            if clean_s.empty:
                return pd.Series(50.0, index=s.index)
            p10 = clean_s.quantile(0.10)
            p90 = clean_s.quantile(0.90)
            clipped = s.clip(lower=p10, upper=p90)
            if p90 == p10:
                return pd.Series(50.0, index=s.index)
            res = ((clipped - p10) / (p90 - p10)) * 100.0
            if not ascending:
                res = 100.0 - res
            return res.fillna(50.0)

        roe_sc = norm_series(df["return_on_equity_pct"])
        fcf_sc = norm_series(df["free_cash_flow_cr"])
        gro_sc = norm_series(df["revenue_cagr_5yr"])
        lev_sc = norm_series(df["debt_to_equity"], ascending=False)

        comp = 0.35 * roe_sc + 0.30 * fcf_sc + 0.20 * gro_sc + 0.15 * lev_sc
        return comp.round(2)


if __name__ == "__main__":
    engine = RatioEngine()
    engine.run()
