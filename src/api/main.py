"""
FastAPI REST API Server Module for Nifty 100 Financial Intelligence Platform.
Implements 16 endpoints for company profiles, financial statements, ratios, screener,
sectors, peer benchmarks, valuation multiples, portfolio stats, and tearsheet PDF downloads.
"""

import os
import time
import sqlite3
import pandas as pd
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(
    title="Nifty 100 Financial Intelligence REST API",
    version="1.0.0",
    description="Production-grade REST API providing access to financial statements, ratios, screener, peer benchmarks, and PDF reports."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "data/nifty100.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


START_TIME = time.time()


# ==============================================================================
# 1. Health & System
# ==============================================================================

@app.get("/api/v1/health")
def health_check():
    conn = get_db()
    tables = [
        "companies", "profitandloss", "balancesheet", "cashflow", "analysis",
        "documents", "prosandcons", "sectors", "stock_prices", "financial_ratios",
        "peer_groups", "market_cap", "peer_percentiles"
    ]
    counts = {}
    for t in tables:
        try:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            counts[t] = 0
    conn.close()

    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": "1.0.0",
        "db_row_counts": counts
    }


# ==============================================================================
# 2. Company Endpoints
# ==============================================================================

@app.get("/api/v1/companies")
def list_companies(
    sector: Optional[str] = None,
    search: Optional[str] = None
):
    conn = get_db()
    query = "SELECT c.*, s.broad_sector, s.sub_sector FROM companies c LEFT JOIN sectors s ON c.id = s.company_id WHERE 1=1"
    params = []

    if sector:
        query += " AND s.broad_sector LIKE ?"
        params.append(f"%{sector}%")
    if search:
        query += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}")
def get_company(ticker: str):
    conn = get_db()
    comp = conn.execute("SELECT c.*, s.broad_sector, s.sub_sector FROM companies c LEFT JOIN sectors s ON c.id = s.company_id WHERE UPPER(c.id) = ?", (ticker.upper(),)).fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    ratios = conn.execute("SELECT * FROM financial_ratios WHERE UPPER(company_id) = ? ORDER BY year DESC LIMIT 1", (ticker.upper(),)).fetchone()
    conn.close()

    res = dict(comp)
    res["latest_ratios"] = dict(ratios) if ratios else {}
    return res


@app.get("/api/v1/companies/{ticker}/pl")
def get_company_pl(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM profitandloss WHERE UPPER(company_id) = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No P&L records found for '{ticker}'.")
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/bs")
def get_company_bs(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM balancesheet WHERE UPPER(company_id) = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No Balance Sheet records found for '{ticker}'.")
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/cashflow")
def get_company_cf(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM cashflow WHERE UPPER(company_id) = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No Cash Flow records found for '{ticker}'.")
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/ratios")
def get_company_ratios(ticker: str, year: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM financial_ratios WHERE UPPER(company_id) = ?"
    params = [ticker.upper()]

    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No financial ratios found for '{ticker}'.")
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/tearsheet")
def get_tearsheet_pdf(ticker: str):
    pdf_path = f"reports/tearsheets/{ticker.upper()}_tearsheet.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Tearsheet PDF for '{ticker}' not found.")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{ticker.upper()}_tearsheet.pdf")


# ==============================================================================
# 3. Screener, Sectors, Peers & Valuation Endpoints
# ==============================================================================

@app.get("/api/v1/screener")
def run_screener(
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None,
    sector: Optional[str] = None
):
    from src.screener.engine import ScreenerEngine
    eng = ScreenerEngine()

    filters = {}
    if min_roe is not None:
        filters["return_on_equity_pct"] = {"min": min_roe}
    if max_de is not None:
        filters["debt_to_equity"] = {"max": max_de}
    if min_fcf is not None:
        filters["free_cash_flow_cr"] = {"min": min_fcf}
    if min_rev_cagr_5yr is not None:
        filters["revenue_cagr_5yr"] = {"min": min_rev_cagr_5yr}
    if min_pat_cagr_5yr is not None:
        filters["pat_cagr_5yr"] = {"min": min_pat_cagr_5yr}
    if max_pe is not None:
        filters["pe_ratio"] = {"max": max_pe}

    df_base = eng.get_merged_dataset("2023-03")
    if sector:
        df_base = df_base[df_base["broad_sector"].astype(str).str.contains(sector, case=False, na=False)]

    res_df = eng.apply_filters(df_base, filters)
    records = res_df.to_dict("records")
    clean_records = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records]
    return clean_records


@app.get("/api/v1/sectors")
def list_sectors():
    conn = get_db()
    query = """
    SELECT s.broad_sector,
           COUNT(s.company_id) as company_count,
           ROUND(AVG(r.return_on_equity_pct), 2) as median_roe,
           ROUND(AVG(r.debt_to_equity), 2) as median_de
    FROM sectors s
    LEFT JOIN financial_ratios r ON s.company_id = r.company_id AND r.year='2023-03'
    GROUP BY s.broad_sector
    ORDER BY company_count DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    conn = get_db()
    query = """
    SELECT c.id as company_id, c.company_name, s.broad_sector, s.sub_sector,
           r.return_on_equity_pct, r.debt_to_equity, r.revenue_cagr_5yr, r.free_cash_flow_cr
    FROM companies c
    JOIN sectors s ON c.id = s.company_id
    LEFT JOIN financial_ratios r ON c.id = r.company_id AND r.year='2023-03'
    WHERE s.broad_sector LIKE ?
    ORDER BY c.company_name ASC
    """
    rows = conn.execute(query, [f"%{sector}%"]).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No companies found for sector '{sector}'.")
    return [dict(r) for r in rows]


@app.get("/api/v1/peers/{group_name}")
def get_peer_group(group_name: str):
    conn = get_db()
    query = """
    SELECT p.peer_group_name, p.company_id, c.company_name, p.is_benchmark
    FROM peer_groups p
    JOIN companies c ON p.company_id = c.id
    WHERE p.peer_group_name LIKE ?
    """
    rows = conn.execute(query, [f"%{group_name}%"]).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found.")
    return [dict(r) for r in rows]


@app.get("/api/v1/companies/{ticker}/peers/compare")
def get_peer_compare(ticker: str):
    from src.analytics.peer import PeerEngine
    eng = PeerEngine()
    info = eng.get_company_peer_info(ticker.upper())
    if info.get("status") == "unmapped":
        raise HTTPException(status_code=404, detail=f"No peer group assigned for '{ticker}'.")
    return info


@app.get("/api/v1/market-cap/{ticker}")
def get_market_cap(ticker: str):
    conn = get_db()
    rows = conn.execute("SELECT * FROM market_cap WHERE UPPER(company_id) = ? ORDER BY year ASC", (ticker.upper(),)).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No market cap data found for '{ticker}'.")
    return [dict(r) for r in rows]


@app.get("/api/v1/portfolio/stats")
def get_portfolio_stats():
    csv_path = "output/portfolio_stats.csv"
    if not os.path.exists(csv_path):
        from src.analytics.clustering import ClusterEngine
        ClusterEngine().run()
    df = pd.read_csv(csv_path)
    return df.to_dict("records")


@app.get("/api/v1/companies/{ticker}/documents")
def get_company_documents(ticker: str):
    conn = get_db()
    rows = conn.execute("SELECT * FROM documents WHERE UPPER(company_id) = ? ORDER BY year DESC", (ticker.upper(),)).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No documents found for '{ticker}'.")

    result = []
    for r in rows:
        d = dict(r)
        url = str(d.get("annual_report", ""))
        d["is_url_valid"] = url.startswith("http://") or url.startswith("https://")
        result.append(d)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
