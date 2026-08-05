"""
Cached SQLite Data Provider for Streamlit Dashboard.
Applies @st.cache_data(ttl=600) to every query function to ensure fast rendering.
"""

import sqlite3
import pandas as pd
import streamlit as st
from typing import Optional

DB_PATH = "data/nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: Optional[str] = None, year: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper())
    if year:
        query += " AND year = ?"
        params.append(year)

    df = pd.read_sql(query, conn, params=params if params else None)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if ticker:
        df = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", conn, params=[ticker.upper()])
    else:
        df = pd.read_sql("SELECT * FROM profitandloss ORDER BY year ASC", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if ticker:
        df = pd.read_sql("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC", conn, params=[ticker.upper()])
    else:
        df = pd.read_sql("SELECT * FROM balancesheet ORDER BY year ASC", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if ticker:
        df = pd.read_sql("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC", conn, params=[ticker.upper()])
    else:
        df = pd.read_sql("SELECT * FROM cashflow ORDER BY year ASC", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if group_name:
        df = pd.read_sql("SELECT * FROM peer_groups WHERE peer_group_name = ?", conn, params=[group_name])
    else:
        df = pd.read_sql("SELECT * FROM peer_groups", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if ticker:
        df = pd.read_sql("SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC", conn, params=[ticker.upper()])
    else:
        df = pd.read_sql("SELECT * FROM market_cap ORDER BY year ASC", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if ticker:
        df = pd.read_sql("SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC", conn, params=[ticker.upper()])
    else:
        df = pd.read_sql("SELECT * FROM documents ORDER BY year DESC", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_prosandcons(ticker: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    if ticker:
        df = pd.read_sql("SELECT * FROM prosandcons WHERE company_id = ?", conn, params=[ticker.upper()])
    else:
        df = pd.read_sql("SELECT * FROM prosandcons", conn)
    conn.close()
    return df
