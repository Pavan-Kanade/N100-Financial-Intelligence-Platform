"""
Valuation Module for Nifty 100 Financial Intelligence Platform.
Computes FCF Yield, Sector Median P/E multiples, 5-Year Historical Median P/E,
and overvaluation/discount flags. Generates valuation_summary.xlsx and valuation_flags.csv.
"""

import os
import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
from typing import Tuple


class ValuationEngine:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.summary_excel_path = os.path.join(self.output_dir, "valuation_summary.xlsx")
        self.flags_csv_path = os.path.join(self.output_dir, "valuation_flags.csv")

    def run(self, year: str = "2023-03") -> pd.DataFrame:
        """
        Runs valuation analysis across all 92 companies for latest available year.
        Returns valuation DataFrame and exports Excel and CSV outputs.
        """
        conn = sqlite3.connect(self.db_path)

        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
        sec_df = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
        mcap_df = pd.read_sql(f"SELECT * FROM market_cap WHERE year='{year}' OR year=2023", conn)
        ratios_df = pd.read_sql(f"SELECT company_id, year, free_cash_flow_cr, return_on_equity_pct FROM financial_ratios WHERE year='{year}'", conn)
        mcap_hist_df = pd.read_sql("SELECT company_id, pe_ratio FROM market_cap", conn)

        conn.close()

        # Merge core datasets
        df = pd.merge(comp_df, sec_df, on="company_id", how="inner")
        df = pd.merge(df, mcap_df[["company_id", "market_cap_crore", "enterprise_value_crore", "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"]], on="company_id", how="left")
        df = pd.merge(df, ratios_df[["company_id", "free_cash_flow_cr"]], on="company_id", how="left")

        # 1. Compute FCF Yield % = (FCF / market_cap_crore) * 100
        df["fcf_yield_pct"] = np.where(
            (df["market_cap_crore"].notnull()) & (df["market_cap_crore"] > 0) & (df["free_cash_flow_cr"].notnull()),
            (df["free_cash_flow_cr"] / df["market_cap_crore"]) * 100.0,
            np.nan
        )
        df["fcf_yield_pct"] = df["fcf_yield_pct"].round(2)

        # 2. Compute 5Y Median P/E per company across market_cap history
        med_pe_5yr = mcap_hist_df.groupby("company_id")["pe_ratio"].median().to_dict()
        df["median_pe_5yr"] = df["company_id"].map(med_pe_5yr).round(2)

        # 3. Compute Broad Sector Median P/E
        sector_median_pe = df.groupby("broad_sector")["pe_ratio"].median().to_dict()
        df["sector_median_pe"] = df["broad_sector"].map(sector_median_pe).round(2)

        # 4. Compute P/E vs Sector Median %
        df["pe_vs_sector_median_pct"] = np.where(
            (df["sector_median_pe"].notnull()) & (df["sector_median_pe"] > 0) & (df["pe_ratio"].notnull()),
            ((df["pe_ratio"] - df["sector_median_pe"]) / df["sector_median_pe"]) * 100.0,
            np.nan
        )
        df["pe_vs_sector_median_pct"] = df["pe_vs_sector_median_pct"].round(2)

        # 5. Overvaluation / Discount Flagging:
        # Caution if PE > sector_median * 1.5
        # Discount if PE < sector_median * 0.7
        # Fair otherwise
        conditions = [
            (df["pe_ratio"] > (df["sector_median_pe"] * 1.5)),
            (df["pe_ratio"] < (df["sector_median_pe"] * 0.7))
        ]
        choices = ["Caution", "Discount"]
        df["valuation_flag"] = np.select(conditions, choices, default="Fair")

        # Select & order output columns
        export_cols = [
            "company_id", "company_name", "broad_sector", "pe_ratio", "pb_ratio",
            "ev_ebitda", "dividend_yield_pct", "fcf_yield_pct", "median_pe_5yr",
            "sector_median_pe", "pe_vs_sector_median_pct", "valuation_flag"
        ]
        df_export = df[export_cols].copy()

        # Generate formatted Excel output
        self.export_excel(df_export)

        # Generate CSV output for Caution & Discount flags
        df_flags = df_export[df_export["valuation_flag"].isin(["Caution", "Discount"])].copy()
        df_flags.to_csv(self.flags_csv_path, index=False)
        print(f"Exported {len(df_flags)} valuation flagged companies to {self.flags_csv_path}")

        return df_export

    def export_excel(self, df: pd.DataFrame):
        """
        Exports formatted valuation summary Excel file with openpyxl styling.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Valuation Summary"

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")

        caution_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        discount_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        fair_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

        border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )

        headers = list(df.columns)

        # Write header
        for col_num, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Write data
        for row_idx, r in enumerate(df.to_dict("records"), 2):
            flag = r.get("valuation_flag", "Fair")

            for col_idx, h in enumerate(headers, 1):
                val = r.get(h)
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.border = border

                if h == "valuation_flag":
                    if flag == "Caution":
                        cell.fill = caution_fill
                    elif flag == "Discount":
                        cell.fill = discount_fill
                    else:
                        cell.fill = fair_fill

                if isinstance(val, (int, float)):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(self.summary_excel_path)
        print(f"Exported valuation summary (92 companies) to {self.summary_excel_path}")


if __name__ == "__main__":
    engine = ValuationEngine()
    engine.run()
