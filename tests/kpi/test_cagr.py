"""
Unit tests for CAGR calculation engine (src/analytics/cagr.py).
Tests all 6 edge-case flags and formula correctness.
"""

import pytest
from src.analytics.cagr import calculate_cagr, calculate_series_cagr


def test_cagr_normal_positive_positive():
    val, flag = calculate_cagr(100, 161.051, 5)
    assert flag == "NORMAL"
    assert abs(val - 10.0) < 0.1


def test_cagr_decline_to_loss():
    val, flag = calculate_cagr(100, -50, 5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_turnaround():
    val, flag = calculate_cagr(-50, 100, 5)
    assert val is None
    assert flag == "TURNAROUND"


def test_cagr_both_negative():
    val, flag = calculate_cagr(-100, -50, 5)
    assert val is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_zero_base():
    val, flag = calculate_cagr(0, 100, 5)
    assert val is None
    assert flag == "ZERO_BASE"


def test_cagr_insufficient_data():
    val, flag = calculate_cagr(None, 100, 5)
    assert val is None
    assert flag == "INSUFFICIENT"

    val_n, flag_n = calculate_cagr(100, 200, 0)
    assert val_n is None
    assert flag_n == "INSUFFICIENT"


def test_series_cagr_sufficient():
    series = [("2019-03", 100.0), ("2020-03", 110.0), ("2021-03", 121.0), ("2022-03", 133.1)]
    val, flag = calculate_series_cagr(series, 3)
    assert flag == "NORMAL"
    assert abs(val - 10.0) < 0.1


def test_series_cagr_insufficient_history():
    series = [("2022-03", 100.0), ("2023-03", 120.0)]
    val, flag = calculate_series_cagr(series, 5)
    assert val is None
    assert flag == "INSUFFICIENT"


def test_cagr_turnaround_series():
    series = [("2019-03", -100.0), ("2020-03", 10.0), ("2021-03", 50.0), ("2022-03", 150.0)]
    val, flag = calculate_series_cagr(series, 3)
    assert val is None
    assert flag == "TURNAROUND"


def test_cagr_decline_to_loss_series():
    series = [("2019-03", 100.0), ("2020-03", 50.0), ("2021-03", 10.0), ("2022-03", -20.0)]
    val, flag = calculate_series_cagr(series, 3)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"
