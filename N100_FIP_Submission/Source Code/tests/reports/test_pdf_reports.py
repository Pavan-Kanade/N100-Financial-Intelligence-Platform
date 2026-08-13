"""
Unit tests for ReportLab PDF Report Generators (tearsheets, sector reports, portfolio summary).
"""

import os
import pytest
from src.reports.tearsheet import CompanyTearsheetGenerator
from src.reports.sector_report import SectorReportGenerator
from src.reports.portfolio import PortfolioReportGenerator


def test_tearsheet_pdf_generation():
    gen = CompanyTearsheetGenerator()
    gen.generate_all_tearsheets()

    pdf_files = [f for f in os.listdir("reports/tearsheets") if f.endswith(".pdf")]
    assert len(pdf_files) >= 90

    # Test size >= 30 KB
    sample_pdf = os.path.join("reports/tearsheets", pdf_files[0])
    size_kb = os.path.getsize(sample_pdf) / 1024.0
    assert size_kb >= 30.0


def test_sector_pdf_generation():
    gen = SectorReportGenerator()
    gen.generate_all_sector_reports()

    pdf_files = [f for f in os.listdir("reports/sector") if f.endswith(".pdf")]
    assert len(pdf_files) >= 10


def test_portfolio_pdf_generation():
    gen = PortfolioReportGenerator()
    gen.generate_portfolio_pdf()

    pdf_path = "reports/portfolio/portfolio_summary.pdf"
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 50000
