"""
ReportLab Sector PDF Report Generator for Nifty 100 Financial Intelligence Platform.
Generates 11 sector PDF reports in reports/sector/<SECTOR>_report.pdf with sector median KPIs
and detailed company performance tables.
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable


class SectorReportGenerator:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "reports/sector"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all_sector_reports(self, year: str = "2023-03"):
        """
        Generates 11 sector PDF reports.
        """
        conn = sqlite3.connect(self.db_path)

        sec_df = pd.read_sql("SELECT * FROM sectors", conn)
        comp_df = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
        ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{year}'", conn)
        mcap_df = pd.read_sql(f"SELECT * FROM market_cap WHERE year='{year}' OR year=2023", conn)

        if ratios_df.empty:
            max_yr = pd.read_sql("SELECT MAX(year) FROM financial_ratios", conn).iloc[0, 0]
            ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{max_yr}'", conn)

        conn.close()

        merged = pd.merge(sec_df, comp_df, on="company_id", how="inner")
        merged = pd.merge(merged, ratios_df, on="company_id", how="left")
        merged = pd.merge(merged, mcap_df[["company_id", "market_cap_crore", "pe_ratio"]], on="company_id", how="left")

        grouped = merged.groupby("broad_sector")
        count = 0

        for sector_name, group_data in grouped:
            safe_name = sector_name.replace(" ", "_").replace("&", "and").replace("/", "_")
            pdf_path = os.path.join(self.output_dir, f"{safe_name}_report.pdf")
            self.build_sector_pdf(pdf_path, sector_name, group_data)
            count += 1

        print(f"Generated {count} sector PDF reports in {self.output_dir}/")

    def build_sector_pdf(self, pdf_path: str, sector_name: str, group_data: pd.DataFrame):
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "SectorTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.HexColor("#FFFFFF"),
            alignment=0
        )

        cell_hdr_style = ParagraphStyle(
            "CellHdr",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#FFFFFF"),
            alignment=1
        )

        cell_body_style = ParagraphStyle(
            "CellBody",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#1E293B"),
            alignment=1
        )

        story = []

        # Header Banner
        header_p1 = Paragraph(f"Nifty 100 Sector Report: {sector_name}", title_style)
        header_table = Table([[header_p1]], colWidths=[540])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F4E78")),
            ("PADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 12))

        # Sector Median Summary
        roe_med = group_data["return_on_equity_pct"].median()
        roce_med = group_data["return_on_capital_employed_pct"].median()
        opm_med = group_data["operating_profit_margin_pct"].median()
        de_med = group_data["debt_to_equity"].median()

        med_text = Paragraph(
            f"<b>Sector Summary ({len(group_data)} Companies):</b> Median ROE = <b>{roe_med:.1f}%</b> | "
            f"Median ROCE = <b>{roce_med:.1f}%</b> | Median OPM = <b>{opm_med:.1f}%</b> | Median D/E = <b>{de_med:.2f}</b>",
            ParagraphStyle("MedStyle", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#1F4E78"))
        )
        story.append(med_text)
        story.append(Spacer(1, 12))

        # Sector Company Table
        table_headers = ["Ticker", "Company Name", "ROE %", "ROCE %", "NPM %", "D/E", "5Y Rev CAGR", "Composite Score"]
        table_rows = [[Paragraph(h, cell_hdr_style) for h in table_headers]]

        for _, r in group_data.iterrows():
            cid = r["company_id"]
            cname = str(r["company_name"])[:20]
            roe = f"{r['return_on_equity_pct']:.1f}%" if pd.notna(r["return_on_equity_pct"]) else "N/A"
            roce = f"{r['return_on_capital_employed_pct']:.1f}%" if pd.notna(r["return_on_capital_employed_pct"]) else "N/A"
            npm = f"{r['net_profit_margin_pct']:.1f}%" if pd.notna(r["net_profit_margin_pct"]) else "N/A"
            de = f"{r['debt_to_equity']:.2f}" if pd.notna(r["debt_to_equity"]) else "N/A"
            cagr = f"{r['revenue_cagr_5yr']:.1f}%" if pd.notna(r["revenue_cagr_5yr"]) else "N/A"
            comp = f"{r['composite_quality_score']:.1f}" if pd.notna(r["composite_quality_score"]) else "N/A"

            row_cells = [
                Paragraph(cid, cell_body_style),
                Paragraph(cname, ParagraphStyle("B", fontName="Helvetica", fontSize=8)),
                Paragraph(roe, cell_body_style),
                Paragraph(roce, cell_body_style),
                Paragraph(npm, cell_body_style),
                Paragraph(de, cell_body_style),
                Paragraph(cagr, cell_body_style),
                Paragraph(comp, cell_body_style)
            ]
            table_rows.append(row_cells)

        comp_table = Table(table_rows, colWidths=[55, 125, 55, 55, 55, 50, 75, 70])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ]))
        story.append(comp_table)

        doc.build(story)


if __name__ == "__main__":
    gen = SectorReportGenerator()
    gen.generate_all_sector_reports()
