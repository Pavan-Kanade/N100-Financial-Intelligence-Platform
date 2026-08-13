"""
ReportLab PDF Tearsheet Engine for Nifty 100 Financial Intelligence Platform.
Generates 2-page company tearsheet PDFs for all 92 companies in reports/tearsheets/.
Page 1: Header, 6 KPI tiles, Revenue/PAT bar chart, ROE/ROCE line chart.
Page 2: Balance Sheet stacked bar, Cash Flow breakdown, Pros & Cons bullets, Capital Allocation badge.
"""

import os
import io
import sqlite3
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable


class CompanyTearsheetGenerator:
    def __init__(self, db_path: str = "data/nifty100.db", output_dir: str = "reports/tearsheets"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all_tearsheets(self):
        """
        Generates 2-page tearsheet PDFs for all 92 companies in nifty100.db.
        """
        conn = sqlite3.connect(self.db_path)

        comp_df = pd.read_sql("SELECT * FROM companies", conn)
        sec_df = pd.read_sql("SELECT * FROM sectors", conn)
        ratios_df = pd.read_sql("SELECT * FROM financial_ratios ORDER BY year ASC", conn)
        pnl_df = pd.read_sql("SELECT * FROM profitandloss ORDER BY year ASC", conn)
        bs_df = pd.read_sql("SELECT * FROM balancesheet ORDER BY year ASC", conn)
        cf_df = pd.read_sql("SELECT * FROM cashflow ORDER BY year ASC", conn)

        pc_csv_path = "output/pros_cons_generated.csv"
        pc_df = pd.read_csv(pc_csv_path) if os.path.exists(pc_csv_path) else pd.DataFrame()

        conn.close()

        count = 0
        skipped = []

        for _, c_row in comp_df.iterrows():
            cid = c_row["id"]
            cname = c_row["company_name"]

            c_ratios = ratios_df[ratios_df["company_id"] == cid]
            c_pnl = pnl_df[pnl_df["company_id"] == cid]
            c_bs = bs_df[bs_df["company_id"] == cid]
            c_cf = cf_df[cf_df["company_id"] == cid]
            c_sec = sec_df[sec_df["company_id"] == cid]

            if len(c_pnl) < 3:
                skipped.append(cid)
                continue

            sec_info = c_sec.iloc[0] if not c_sec.empty else {"broad_sector": "N/A", "sub_sector": "N/A"}
            c_pc = pc_df[pc_df["company_id"] == cid] if not pc_df.empty else pd.DataFrame()

            pdf_path = os.path.join(self.output_dir, f"{cid}_tearsheet.pdf")
            self.build_pdf(pdf_path, cid, cname, sec_info, c_ratios, c_pnl, c_bs, c_cf, c_pc)
            count += 1

        print(f"Generated {count} 2-page company tearsheet PDFs in {self.output_dir}/")
        if skipped:
            pd.DataFrame({"company_id": skipped}).to_csv("output/skipped_tearsheets.csv", index=False)
            print(f"Logged {len(skipped)} skipped tickers to output/skipped_tearsheets.csv")

    def build_pdf(self, pdf_path: str, cid: str, cname: str, sec_info: Dict, c_ratios: pd.DataFrame, c_pnl: pd.DataFrame, c_bs: pd.DataFrame, c_cf: pd.DataFrame, c_pc: pd.DataFrame):
        """
        Renders a 2-page ReportLab PDF tearsheet.
        """
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
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.HexColor("#FFFFFF"),
            alignment=0,
            spaceAfter=4
        )

        sub_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#E2E8F0"),
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
            fontSize=13,
            textColor=colors.HexColor("#1F4E78"),
            alignment=1
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B")
        )

        pro_bullet_style = ParagraphStyle(
            "ProBullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#15803D")
        )

        con_bullet_style = ParagraphStyle(
            "ConBullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#B91C1C")
        )

        story = []

        # ====================================================
        # PAGE 1: HEADER, 6 KPI TILES, P&L BARS, RATIO LINES
        # ====================================================
        header_p1 = Paragraph(f"{cname} ({cid})", title_style)
        header_p2 = Paragraph(f"Broad Sector: {sec_info.get('broad_sector', 'N/A')} | Industry: {sec_info.get('sub_sector', 'N/A')} | Nifty 100 Financial Intelligence", sub_style)

        header_table = Table([[header_p1], [header_p2]], colWidths=[540])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F4E78")),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # 6 KPI Tiles
        latest_r = c_ratios.iloc[-1] if not c_ratios.empty else {}
        latest_pnl = c_pnl.iloc[-1] if not c_pnl.empty else {}

        roe_v = latest_r.get("return_on_equity_pct")
        roce_v = latest_r.get("return_on_capital_employed_pct")
        npm_v = latest_r.get("net_profit_margin_pct")
        de_v = latest_r.get("debt_to_equity")
        cagr_v = latest_r.get("revenue_cagr_5yr")
        fcf_v = latest_r.get("free_cash_flow_cr")

        kpi_data = [
            [
                Paragraph("RETURN ON EQUITY", kpi_title_style),
                Paragraph("RETURN ON CAPITAL", kpi_title_style),
                Paragraph("NET PROFIT MARGIN", kpi_title_style)
            ],
            [
                Paragraph(f"{roe_v:.1f}%" if pd.notna(roe_v) else "N/A", kpi_val_style),
                Paragraph(f"{roce_v:.1f}%" if pd.notna(roce_v) else "N/A", kpi_val_style),
                Paragraph(f"{npm_v:.1f}%" if pd.notna(npm_v) else "N/A", kpi_val_style)
            ],
            [
                Paragraph("DEBT TO EQUITY", kpi_title_style),
                Paragraph("5Y REVENUE CAGR", kpi_title_style),
                Paragraph("FREE CASH FLOW", kpi_title_style)
            ],
            [
                Paragraph(f"{de_v:.2f}" if pd.notna(de_v) else "N/A", kpi_val_style),
                Paragraph(f"{cagr_v:.1f}%" if pd.notna(cagr_v) else "N/A", kpi_val_style),
                Paragraph(f"₹{fcf_v:,.0f} Cr" if pd.notna(fcf_v) else "N/A", kpi_val_style)
            ]
        ]

        kpi_table = Table(kpi_data, colWidths=[180, 180, 180])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 12))

        # Render Page 1 Charts via Matplotlib
        chart1_img = self.render_pnl_chart(c_pnl)
        chart2_img = self.render_ratio_chart(c_ratios)

        chart_table = Table([[Image(chart1_img, width=260, height=210), Image(chart2_img, width=260, height=210)]], colWidths=[270, 270])
        chart_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(chart_table)

        # ====================================================
        # PAGE 2: BALANCE SHEET, CASH FLOW, PROS & CONS, BADGE
        # ====================================================
        story.append(PageBreak())

        # Page 2 Header
        header_p2_1 = Paragraph(f"{cname} ({cid}) - Balance Sheet & Qualitative Analysis", title_style)
        header_table2 = Table([[header_p2_1]], colWidths=[540])
        header_table2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F4E78")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(header_table2)
        story.append(Spacer(1, 10))

        chart3_img = self.render_bs_chart(c_bs)
        chart4_img = self.render_cf_waterfall(c_cf)

        chart_table2 = Table([[Image(chart3_img, width=260, height=200), Image(chart4_img, width=260, height=200)]], colWidths=[270, 270])
        chart_table2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(chart_table2)
        story.append(Spacer(1, 10))

        # Pros and Cons Bullets
        pros_list = c_pc[c_pc["type"] == "pro"]["text"].tolist() if not c_pc.empty else []
        cons_list = c_pc[c_pc["type"] == "con"]["text"].tolist() if not c_pc.empty else []

        if not pros_list:
            pros_list = ["Resilient market positioning in industry", "Established operational history"]
        if not cons_list:
            cons_list = ["Exposed to sector-wide input cost fluctuations", "General market cyclicality risk"]

        pros_elements = [Paragraph(f"• {p}", pro_bullet_style) for p in pros_list[:3]]
        cons_elements = [Paragraph(f"• {c}", con_bullet_style) for c in cons_list[:3]]

        pc_table_data = [
            [Paragraph("<b>STRENGTHS & PROS</b>", ParagraphStyle("P", fontName="Helvetica-Bold", textColor=colors.HexColor("#15803D"))),
             Paragraph("<b>KEY CONCERNS & CONS</b>", ParagraphStyle("C", fontName="Helvetica-Bold", textColor=colors.HexColor("#B91C1C")))],
            [pros_elements, cons_elements]
        ]

        pc_table = Table(pc_table_data, colWidths=[270, 270])
        pc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0FDF4")),
            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#FEF2F2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP")
        ]))
        story.append(pc_table)
        story.append(Spacer(1, 10))

        # Capital Allocation Badge Footer
        cap_alloc = latest_r.get("capital_allocation_pattern", "MODERATE_CAPEX")
        badge_p = Paragraph(f"<b>CAPITAL ALLOCATION CLASSIFICATION:</b> <font color='#1F4E78'><b>{cap_alloc}</b></font>", body_style)
        badge_table = Table([[badge_p]], colWidths=[540])
        badge_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 8)
        ]))
        story.append(badge_table)

        doc.build(story)

    def render_pnl_chart(self, df: pd.DataFrame) -> io.BytesIO:
        fig, ax = plt.subplots(figsize=(4.5, 3.2))
        sub = df.tail(10)
        x = np.arange(len(sub))
        width = 0.35

        ax.bar(x - width/2, sub["sales"], width, label="Sales", color="#1F4E78")
        ax.bar(x + width/2, sub["net_profit"], width, label="PAT", color="#2CA02C")
        ax.set_xticks(x)
        ax.set_xticklabels(sub["year"].str.replace("-03", ""), rotation=45, fontsize=7)
        ax.set_title("10-Year Revenue & Net Profit (Cr)", fontsize=9, fontweight="bold", pad=8)
        ax.legend(fontsize=7)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf

    def render_ratio_chart(self, df: pd.DataFrame) -> io.BytesIO:
        fig, ax = plt.subplots(figsize=(4.5, 3.2))
        sub = df.tail(10)
        x = np.arange(len(sub))

        ax.plot(x, sub["return_on_equity_pct"], marker="o", color="#1F4E78", label="ROE %", linewidth=1.5)
        ax.plot(x, sub["return_on_capital_employed_pct"], marker="s", color="#FF7F0E", linestyle="--", label="ROCE %", linewidth=1.5)
        ax.set_xticks(x)
        ax.set_xticklabels(sub["year"].str.replace("-03", ""), rotation=45, fontsize=7)
        ax.set_title("ROE & ROCE Trajectory (%)", fontsize=9, fontweight="bold", pad=8)
        ax.legend(fontsize=7)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf

    def render_bs_chart(self, df: pd.DataFrame) -> io.BytesIO:
        fig, ax = plt.subplots(figsize=(4.5, 3.0))
        sub = df.tail(6)
        x = np.arange(len(sub))

        eq = sub["equity_capital"].fillna(0) + sub["reserves"].fillna(0)
        borr = sub["borrowings"].fillna(0)
        other = sub["other_liabilities"].fillna(0)

        ax.bar(x, eq, label="Equity+Reserves", color="#1F4E78")
        ax.bar(x, borr, bottom=eq, label="Borrowings", color="#D9534F")
        ax.bar(x, other, bottom=eq+borr, label="Other Liab", color="#A6A6A6")

        ax.set_xticks(x)
        ax.set_xticklabels(sub["year"].str.replace("-03", ""), rotation=45, fontsize=7)
        ax.set_title("Balance Sheet Composition (Cr)", fontsize=9, fontweight="bold", pad=8)
        ax.legend(fontsize=7)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf

    def render_cf_waterfall(self, df: pd.DataFrame) -> io.BytesIO:
        fig, ax = plt.subplots(figsize=(4.5, 3.0))
        if not df.empty:
            latest = df.iloc[-1]
            cfo = latest.get("operating_activity", 0.0)
            cfi = latest.get("investing_activity", 0.0)
            cff = latest.get("financing_activity", 0.0)
            net_cf = latest.get("net_cash_flow", 0.0)

            cats = ["CFO", "CFI", "CFF", "Net Cash"]
            vals = [cfo, cfi, cff, net_cf]
            colors_list = ["#2CA02C" if v >= 0 else "#D9534F" for v in vals]

            ax.bar(cats, vals, color=colors_list)
            ax.set_title(f"Cash Flow Breakdown ({latest.get('year', '')})", fontsize=9, fontweight="bold", pad=8)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.grid(axis="y", linestyle="--", alpha=0.5)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf


if __name__ == "__main__":
    gen = CompanyTearsheetGenerator()
    gen.generate_all_tearsheets()
