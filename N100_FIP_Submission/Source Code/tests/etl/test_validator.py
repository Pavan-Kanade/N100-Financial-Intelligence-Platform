"""
Unit tests for DQ Validator module (validator.py).
Tests triggering of DQ-01 to DQ-16 rules.
"""

import pytest
import pandas as pd
from src.etl.validator import DQValidator


@pytest.fixture
def validator():
    return DQValidator()


def test_dq01_duplicate_company(validator):
    companies = pd.DataFrame([
        {"id": "TCS", "company_name": "Tata Consultancy Services"},
        {"id": "TCS", "company_name": "Duplicate TCS"}
    ])
    df_res = validator.validate_all({"companies": companies})
    dq01_failures = df_res[df_res['rule_id'] == 'DQ-01']
    assert len(dq01_failures) > 0
    assert dq01_failures.iloc[0]['severity'] == 'CRITICAL'


def test_dq02_annual_pk_duplicate(validator):
    pl = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 1000},
        {"company_id": "TCS", "year": "2023-03", "sales": 1050}
    ])
    df_res = validator.validate_all({"profitandloss": pl})
    dq02_failures = df_res[df_res['rule_id'] == 'DQ-02']
    assert len(dq02_failures) > 0
    assert dq02_failures.iloc[0]['severity'] == 'CRITICAL'


def test_dq03_orphan_fk(validator):
    companies = pd.DataFrame([{"id": "TCS"}])
    pl = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03"},
        {"company_id": "INVALID_TICKER", "year": "2023-03"}
    ])
    df_res = validator.validate_all({"companies": companies, "profitandloss": pl})
    dq03_failures = df_res[df_res['rule_id'] == 'DQ-03']
    assert len(dq03_failures) == 1
    assert dq03_failures.iloc[0]['company_id'] == 'INVALID_TICKER'


def test_dq04_bs_balance(validator):
    bs = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "total_assets": 1000, "total_liabilities": 1050} # 5% diff
    ])
    df_res = validator.validate_all({"balancesheet": bs})
    dq04_failures = df_res[df_res['rule_id'] == 'DQ-04']
    assert len(dq04_failures) == 1
    assert dq04_failures.iloc[0]['severity'] == 'WARNING'


def test_dq05_opm_mismatch(validator):
    pl = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 1000, "operating_profit": 200, "opm_percentage": 25.0} # reported 25%, calculated 20%
    ])
    df_res = validator.validate_all({"profitandloss": pl})
    dq05_failures = df_res[df_res['rule_id'] == 'DQ-05']
    assert len(dq05_failures) == 1


def test_dq06_zero_sales(validator):
    pl = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 0}
    ])
    df_res = validator.validate_all({"profitandloss": pl})
    dq06_failures = df_res[df_res['rule_id'] == 'DQ-06']
    assert len(dq06_failures) == 1


def test_dq07_year_format(validator):
    pl = pd.DataFrame([
        {"company_id": "TCS", "year": "INVALID_YEAR"}
    ])
    df_res = validator.validate_all({"profitandloss": pl})
    dq07_failures = df_res[df_res['rule_id'] == 'DQ-07']
    assert len(dq07_failures) == 1
    assert dq07_failures.iloc[0]['severity'] == 'CRITICAL'


def test_dq08_ticker_format(validator):
    companies = pd.DataFrame([
        {"id": "A"} # length 1 (too short)
    ])
    df_res = validator.validate_all({"companies": companies})
    dq08_failures = df_res[df_res['rule_id'] == 'DQ-08']
    assert len(dq08_failures) == 1


def test_dq09_net_cash_mismatch(validator):
    cf = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "operating_activity": 100, "investing_activity": -50, "financing_activity": -20, "net_cash_flow": 100} # reported 100, computed 30
    ])
    df_res = validator.validate_all({"cashflow": cf})
    dq09_failures = df_res[df_res['rule_id'] == 'DQ-09']
    assert len(dq09_failures) == 1
