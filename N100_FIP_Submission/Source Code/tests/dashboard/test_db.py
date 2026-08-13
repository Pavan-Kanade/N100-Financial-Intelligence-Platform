"""
Unit tests for Cached SQLite Data Provider (src/dashboard/utils/db.py).
Tests database query functions and return structure.
"""

import pytest
import pandas as pd
from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_bs, get_cf,
    get_sectors, get_peers, get_valuation, get_documents, get_prosandcons
)


def test_get_companies():
    df = get_companies()
    assert not df.empty
    assert len(df) == 92
    assert "id" in df.columns


def test_get_ratios_by_ticker():
    df = get_ratios(ticker="TCS")
    assert not df.empty
    assert (df["company_id"] == "TCS").all()


def test_get_pl_by_ticker():
    df = get_pl(ticker="RELIANCE")
    assert not df.empty
    assert "sales" in df.columns


def test_get_bs_by_ticker():
    df = get_bs(ticker="INFY")
    assert not df.empty
    assert "total_assets" in df.columns


def test_get_cf_by_ticker():
    df = get_cf(ticker="HDFCBANK")
    assert not df.empty
    assert "operating_activity" in df.columns


def test_get_sectors():
    df = get_sectors()
    assert not df.empty
    assert "broad_sector" in df.columns


def test_get_peers_by_group():
    df = get_peers(group_name="IT Services")
    assert not df.empty
    assert (df["peer_group_name"] == "IT Services").all()


def test_get_valuation_by_ticker():
    df = get_valuation(ticker="TCS")
    assert not df.empty
    assert "pe_ratio" in df.columns


def test_get_documents_by_ticker():
    df = get_documents(ticker="TCS")
    assert not df.empty


def test_get_prosandcons_by_ticker():
    df = get_prosandcons(ticker="TCS")
    assert not df.empty
