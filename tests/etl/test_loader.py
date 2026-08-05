"""
Integration and End-to-End Tests for ETL Loader & SQLite Database (nifty100.db).
"""

import os
import sqlite3
import pytest
import pandas as pd
from src.etl.loader import ETLLoader


@pytest.fixture(scope="module")
def loaded_db():
    loader = ETLLoader()
    df_audit, df_failures = loader.run_pipeline()
    return loader.db_path, df_audit, df_failures


def test_db_file_exists(loaded_db):
    db_path, _, _ = loaded_db
    assert os.path.exists(db_path)


def test_companies_rowcount(loaded_db):
    db_path, _, _ = loaded_db
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM companies;").fetchone()[0]
    conn.close()
    assert count == 92


def test_foreign_key_integrity(loaded_db):
    db_path, _, _ = loaded_db
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    fk_checks = conn.execute("PRAGMA foreign_key_check;").fetchall()
    conn.close()
    assert len(fk_checks) == 0


def test_audit_csv_file(loaded_db):
    loader = ETLLoader()
    audit_csv = os.path.join(loader.output_dir, "load_audit.csv")
    assert os.path.exists(audit_csv)
    df_audit = pd.read_csv(audit_csv)
    assert len(df_audit) >= 10
    assert "rows_in" in df_audit.columns
    assert "rows_out" in df_audit.columns
    assert "rejected" in df_audit.columns


def test_validation_failures_csv_file(loaded_db):
    loader = ETLLoader()
    failures_csv = os.path.join(loader.output_dir, "validation_failures.csv")
    assert os.path.exists(failures_csv)
    df_fail = pd.read_csv(failures_csv)
    assert "rule_id" in df_fail.columns
    assert "severity" in df_fail.columns


def test_time_series_tables_populated(loaded_db):
    db_path, _, _ = loaded_db
    conn = sqlite3.connect(db_path)
    pl_cnt = conn.execute("SELECT COUNT(*) FROM profitandloss;").fetchone()[0]
    bs_cnt = conn.execute("SELECT COUNT(*) FROM balancesheet;").fetchone()[0]
    cf_cnt = conn.execute("SELECT COUNT(*) FROM cashflow;").fetchone()[0]
    sp_cnt = conn.execute("SELECT COUNT(*) FROM stock_prices;").fetchone()[0]
    conn.close()

    assert pl_cnt > 1000
    assert bs_cnt > 1000
    assert cf_cnt > 1000
    assert sp_cnt == 5520
