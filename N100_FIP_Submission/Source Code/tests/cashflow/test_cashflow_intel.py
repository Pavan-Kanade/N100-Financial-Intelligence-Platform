"""
Unit tests for Cash Flow Intelligence Module (src/analytics/cashflow_intelligence.py).
"""

import os
import pytest
import pandas as pd
from src.analytics.cashflow_intelligence import CashFlowIntelligence


@pytest.fixture(scope="module")
def cashflow_intel_data():
    intel = CashFlowIntelligence()
    return intel.run()


def test_cashflow_intelligence_excel_exists(cashflow_intel_data):
    assert os.path.exists("output/cashflow_intelligence.xlsx")
    assert os.path.exists("output/distress_alerts.csv")
    assert os.path.exists("output/pattern_changes.csv")


def test_cashflow_intelligence_rowcount(cashflow_intel_data):
    df_intel, _ = cashflow_intel_data
    assert len(df_intel) >= 90


def test_cashflow_labels_valid(cashflow_intel_data):
    df_intel, _ = cashflow_intel_data
    valid_q_labels = {"High Quality", "Moderate", "Accrual Risk"}
    valid_c_labels = {"Asset Light", "Moderate", "Capital Intensive"}

    assert set(df_intel["cfo_quality_label"].unique()).issubset(valid_q_labels)
    assert set(df_intel["capex_label"].unique()).issubset(valid_c_labels)
