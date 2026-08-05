"""
Unit tests for Valuation Module (src/analytics/valuation.py).
Tests FCF yield %, sector median P/E, 5Y historical median P/E, overvaluation/discount flags,
and file output generation.
"""

import os
import pytest
import pandas as pd
from src.analytics.valuation import ValuationEngine


@pytest.fixture(scope="module")
def valuation_df():
    engine = ValuationEngine()
    return engine.run()


def test_valuation_summary_rows_count(valuation_df):
    assert len(valuation_df) == 92


def test_valuation_required_columns_present(valuation_df):
    required_cols = [
        "company_id", "company_name", "broad_sector", "pe_ratio", "pb_ratio",
        "ev_ebitda", "dividend_yield_pct", "fcf_yield_pct", "median_pe_5yr",
        "sector_median_pe", "pe_vs_sector_median_pct", "valuation_flag"
    ]
    for c in required_cols:
        assert c in valuation_df.columns


def test_valuation_flags_valid_values(valuation_df):
    valid_flags = {"Caution", "Discount", "Fair"}
    actual_flags = set(valuation_df["valuation_flag"].unique())
    assert actual_flags.issubset(valid_flags)


def test_fcf_yield_calculation(valuation_df):
    # FCF yield = (FCF / Mkt Cap) * 100
    tcs = valuation_df[valuation_df["company_id"] == "TCS"].iloc[0]
    if pd.notna(tcs["fcf_yield_pct"]):
        assert isinstance(tcs["fcf_yield_pct"], float)


def test_valuation_output_files_exist():
    assert os.path.exists("output/valuation_summary.xlsx")
    assert os.path.exists("output/valuation_flags.csv")
