"""
Unit tests for Auto Pros & Cons Generator (src/nlp/pros_cons_generator.py).
Tests rule execution, confidence scores, and guarantees 1 pro and 1 con per company.
"""

import os
import pytest
import sqlite3
import pandas as pd
from src.nlp.pros_cons_generator import ProsConsGenerator


@pytest.fixture(scope="module")
def pros_cons_df():
    gen = ProsConsGenerator()
    return gen.generate()


def test_pros_cons_csv_file_exists(pros_cons_df):
    assert os.path.exists("output/pros_cons_generated.csv")


def test_every_company_has_pro_and_con(pros_cons_df):
    conn = sqlite3.connect("data/nifty100.db")
    all_companies = pd.read_sql("SELECT id as company_id FROM companies", conn)["company_id"].tolist()
    conn.close()

    pros_cos = set(pros_cons_df[pros_cons_df["type"] == "pro"]["company_id"])
    cons_cos = set(pros_cons_df[pros_cons_df["type"] == "con"]["company_id"])

    for cid in all_companies:
        assert cid in pros_cos, f"Company {cid} missing pro"
        assert cid in cons_cos, f"Company {cid} missing con"


def test_confidence_scores_above_threshold(pros_cons_df):
    assert (pros_cons_df["confidence_pct"] > 60).all()
