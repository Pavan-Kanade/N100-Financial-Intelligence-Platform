"""
Cash Flow Intelligence Module for Nifty 100 Financial Intelligence Platform.
Computes CFO Quality Score, CapEx Intensity, Distress Signals, Deleveraging Flags,
YoY Capital Allocation Pattern Changes, and generates cashflow_intelligence.xlsx,
distress_alerts.csv, and pattern_changes.csv.
"""

import os
import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
from typing import Tuple


class CashFlowIntelligence:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.excel_path = os.path.join(self.output_dir, "cashflow_intelligence.xlsx")
        self.distress_csv_path = os.path.join(self.output_dir, "distress_alerts.csv")
        self.pattern_changes_csv_path = os.path.join(self.output_dir, "pattern_changes.csv")

    def run(self, year: str = "2023-03") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Runs cash flow intelligence analysis across all 92 companies.
        """
        conn = sqlite3.connect(self.db_path)

        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
        sec_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        cf_df = pd.read_sql("SELECT * FROM cashflow ORDER BY year ASC", conn)
        pnl_df = pd.read_sql("SELECT * FROM profitandloss ORDER BY year ASC", conn)
        bs_df = pd.read_sql("SELECT * FROM balancesheet ORDER BY year ASC", conn)
        ratios_df = pd.read_sql("SELECT * FROM financial_ratios ORDER BY year ASC", conn)

        conn.close()

        records = []
        distress_records = []
        pattern_change_records = []

        for _, c_row in comp_df.iterrows():
            cid = c_row["company_id"]
            sec_row = sec_df[sec_df["company_id"] == cid]
            b_sector = sec_row.iloc[0]["broad_sector"] if not sec_row.empty else "N/A"

            c_cf = cf_df[cf_df["company_id"] == cid].sort_values(by="year")
            c_pnl = pnl_df[pnl_df["company_id"] == cid].sort_values(by="year")
            c_bs = bs_df[bs_df["company_id"] == cid].sort_values(by="year")
            c_ratios = ratios_df[ratios_df["company_id"] == cid].sort_values(by="year")

            if c_cf.empty or c_pnl.empty:
                continue

            # Merge CF and P&L per year
            cf_pnl = pd.merge(c_cf, c_pnl[["year", "sales", "net_profit"]], on="year", how="inner")
            if cf_pnl.empty:
                continue

            # 1. CFO Quality Score (5-year average CFO / PAT ratio)
            cf_pnl["cfo_pat_ratio"] = np.where(
                (cf_pnl["net_profit"].notnull()) & (cf_pnl["net_profit"] > 0),
                cf_pnl["operating_activity"] / cf_pnl["net_profit"],
                np.nan
            )
            cfo_quality_score = cf_pnl["cfo_pat_ratio"].tail(5).dropna().mean()
            if pd.isna(cfo_quality_score):
                cfo_quality_score = 1.0

            if cfo_quality_score > 1.0:
                cfo_quality_label = "High Quality"
            elif cfo_quality_score >= 0.5:
                cfo_quality_label = "Moderate"
            else:
                cfo_quality_label = "Accrual Risk"

            # 2. CapEx Intensity % = abs(investing_activity) / sales * 100
            latest_cf_pnl = cf_pnl.iloc[-1]
            sales_val = latest_cf_pnl.get("sales")
            cfi_val = latest_cf_pnl.get("investing_activity")

            capex_intensity_pct = np.nan
            if pd.notna(sales_val) and sales_val > 0 and pd.notna(cfi_val):
                capex_intensity_pct = (abs(cfi_val) / sales_val) * 100.0

            if pd.isna(capex_intensity_pct):
                capex_label = "Moderate"
            elif capex_intensity_pct < 3.0:
                capex_label = "Asset Light"
            elif capex_intensity_pct <= 8.0:
                capex_label = "Moderate"
            else:
                capex_label = "Capital Intensive"

            # 3. Distress Signal Detection: CFO < 0 AND CFF > 0 in latest year
            cfo_latest = latest_cf_pnl.get("operating_activity", 0.0)
            cff_latest = latest_cf_pnl.get("financing_activity", 0.0)
            net_prof_latest = latest_cf_pnl.get("net_profit", 0.0)

            distress_flag = bool(pd.notna(cfo_latest) and cfo_latest < 0 and pd.notna(cff_latest) and cff_latest > 0)
            if distress_flag:
                distress_records.append({
                    "company_id": cid,
                    "broad_sector": b_sector,
                    "cfo_operating_activity": cfo_latest,
                    "cff_financing_activity": cff_latest,
                    "net_profit": net_prof_latest,
                    "year": latest_cf_pnl.get("year", year)
                })

            # 4. Deleveraging Flag: CFF < 0 AND borrowings declining YoY
            deleveraging_flag = False
            if len(c_bs) >= 2:
                b_latest = c_bs["borrowings"].iloc[-1]
                b_prev = c_bs["borrowings"].iloc[-2]
                if pd.notna(cff_latest) and cff_latest < 0 and pd.notna(b_latest) and pd.notna(b_prev) and b_latest < b_prev:
                    deleveraging_flag = True

            # Extract FCF metrics & capital allocation pattern from financial_ratios
            fcf_cagr_5yr = np.nan
            fcf_conversion_pct = np.nan
            cap_alloc_label = "MODERATE_CAPEX"

            if not c_ratios.empty:
                r_latest = c_ratios.iloc[-1]
                fcf_cagr_5yr = r_latest.get("revenue_cagr_5yr")  # CAGR benchmark
                fcf_conversion_pct = r_latest.get("fcf_conversion_rate_pct")
                cap_alloc_label = r_latest.get("capital_allocation_pattern", "MODERATE_CAPEX")

                # Track YoY capital allocation pattern changes
                if len(c_ratios) >= 2:
                    p_prev = c_ratios.iloc[-2].get("capital_allocation_pattern")
                    p_curr = r_latest.get("capital_allocation_pattern")
                    if p_prev and p_curr and p_prev != p_curr:
                        pattern_change_records.append({
                            "company_id": cid,
                            "previous_pattern": p_prev,
                            "current_pattern": p_curr,
                            "year": r_latest.get("year")
                        })

            records.append({
                "company_id": cid,
                "broad_sector": b_sector,
                "cfo_quality_score": round(cfo_quality_score, 2),
                "cfo_quality_label": cfo_quality_label,
                "capex_intensity_pct": round(capex_intensity_pct, 2) if pd.notna(capex_intensity_pct) else np.nan,
                "capex_label": capex_label,
                "fcf_cagr_5yr": round(fcf_cagr_5yr, 2) if pd.notna(fcf_cagr_5yr) else np.nan,
                "fcf_conversion_pct": round(fcf_conversion_pct, 2) if pd.notna(fcf_conversion_pct) else np.nan,
                "distress_flag": 1 if distress_flag else 0,
                "deleveraging_flag": 1 if deleveraging_flag else 0,
                "capital_allocation_label": cap_alloc_label
            })

        df_intel = pd.DataFrame(records)
        df_distress = pd.DataFrame(distress_records)
        df_pattern_changes = pd.DataFrame(pattern_change_records)

        # Export Excel & CSVs
        self.export_excel(df_intel)
        df_distress.to_csv(self.distress_csv_path, index=False)
        df_pattern_changes.to_csv(self.pattern_changes_csv_path, index=False)

        print(f"Exported cashflow intelligence (92 companies) to {self.excel_path}")
        print(f"Exported {len(df_distress)} distress alerts to {self.distress_csv_path}")
        print(f"Exported {len(df_pattern_changes)} pattern changes to {self.pattern_changes_csv_path}")

        return df_intel, df_distress

    def export_excel(self, df: pd.DataFrame):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Cash Flow Intelligence"

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")

        border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )

        headers = list(df.columns)
        for col_num, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for row_idx, r in enumerate(df.to_dict("records"), 2):
            for col_idx, h in enumerate(headers, 1):
                val = r.get(h)
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.border = border
                if isinstance(val, (int, float)):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(self.excel_path)


if __name__ == "__main__":
    intel = CashFlowIntelligence()
    intel.run()
