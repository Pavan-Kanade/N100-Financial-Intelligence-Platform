"""
Unit tests for ETL normaliser module (normaliser.py).
Contains 35+ unit tests covering normalize_year and normalize_ticker.
"""

import pytest
from src.etl.normaliser import normalize_year, normalize_ticker


# ==========================================
# 20+ Unit Tests for normalize_year()
# ==========================================

def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"

def test_year_mar_space_23():
    assert normalize_year("Mar 23") == "2023-03"

def test_year_march2023():
    assert normalize_year("March-2023") == "2023-03"

def test_year_mar2023():
    assert normalize_year("Mar-2023") == "2023-03"

def test_year_fy23():
    assert normalize_year("FY23") == "2023-03"

def test_year_fy2023():
    assert normalize_year("FY2023") == "2023-03"

def test_year_fy_space_23():
    assert normalize_year("FY 23") == "2023-03"

def test_year_int_2023():
    assert normalize_year(2023) == "2023-03"

def test_year_str_2023():
    assert normalize_year("2023") == "2023-03"

def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"

def test_year_dec_space_22():
    assert normalize_year("Dec 22") == "2022-12"

def test_year_december2022():
    assert normalize_year("December-2022") == "2022-12"

def test_year_jun23():
    assert normalize_year("Jun-23") == "2023-06"

def test_year_june2023():
    assert normalize_year("June-2023") == "2023-06"

def test_year_sep21():
    assert normalize_year("Sep-21") == "2021-09"

def test_year_september2021():
    assert normalize_year("September-2021") == "2021-09"

def test_year_already_formatted():
    assert normalize_year("2023-03") == "2023-03"

def test_year_already_formatted_dec():
    assert normalize_year("2022-12") == "2022-12"

def test_year_garbage():
    assert normalize_year("garbage") == "PARSE_ERROR"

def test_year_xyz():
    assert normalize_year("xyz") == "PARSE_ERROR"

def test_year_none():
    assert normalize_year(None) == "PARSE_ERROR"

def test_year_empty():
    assert normalize_year("") == "PARSE_ERROR"

def test_year_whitespace_only():
    assert normalize_year("   ") == "PARSE_ERROR"


# ==========================================
# 15+ Unit Tests for normalize_ticker()
# ==========================================

def test_ticker_standard():
    assert normalize_ticker("TCS") == "TCS"

def test_ticker_lowercase():
    assert normalize_ticker("tcs") == "TCS"

def test_ticker_leading_whitespace():
    assert normalize_ticker("  TCS") == "TCS"

def test_ticker_trailing_whitespace():
    assert normalize_ticker("TCS  ") == "TCS"

def test_ticker_both_whitespace():
    assert normalize_ticker("  TCS  ") == "TCS"

def test_ticker_hyphen():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"

def test_ticker_hyphen_lowercase():
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"

def test_ticker_ampersand():
    assert normalize_ticker("M&M") == "M&M"

def test_ticker_ampersand_lowercase():
    assert normalize_ticker("m&m") == "M&M"

def test_ticker_hdfcbank():
    assert normalize_ticker("hdfcbank") == "HDFCBANK"

def test_ticker_reliance():
    assert normalize_ticker(" RELIANCE ") == "RELIANCE"

def test_ticker_none():
    assert normalize_ticker(None) == ""

def test_ticker_empty():
    assert normalize_ticker("") == ""

def test_ticker_number():
    assert normalize_ticker(12345) == "12345"

def test_ticker_mixed_case():
    assert normalize_ticker("InFy") == "INFY"
