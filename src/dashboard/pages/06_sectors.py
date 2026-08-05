import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Sector Analysis Screen (06_sectors.py)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils.db import get_sectors, get_ratios, get_companies, get_valuation, get_pl

st.header("🏭 Sector Analysis & Industry Benchmarks")

sec_df = get_sectors()
broad_sectors = sorted(sec_df["broad_sector"].unique().tolist())

selected_sector = st.selectbox("Select Broad Sector", options=broad_sectors, index=0)

ratios_df = get_ratios(year="2023-03")
comp_df = get_companies()
val_df = get_valuation()
pl_df = get_pl()

# Merge datasets
merged = pd.merge(sec_df, ratios_df, on="company_id", how="inner")
merged = pd.merge(merged, comp_df[["id", "company_name"]].rename(columns={"id": "company_id"}), on="company_id", how="left")

val_23 = val_df[val_df["year"].astype(str).isin(["2023-03", "2023"])][["company_id", "market_cap_crore"]].drop_duplicates(subset=["company_id"])
merged = pd.merge(merged, val_23, on="company_id", how="left")

pnl_23 = pl_df[pl_df["year"] == "2023-03"][["company_id", "sales"]]
merged = pd.merge(merged, pnl_23, on="company_id", how="left")

sector_filtered = merged[merged["broad_sector"] == selected_sector].copy()

if sector_filtered.empty:
    st.warning(f"No data available for sector {selected_sector}.")
    st.stop()

# 1. Bubble Chart (X = Revenue, Y = ROE, size = Market Cap, color = sub_sector)
st.subheader(f"Bubble Chart: {selected_sector} (Revenue vs ROE vs Market Cap)")

sector_filtered["market_cap_crore_clean"] = sector_filtered["market_cap_crore"].fillna(1000.0).clip(lower=500.0)
sector_filtered["sales_clean"] = sector_filtered["sales"].fillna(100.0)
sector_filtered["roe_clean"] = sector_filtered["return_on_equity_pct"].fillna(0.0)

fig_bubble = px.scatter(
    sector_filtered,
    x="sales_clean",
    y="roe_clean",
    size="market_cap_crore_clean",
    color="sub_sector",
    hover_name="company_name",
    hover_data=["company_id", "debt_to_equity", "revenue_cagr_5yr"],
    text="company_id",
    labels={"sales_clean": "Revenue (sales Cr)", "roe_clean": "Return on Equity (ROE %)", "sub_sector": "Sub Sector"},
    size_max=50
)
fig_bubble.update_traces(textposition="top center")
fig_bubble.update_layout(margin=dict(t=30, b=30, l=30, r=30))

st.plotly_chart(fig_bubble, use_container_width=True)

st.write("---")

# 2. Sector Median KPI Bar Chart
st.subheader("Sector Median KPI Benchmarks Across All 11 Sectors")

sec_medians = merged.groupby("broad_sector")[["return_on_equity_pct", "operating_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr"]].median().reset_index()

metric_to_chart = st.radio("Select Metric for Sector Median Bar Chart", ["return_on_equity_pct", "operating_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr"], horizontal=True)

fig_bar = px.bar(
    sec_medians.sort_values(by=metric_to_chart, ascending=False),
    x="broad_sector",
    y=metric_to_chart,
    color="broad_sector",
    title=f"Sector Median {metric_to_chart}",
    labels={"broad_sector": "Sector", metric_to_chart: "Median Value"}
)
fig_bar.update_layout(showlegend=False, margin=dict(t=40, b=30, l=30, r=30))
st.plotly_chart(fig_bar, use_container_width=True)
