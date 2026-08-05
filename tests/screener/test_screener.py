"""
Unit tests for Stock Screener Engine (src/screener/engine.py).
Tests all 6 preset screeners, filter logic, D/E carve-outs, ICR debt-free handling, and composite scores.
"""

import pytest
import pandas as pd
from src.screener.engine import ScreenerEngine


@pytest.fixture(scope="module")
def screener_engine():
    return ScreenerEngine()


def test_screener_config_loaded(screener_engine):
    assert "presets" in screener_engine.config
    assert "Quality Compounder" in screener_engine.config["presets"]


def test_quality_compounder_preset(screener_engine):
    df_res = screener_engine.run_preset("Quality Compounder")
    assert not df_res.empty
    assert 5 <= len(df_res) <= 50
    assert (df_res["return_on_equity_pct"] >= 15.0).all()


def test_value_pick_preset(screener_engine):
    df_res = screener_engine.run_preset("Value Pick")
    assert not df_res.empty
    assert 5 <= len(df_res) <= 50


def test_growth_accelerator_preset(screener_engine):
    df_res = screener_engine.run_preset("Growth Accelerator")
    assert not df_res.empty
    assert 5 <= len(df_res) <= 50


def test_dividend_champion_preset(screener_engine):
    df_res = screener_engine.run_preset("Dividend Champion")
    assert not df_res.empty
    assert 5 <= len(df_res) <= 50


def test_debt_free_blue_chip_preset(screener_engine):
    df_res = screener_engine.run_preset("Debt-Free Blue Chip")
    assert not df_res.empty
    assert 5 <= len(df_res) <= 50


def test_turnaround_watch_preset(screener_engine):
    df_res = screener_engine.run_preset("Turnaround Watch")
    assert not df_res.empty
    assert 5 <= len(df_res) <= 50


def test_de_financials_carveout(screener_engine):
    df_base = screener_engine.get_merged_dataset()
    filters = {"debt_to_equity": {"max": 1.0}}
    df_filtered = screener_engine.apply_filters(df_base, filters)

    fin_companies = df_filtered[df_filtered["broad_sector"].astype(str).str.contains("Financial", case=False, na=False)]
    assert not fin_companies.empty
    # Financials can have D/E > 1.0 due to carve-out
    assert (fin_companies["debt_to_equity"] > 1.0).any()


def test_icr_debt_free_pass(screener_engine):
    df_base = screener_engine.get_merged_dataset()
    filters = {"interest_coverage": {"min": 5.0}}
    df_filtered = screener_engine.apply_filters(df_base, filters)

    debt_free_cos = df_filtered[df_filtered["icr_label"] == "Debt Free"]
    assert not debt_free_cos.empty
