"""
ReportLab Portfolio Summary PDF Generator for Nifty 100 Financial Intelligence Platform.
Generates reports/portfolio/portfolio_summary.pdf (1 page per company in alphabetical order)
featuring top 6 KPIs with trend arrows (^ improved, v declined, -> flat).
"""

import os
import sqlite3
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


class PortfolioReportGenerator:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "reports/portfolio"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.pdf_path = os.path.join(self.output_dir, "portfolio_summary.pdf")

    def generate_portfolio_pdf(self):
        """
        Generates master portfolio summary PDF.
        """
        conn = sqlite3.connect(self.db_path)

        comp_df = pd.read_sql("SELECT * FROM companies ORDER BY id ASC", conn)
        sec_df = pd.read_sql("SELECT * FROM sectors", conn)
        ratios_df = pd.read_sql("SELECT * FROM financial_ratios ORDER BY year ASC", conn)

        conn.close()

        doc = SimpleDocTemplate(
            self.pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "PortTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.HexColor("#FFFFFF"),
            alignment=0
        )

        kpi_title_style = ParagraphStyle(
            "KPITitle",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#475569"),
            alignment=1
        )

        kpi_val_style = ParagraphStyle(
            "KPIVal",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=colors.HexColor("#1F4E78"),
            alignment=1
        )

        story = []

        total_cos = len(comp_df)
        idx_count = 0

        for _, c_row in comp_df.iterrows():
            cid = c_row["id"]
            cname = c_row["company_name"]

            sec_match = sec_df[sec_df["company_id"] == cid]
            sec_info = sec_match.iloc[0] if not sec_match.empty else {"broad_sector": "N/A", "sub_sector": "N/A"}

            c_ratios = ratios_df[ratios_df["company_id"] == cid].sort_values(by="year")

            # Extract latest & previous ratio values for trend arrows
            if len(c_ratios) >= 2:
                latest_r = c_ratios.iloc[-1]
                prev_r = c_ratios.iloc[-2]
            elif not c_ratios.empty:
                latest_r = c_ratios.iloc[-1]
                prev_r = {}
            else:
                latest_r = {}
                prev_r = {}

            def get_trend_arrow(curr_val, prev_val, higher_is_better=True) -> str:
                if pd.isna(curr_val) or pd.isna(prev_val):
                    return ""
                diff_pct = ((curr_val - prev_val) / abs(prev_val)) * 100.0 if prev_val != 0 else 0
                if abs(diff_pct) <= 2.0:
                    return " ->"
                elif diff_pct > 2.0:
                    return " ^" if higher_is_better else " v"
                else:
                    return " v" if higher_is_better else " ^"

            roe_curr = latest_r.get("return_on_equity_pct")
            roe_prev = prev_r.get("return_on_equity_pct")
            roe_arr = get_trend_arrow(roe_curr, roe_prev, True)

            roce_curr = latest_r.get("return_on_capital_employed_pct")
            roce_prev = prev_r.get("return_on_capital_employed_pct")
            roce_arr = get_trend_arrow(roce_curr, roce_prev, True)

            npm_curr = latest_r.get("net_profit_margin_pct")
            npm_prev = prev_r.get("net_profit_margin_pct")
            npm_arr = get_trend_arrow(npm_curr, npm_prev, True)

            de_curr = latest_r.get("debt_to_equity")
            de_prev = prev_r.get("debt_to_equity")
            de_arr = get_trend_arrow(de_curr, de_prev, False)

            cagr_curr = latest_r.get("revenue_cagr_5yr")
            cagr_prev = prev_r.get("revenue_cagr_5yr")
            cagr_arr = get_trend_arrow(cagr_curr, cagr_prev, True)

            fcf_curr = latest_r.get("free_cash_flow_cr")
            fcf_prev = prev_r.get("free_cash_flow_cr")
            fcf_arr = get_trend_arrow(fcf_curr, fcf_prev, True)

            # Header Banner
            header_p1 = Paragraph(f"{cname} ({cid})", title_style)
            header_p2 = Paragraph(f"Broad Sector: {sec_info.get('broad_sector', 'N/A')} | Industry: {sec_info.get('sub_sector', 'N/A')}", ParagraphStyle("Sub", fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#E2E8F0")))

            header_table = Table([[header_p1], [header_p2]], colWidths=[540])
            header_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F4E78")),
                ("PADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 15))

            # 6 KPI Tiles Table with Trend Arrows
            kpi_data = [
                [
                    Paragraph("RETURN ON EQUITY", kpi_title_style),
                    Paragraph("RETURN ON CAPITAL", kpi_title_style),
                    Paragraph("NET PROFIT MARGIN", kpi_title_style)
                ],
                [
                    Paragraph(f"{roe_curr:.1f}% {roe_arr}" if pd.notna(roe_curr) else "N/A", kpi_val_style),
                    Paragraph(f"{roce_curr:.1f}% {roce_arr}" if pd.notna(roce_curr) else "N/A", kpi_val_style),
                    Paragraph(f"{npm_curr:.1f}% {npm_arr}" if pd.notna(npm_curr) else "N/A", kpi_val_style)
                ],
                [
                    Paragraph("DEBT TO EQUITY", kpi_title_style),
                    Paragraph("5Y REVENUE CAGR", kpi_title_style),
                    Paragraph("FREE CASH FLOW", kpi_title_style)
                ],
                [
                    Paragraph(f"{de_curr:.2f} {de_arr}" if pd.notna(de_curr) else "N/A", kpi_val_style),
                    Paragraph(f"{cagr_curr:.1f}% {cagr_arr}" if pd.notna(cagr_curr) else "N/A", kpi_val_style),
                    Paragraph(f"₹{fcf_curr:,.0f} Cr {fcf_arr}" if pd.notna(fcf_curr) else "N/A", kpi_val_style)
                ]
            ]

            kpi_table = Table(kpi_data, colWidths=[180, 180, 180])
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 20))

            # Summary Text
            comp_score = latest_r.get("composite_quality_score", 50.0)
            cap_pattern = latest_r.get("capital_allocation_pattern", "MODERATE_CAPEX")

            summary_text = Paragraph(
                f"<b>Composite Quality Score:</b> <font color='#1F4E78'><b>{comp_score:.1f} / 100</b></font> | "
                f"<b>Capital Allocation Pattern:</b> <font color='#1F4E78'><b>{cap_pattern}</b></font><br/>"
                f"<i>Note: Trend indicator ^ denotes >2% YoY improvement, v denotes >2% YoY contraction, -> denotes stable trajectory.</i>",
                ParagraphStyle("Sum", fontName="Helvetica", fontSize=9.5, leading=14, textColor=colors.HexColor("#334155"))
            )
            story.append(summary_text)

            idx_count += 1
            if idx_count < total_cos:
                story.append(PageBreak())

        doc.build(story)
        print(f"Exported master portfolio summary PDF ({total_cos} pages) to {self.pdf_path}")


if __name__ == "__main__":
    gen = PortfolioReportGenerator()
    gen.generate_portfolio_pdf()
