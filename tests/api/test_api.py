"""
Unit & Integration Tests for FastAPI REST API endpoints (src/api/main.py).
Verifies health check, company lookup, P&L, screener, sectors, peers, and valuation endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_api_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    assert data["db_row_counts"]["companies"] == 92


def test_api_list_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92


def test_api_get_company_valid_and_invalid():
    # Valid company
    res_tcs = client.get("/api/v1/companies/TCS")
    assert res_tcs.status_code == 200
    assert res_tcs.json()["id"] == "TCS"

    # Invalid company
    res_inv = client.get("/api/v1/companies/INVALID_TICKER")
    assert res_inv.status_code == 404


def test_api_company_financial_statements():
    # P&L
    res_pl = client.get("/api/v1/companies/TCS/pl")
    assert res_pl.status_code == 200
    assert len(res_pl.json()) >= 5

    # Balance Sheet
    res_bs = client.get("/api/v1/companies/TCS/bs")
    assert res_bs.status_code == 200

    # Cash Flow
    res_cf = client.get("/api/v1/companies/TCS/cashflow")
    assert res_cf.status_code == 200


def test_api_screener():
    response = client.get("/api/v1/screener?min_roe=15.0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    for comp in data:
        if comp.get("return_on_equity_pct") is not None:
            assert comp["return_on_equity_pct"] >= 15.0


def test_api_sectors_and_peers():
    # Sectors
    res_sec = client.get("/api/v1/sectors")
    assert res_sec.status_code == 200
    assert len(res_sec.json()) >= 10

    # Peer Group
    res_peer = client.get("/api/v1/peers/IT Services")
    assert res_peer.status_code == 200
    assert len(res_peer.json()) >= 3


def test_api_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
