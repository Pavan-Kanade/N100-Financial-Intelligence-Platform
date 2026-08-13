"""
Peer Comparison Excel Report Generator for Nifty 100 Financial Intelligence Platform.
Generates output/peer_comparison.xlsx with 11 sheets, percentile color coding,
gold benchmark company row highlighting, and median summary rows.
"""

import os
import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from typing import Dict


class PeerReportGenerator:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.export_path = os.path.join(self.output_dir, "peer_comparison.xlsx")

    def generate_report(self, year: str = "2023-03"):
        """
        Generates 11-sheet peer_comparison.xlsx report.
        """
        conn = sqlite3.connect(self.db_path)

        peers_df = pd.read_sql("SELECT * FROM peer_groups", conn)
        ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{year}'", conn)
        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
        pct_df = pd.read_sql(f"SELECT * FROM peer_percentiles WHERE year='{year}'", conn)

        if ratios_df.empty:
            max_yr = pd.read_sql("SELECT MAX(year) FROM financial_ratios", conn).iloc[0, 0]
            ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{max_yr}'", conn)

        conn.close()

        wb = openpyxl.Workbook()
        default_sheet = wb.active

        # Styles
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")

        bench_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
        bench_font = Font(name="Calibri", size=11, bold=True, color="000000")

        green_pct_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        yellow_pct_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        red_pct_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")

        median_font = Font(name="Calibri", size=11, bold=True, italic=True)
        median_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

        border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )

        metrics = [
            "return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
            "operating_profit_margin_pct", "debt_to_equity", "interest_coverage",
            "net_debt_cr", "asset_turnover", "free_cash_flow_cr", "capex_cr",
            "cfo_quality_score", "fcf_conversion_rate_pct", "revenue_cagr_5yr",
            "pat_cagr_5yr", "eps_cagr_5yr", "earnings_per_share", "book_value_per_share",
            "dividend_payout_ratio_pct", "composite_quality_score"
        ]

        grouped = peers_df.groupby("peer_group_name")

        for group_name, group_peers in grouped:
            ws = wb.create_sheet(title=group_name[:31])

            merged_group = pd.merge(group_peers, comp_df, on="company_id", how="left")
            merged_group = pd.merge(merged_group, ratios_df, on="company_id", how="left")

            # Headers
            headers = ["company_id", "company_name", "is_benchmark"] + metrics
            for col_num, h in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Rows
            row_idx = 2
            for _, r in merged_group.iterrows():
                cid = r["company_id"]
                is_bench = bool(r.get("is_benchmark", 0))

                for col_idx, h in enumerate(headers, 1):
                    val = r.get(h)
                    cell = ws.cell(row=row_idx, column=col_idx, value=val)
                    cell.border = border

                    if is_bench:
                        cell.fill = bench_fill
                        cell.font = bench_font

                    if isinstance(val, (int, float)):
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.alignment = Alignment(horizontal="left", vertical="center")

                    # Color code percentiles if available
                    if not is_bench and h in metrics and pct_df is not None and not pct_df.empty:
                        pct_match = pct_df[(pct_df["company_id"] == cid) & (pct_df["metric"] == h)]
                        if not pct_match.empty:
                            p_rank = pct_match.iloc[0]["percentile_rank"]
                            if pd.notna(p_rank):
                                if p_rank >= 0.75:
                                    cell.fill = green_pct_fill
                                elif p_rank >= 0.25:
                                    cell.fill = yellow_pct_fill
                                else:
                                    cell.fill = red_pct_fill

                row_idx += 1

            # Summary Median Row
            ws.cell(row=row_idx, column=1, value="MEDIAN").font = median_font
            ws.cell(row=row_idx, column=2, value="Peer Group Median").font = median_font
            ws.cell(row=row_idx, column=3, value="-").font = median_font

            for col_idx, h in enumerate(metrics, 4):
                med_val = merged_group[h].dropna().median() if h in merged_group.columns else None
                cell = ws.cell(row=row_idx, column=col_idx, value=round(med_val, 2) if pd.notna(med_val) else "N/A")
                cell.font = median_font
                cell.fill = median_fill
                cell.border = border

            # Column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        if default_sheet in wb.worksheets and len(wb.worksheets) > 1:
            wb.remove(default_sheet)

        wb.save(self.export_path)
        print(f"Exported 11-sheet peer comparison report to {self.export_path}")


if __name__ == "__main__":
    gen = PeerReportGenerator()
    gen.generate_report()
