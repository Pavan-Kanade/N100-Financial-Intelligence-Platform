"""
Unit tests for Cash Flow KPIs and Capital Allocation Classifier (src/analytics/cashflow_kpis.py).
"""

import pytest
from src.analytics.cashflow_kpis import (
    compute_free_cash_flow,
    compute_cfo_quality_score,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
    classify_capital_allocation,
)


def test_free_cash_flow_positive_and_negative():
    assert compute_free_cash_flow(100, -40) == 60.0
    assert compute_free_cash_flow(50, -100) == -50.0  # negative FCF allowed
    assert compute_free_cash_flow(None, -40) is None


def test_cfo_quality_score():
    cfo = [120, 150, 110, 130, 140]
    pat = [100, 100, 100, 100, 100]
    score, cat = compute_cfo_quality_score(cfo, pat)
    assert score == 1.3
    assert cat == "High Quality"

    cfo_low = [30, 40, 20, 40, 20]
    score_low, cat_low = compute_cfo_quality_score(cfo_low, pat)
    assert score_low == 0.3
    assert cat_low == "Accrual Risk"


def test_capex_intensity():
    # CFI = -20, Sales = 1000 -> 2% -> Asset Light
    val1, cat1 = compute_capex_intensity(-20, 1000)
    assert val1 == 2.0
    assert cat1 == "Asset Light"

    # CFI = -50, Sales = 1000 -> 5% -> Moderate
    val2, cat2 = compute_capex_intensity(-50, 1000)
    assert val2 == 5.0
    assert cat2 == "Moderate"

    # CFI = -100, Sales = 1000 -> 10% -> Capital Intensive
    val3, cat3 = compute_capex_intensity(-100, 1000)
    assert val3 == 10.0
    assert cat3 == "Capital Intensive"


def test_fcf_conversion_rate():
    assert compute_fcf_conversion_rate(60, 100) == 60.0
    assert compute_fcf_conversion_rate(60, 0) is None


def test_capital_allocation_patterns():
    # (+, -, -) with high CFO/PAT -> Shareholder Returns
    cfo_s, cfi_s, cff_s, label1 = classify_capital_allocation(100, -50, -30, cfo_pat_ratio=1.2)
    assert (cfo_s, cfi_s, cff_s) == ("+", "-", "-")
    assert label1 == "Shareholder Returns"

    # (+, -, -) default -> Reinvestor
    _, _, _, label2 = classify_capital_allocation(100, -50, -30, cfo_pat_ratio=0.8)
    assert label2 == "Reinvestor"

    # (-, +, +) -> Distress Signal
    _, _, _, label3 = classify_capital_allocation(-50, 20, 30)
    assert label3 == "Distress Signal"

    # (-, -, +) -> Growth Funded by Debt
    _, _, _, label4 = classify_capital_allocation(-50, -20, 30)
    assert label4 == "Growth Funded by Debt"
