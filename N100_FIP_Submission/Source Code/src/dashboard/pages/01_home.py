import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Home / Overview Screen (01_home.py)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_companies, get_ratios, get_sectors, get_valuation

st.header("📊 Market Overview & Summary Analytics")

# Year Selector in Sidebar
selected_year = st.sidebar.selectbox("Select Financial Year", ["2023-03", "2024-03", "2022-03", "2021-03", "2020-03", "2019-03"], index=0)

ratios_df = get_ratios(year=selected_year)
comp_df = get_companies()
sec_df = get_sectors()
val_df = get_valuation()

if ratios_df.empty:
    st.warning(f"No data available for year {selected_year}. Showing latest available data.")
    ratios_df = get_ratios()

# Merge datasets
merged = pd.merge(ratios_df, comp_df[["id"]].rename(columns={"id": "company_id"}), on="company_id", how="inner")
merged = pd.merge(merged, sec_df, on="company_id", how="left")
merged = pd.merge(merged, val_df[val_df["year"] == selected_year][["company_id", "pe_ratio"]], on="company_id", how="left")

# Top 6 KPI Tiles
col1, col2, col3, col4, col5, col6 = st.columns(6)

avg_roe = merged["return_on_equity_pct"].mean()
med_pe = merged["pe_ratio"].median()
med_de = merged["debt_to_equity"].median()
total_cos = len(merged["company_id"].unique())
med_cagr = merged["revenue_cagr_5yr"].median()
debt_free_cnt = (merged["debt_to_equity"] <= 0.05).sum()

col1.metric("Avg ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
col2.metric("Median P/E", f"{med_pe:.1f}x" if pd.notna(med_pe) else "N/A")
col3.metric("Median D/E", f"{med_de:.2f}" if pd.notna(med_de) else "N/A")
col4.metric("Total Companies", f"{total_cos}")
col5.metric("Med Rev CAGR 5Y", f"{med_cagr:.1f}%" if pd.notna(med_cagr) else "N/A")
col6.metric("Debt-Free Cos", f"{debt_free_cnt}")

st.write("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Sector Breakdown")
    sec_counts = merged.groupby("broad_sector")["company_id"].count().reset_index()
    sec_counts.columns = ["Sector", "Company Count"]
    fig_donut = px.pie(
        sec_counts,
        names="Sector",
        values="Company Count",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.subheader("Top 5 Quality Compounders")
    top5 = merged.sort_values(by="composite_quality_score", ascending=False).head(5)
    cols_show = ["company_id", "broad_sector", "composite_quality_score", "return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr"]
    st.dataframe(
        top5[cols_show].rename(columns={
            "company_id": "Ticker",
            "broad_sector": "Sector",
            "composite_quality_score": "Quality Score",
            "return_on_equity_pct": "ROE %",
            "debt_to_equity": "D/E",
            "revenue_cagr_5yr": "5Y Rev CAGR %"
        }),
        use_container_width=True,
        hide_index=True
    )
