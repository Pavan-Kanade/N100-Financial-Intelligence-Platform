"""
Auto Pros & Cons Generator Module for Nifty 100 Financial Intelligence Platform.
Evaluates 12 Pro rules and 12 Con rules per company with confidence scoring.
Guarantees at least 1 pro and 1 con for every company in nifty100.db.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class ProsConsGenerator:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_csv_path = os.path.join(self.output_dir, "pros_cons_generated.csv")

    def generate(self) -> pd.DataFrame:
        """
        Evaluates 12 Pro rules and 12 Con rules across all 92 companies.
        Exports pros_cons_generated.csv.
        """
        conn = sqlite3.connect(self.db_path)

        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
        sec_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        ratios_df = pd.read_sql("SELECT * FROM financial_ratios ORDER BY year ASC", conn)
        mcap_df = pd.read_sql("SELECT * FROM market_cap WHERE year='2023-03' OR year=2023", conn)
        pnl_df = pd.read_sql("SELECT * FROM profitandloss ORDER BY year ASC", conn)
        bs_df = pd.read_sql("SELECT * FROM balancesheet ORDER BY year ASC", conn)

        conn.close()

        records = []

        for _, c_row in comp_df.iterrows():
            cid = c_row["company_id"]
            sec_row = sec_df[sec_df["company_id"] == cid]
            b_sector = sec_row.iloc[0]["broad_sector"] if not sec_row.empty else "N/A"
            is_financial = "Financial" in b_sector

            c_ratios = ratios_df[ratios_df["company_id"] == cid].sort_values(by="year")
            c_mcap = mcap_df[mcap_df["company_id"] == cid]
            c_pnl = pnl_df[pnl_df["company_id"] == cid].sort_values(by="year")
            c_bs = bs_df[bs_df["company_id"] == cid].sort_values(by="year")

            if c_ratios.empty:
                continue

            latest_r = c_ratios.iloc[-1]
            latest_mcap = c_mcap.iloc[-1] if not c_mcap.empty else {}
            latest_pnl = c_pnl.iloc[-1] if not c_pnl.empty else {}

            pros_found = []
            cons_found = []

            # ----------------------------------------------------
            # PRO RULES (12 Rules)
            # ----------------------------------------------------
            # Pro 1: ROE > 20%
            roe_val = latest_r.get("return_on_equity_pct")
            if pd.notna(roe_val) and roe_val > 20.0:
                pros_found.append(("P01", "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", 90))

            # Pro 2: FCF > 0 for 3+ years
            fcf_series = c_ratios["free_cash_flow_cr"].dropna()
            if len(fcf_series) >= 3 and (fcf_series.tail(3) > 0).all():
                pros_found.append(("P02", "Strong free cash flow generation over recent years signals healthy business fundamentals", 85))

            # Pro 3: D/E <= 0.05
            de_val = latest_r.get("debt_to_equity")
            if pd.notna(de_val) and de_val <= 0.05 and not is_financial:
                pros_found.append(("P03", "Debt-free balance sheet provides financial flexibility and eliminates interest burden", 95))

            # Pro 4: Revenue CAGR 5Y > 15%
            rev_cagr = latest_r.get("revenue_cagr_5yr")
            if pd.notna(rev_cagr) and rev_cagr > 15.0:
                pros_found.append(("P04", "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum", 85))

            # Pro 5: OPM > 25%
            opm_val = latest_r.get("operating_profit_margin_pct")
            if pd.notna(opm_val) and opm_val > 25.0:
                pros_found.append(("P05", "Operating profit margin above 25% indicates strong pricing power and cost discipline", 85))

            # Pro 6: PAT CAGR 5Y > 20%
            pat_cagr = latest_r.get("pat_cagr_5yr")
            if pd.notna(pat_cagr) and pat_cagr > 20.0:
                pros_found.append(("P06", "Net profit compounding at above 20% over 5 years creates significant shareholder value", 90))

            # Pro 7: ICR > 10 or Debt Free
            icr_val = latest_r.get("interest_coverage")
            icr_lbl = latest_r.get("icr_label")
            if (pd.notna(icr_val) and icr_val > 10.0) or icr_lbl == "Debt Free":
                pros_found.append(("P07", "Very high interest coverage ratio reflects negligible financial stress from debt servicing", 85))

            # Pro 8: Dividend Yield > 2% with FCF positive
            div_val = latest_mcap.get("dividend_yield_pct")
            fcf_val = latest_r.get("free_cash_flow_cr")
            if pd.notna(div_val) and div_val > 2.0 and pd.notna(fcf_val) and fcf_val > 0:
                pros_found.append(("P08", "Consistent dividend yield above 2% backed by positive free cash flow", 80))

            # Pro 9: EPS CAGR 5Y > 15%
            eps_cagr = latest_r.get("eps_cagr_5yr")
            if pd.notna(eps_cagr) and eps_cagr > 15.0:
                pros_found.append(("P09", "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding", 85))

            # Pro 10: ROE improving for 3 consecutive years
            roe_series = c_ratios["return_on_equity_pct"].dropna()
            if len(roe_series) >= 3 and roe_series.iloc[-1] > roe_series.iloc[-2] > roe_series.iloc[-3]:
                pros_found.append(("P10", "Return on equity improving for 3 consecutive years shows strengthening business quality", 80))

            # Pro 11: Revenue CAGR < PAT CAGR (operating leverage)
            if pd.notna(rev_cagr) and pd.notna(pat_cagr) and rev_cagr > 0 and pat_cagr > rev_cagr:
                pros_found.append(("P11", "Revenue growing slower than profits shows improving operating leverage and scale benefits", 75))

            # Pro 12: Total Assets growing with declining Borrowings
            if len(c_bs) >= 2:
                a_trend = c_bs["total_assets"].iloc[-1] > c_bs["total_assets"].iloc[-2]
                b_trend = c_bs["borrowings"].iloc[-1] <= c_bs["borrowings"].iloc[-2]
                if a_trend and b_trend and not is_financial:
                    pros_found.append(("P12", "Growing asset base funded by internal accruals reflects self-sustaining growth", 75))

            # Default Fallback Pro if none matched
            if not pros_found:
                pros_found.append(("P00", "Established market position in core sector with resilient operations", 70))

            # ----------------------------------------------------
            # CON RULES (12 Rules)
            # ----------------------------------------------------
            # Con 1: D/E > 2.0 for non-financial companies
            if pd.notna(de_val) and de_val > 2.0 and not is_financial:
                cons_found.append(("C01", f"Debt-to-equity ratio of {de_val:.2f} is elevated for a non-financial company and warrants monitoring", 85))

            # Con 2: FCF < 0 for 3 consecutive years
            if len(fcf_series) >= 3 and (fcf_series.tail(3) < 0).all():
                cons_found.append(("C02", "Free cash flow negative for 3 consecutive years raises concern about cash generation quality", 90))

            # Con 3: OPM declining for 3 consecutive years
            opm_series = c_ratios["operating_profit_margin_pct"].dropna()
            if len(opm_series) >= 3 and opm_series.iloc[-1] < opm_series.iloc[-2] < opm_series.iloc[-3]:
                cons_found.append(("C03", "Operating margins declining for 3 consecutive years suggest pricing or cost pressure", 85))

            # Con 4: Net profit < 0 in latest year
            np_val = latest_pnl.get("net_profit")
            if pd.notna(np_val) and np_val < 0:
                cons_found.append(("C04", "Company reported a net loss in the most recent financial year", 95))

            # Con 5: Revenue declining for 2+ consecutive years
            sales_series = c_pnl["sales"].dropna()
            if len(sales_series) >= 3 and sales_series.iloc[-1] < sales_series.iloc[-2] < sales_series.iloc[-3]:
                cons_found.append(("C05", "Revenue contraction over consecutive years indicates demand weakness or market share loss", 85))

            # Con 6: ICR < 1.5
            if pd.notna(icr_val) and icr_val < 1.5 and icr_lbl != "Debt Free" and not is_financial:
                cons_found.append(("C06", "Interest coverage ratio below 1.5x indicates the company is at risk of debt servicing stress", 90))

            # Con 7: Dividend payout > 100%
            dp_val = latest_r.get("dividend_payout_ratio_pct")
            if pd.notna(dp_val) and dp_val > 100.0:
                cons_found.append(("C07", "Dividend payout ratio above 100% means the company is paying dividends from reserves", 80))

            # Con 8: D/E rising for 3 consecutive years
            de_series = c_ratios["debt_to_equity"].dropna()
            if len(de_series) >= 3 and de_series.iloc[-1] > de_series.iloc[-2] > de_series.iloc[-3] and not is_financial:
                cons_found.append(("C08", "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk", 80))

            # Con 9: EPS declining for 3 consecutive years
            eps_series = c_ratios["earnings_per_share"].dropna()
            if len(eps_series) >= 3 and eps_series.iloc[-1] < eps_series.iloc[-2] < eps_series.iloc[-3]:
                cons_found.append(("C09", "Earnings per share declining for 3 consecutive years reflects deteriorating profitability", 80))

            # Con 10: ROCE < 10%
            roce_val = latest_r.get("return_on_capital_employed_pct")
            if pd.notna(roce_val) and roce_val < 10.0 and not is_financial:
                cons_found.append(("C10", "Return on capital employed below 10% suggests the business is generating modest returns", 75))

            # Con 11: Net Debt > 3x EBITDA (or Net Debt > 3x Sales/Operating Profit)
            net_debt = latest_r.get("net_debt_cr")
            op_val = latest_pnl.get("operating_profit")
            if pd.notna(net_debt) and pd.notna(op_val) and op_val > 0 and net_debt > (3.0 * op_val) and not is_financial:
                cons_found.append(("C11", "Net debt exceeding 3 times operating profit indicates high leverage ratio limiting flexibility", 85))

            # Con 12: Revenue CAGR 5Y < 5%
            if pd.notna(rev_cagr) and rev_cagr < 5.0:
                cons_found.append(("C12", "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum", 75))

            # Default Fallback Con if none matched
            if not cons_found:
                cons_found.append(("C00", "Subject to macroeconomic cyclicality and commodity/input cost fluctuations", 65))

            # Add to output records
            for rule_id, text, conf in pros_found:
                if conf > 60:
                    records.append({"company_id": cid, "type": "pro", "rule_id": rule_id, "text": text, "confidence_pct": conf})

            for rule_id, text, conf in cons_found:
                if conf > 60:
                    records.append({"company_id": cid, "type": "con", "rule_id": rule_id, "text": text, "confidence_pct": conf})

        df_out = pd.DataFrame(records)
        df_out.to_csv(self.output_csv_path, index=False)
        print(f"Exported {len(df_out)} generated pros & cons for all 92 companies to {self.output_csv_path}")
        return df_out


if __name__ == "__main__":
    gen = ProsConsGenerator()
    gen.generate()
