"""
Unit tests for profitability, leverage, and efficiency ratios (src/analytics/ratios.py).
"""

import pytest
from src.analytics.ratios import (
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_return_on_equity,
    compute_return_on_capital_employed,
    compute_return_on_assets,
    compute_debt_to_equity,
    check_high_leverage_flag,
    compute_interest_coverage,
    get_icr_label_and_warning,
    compute_net_debt,
    compute_asset_turnover,
)


def test_net_profit_margin_normal_and_zero():
    assert compute_net_profit_margin(100, 500) == 20.0
    assert compute_net_profit_margin(100, 0) is None
    assert compute_net_profit_margin(-50, 200) == -25.0


def test_opm_and_cross_check():
    assert compute_operating_profit_margin(150, 1000) == 15.0
    assert compute_operating_profit_margin(0, 1000) == 0.0
    assert compute_operating_profit_margin(100, 0) is None


def test_return_on_equity_positive_and_negative():
    assert compute_return_on_equity(100, 50, 450) == 20.0  # 100 / 500
    assert compute_return_on_equity(100, 10, -50) is None  # negative total equity -40


def test_roce_and_roa():
    # EBITDA=200, Dep=50 -> EBIT=150, Eq=100, Res=400, Bor=250 -> Cap=750 -> 150/750 = 20%
    assert compute_return_on_capital_employed(200, 50, 100, 400, 250) == 20.0
    assert compute_return_on_assets(50, 1000) == 5.0
    assert compute_return_on_assets(50, 0) is None


def test_debt_to_equity_debtfree_and_normal():
    assert compute_debt_to_equity(0, 100, 400) == 0.0  # debt-free returns 0.0
    assert compute_debt_to_equity(500, 100, 400) == 1.0  # 500 / 500
    assert compute_debt_to_equity(100, 10, -50) is None  # negative equity


def test_high_leverage_flag():
    assert check_high_leverage_flag(6.0, "Consumer Staples") is True
    assert check_high_leverage_flag(6.0, "Financials") is False  # Bank carve-out
    assert check_high_leverage_flag(2.0, "Consumer Staples") is False


def test_interest_coverage_and_label():
    # OpProfit=200, OtherInc=50, Interest=50 -> ICR = 250 / 50 = 5.0
    icr = compute_interest_coverage(200, 50, 50)
    assert icr == 5.0
    label, warn = get_icr_label_and_warning(icr, 50)
    assert label is None
    assert warn is False

    # Interest = 0 (Debt Free)
    icr_zero = compute_interest_coverage(200, 50, 0)
    assert icr_zero is None
    label_zero, warn_zero = get_icr_label_and_warning(icr_zero, 0)
    assert label_zero == "Debt Free"

    # ICR < 1.5 warning
    icr_low = compute_interest_coverage(100, 0, 80)  # 100/80 = 1.25
    _, warn_low = get_icr_label_and_warning(icr_low, 80)
    assert warn_low is True


def test_net_debt_and_asset_turnover():
    assert compute_net_debt(500, 100) == 400.0
    assert compute_asset_turnover(1000, 500) == 2.0
    assert compute_asset_turnover(1000, 0) is None
