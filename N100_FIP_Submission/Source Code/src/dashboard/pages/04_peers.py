import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Peer Comparison Screen (04_peers.py)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.dashboard.utils.db import get_peers, get_ratios, get_companies, get_sectors

st.header("👥 Peer Group Comparison & Radar Analysis")

peers_df = get_peers()
group_names = sorted(peers_df["peer_group_name"].unique().tolist())

selected_group = st.selectbox("Select Peer Group", options=group_names, index=0)

group_peers = peers_df[peers_df["peer_group_name"] == selected_group]

conn_ratios = get_ratios(year="2023-03")
comp_df = get_companies()

merged_group = pd.merge(group_peers, conn_ratios, on="company_id", how="inner")
merged_group = pd.merge(merged_group, comp_df[["id", "company_name"]].rename(columns={"id": "company_id"}), on="company_id", how="left")

if merged_group.empty:
    st.warning(f"No ratio data available for peer group {selected_group}.")
    st.stop()

company_list = merged_group["company_id"].tolist()
selected_ticker = st.selectbox("Select Benchmark/Target Company for Radar Overlay", options=company_list, index=0)

# Radar Chart Setup (8 metrics)
radar_metrics = [
    ("return_on_equity_pct", "ROE"),
    ("return_on_capital_employed_pct", "ROCE"),
    ("net_profit_margin_pct", "NPM"),
    ("debt_to_equity", "D/E"),
    ("free_cash_flow_cr", "FCF"),
    ("pat_cagr_5yr", "PAT CAGR"),
    ("revenue_cagr_5yr", "Rev CAGR"),
    ("composite_quality_score", "Quality Score")
]

# Normalise metrics 0-100 for polar rendering
norm_data = merged_group.copy()
for m_col, _ in radar_metrics:
    s = norm_data[m_col].fillna(0.0)
    p10, p90 = s.quantile(0.10), s.quantile(0.90)
    if p90 == p10:
        norm_data[m_col + "_norm"] = 50.0
    else:
        scaled = ((s.clip(p10, p90) - p10) / (p90 - p10)) * 100.0
        if m_col == "debt_to_equity":
            scaled = 100.0 - scaled
        norm_data[m_col + "_norm"] = scaled

target_row = norm_data[norm_data["company_id"] == selected_ticker].iloc[0]
peer_avg = norm_data[[m + "_norm" for m, _ in radar_metrics]].mean().values

target_vals = [target_row[m + "_norm"] for m, _ in radar_metrics]
axes_labels = [label for _, label in radar_metrics]

# Close polygon loops
target_loop = target_vals + [target_vals[0]]
peer_loop = peer_avg.tolist() + [peer_avg[0]]
axes_loop = axes_labels + [axes_labels[0]]

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=target_loop,
    theta=axes_loop,
    fill="toself",
    name=selected_ticker,
    line_color="#1F4E78"
))
fig_radar.add_trace(go.Scatterpolar(
    r=peer_loop,
    theta=axes_loop,
    name="Peer Group Average",
    line=dict(color="#D9534F", dash="dash")
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    margin=dict(t=30, b=30, l=30, r=30)
)

st.subheader(f"Radar Chart: {selected_ticker} vs {selected_group} Average")
st.plotly_chart(fig_radar, use_container_width=True)

st.write("---")

# Side-by-side KPI Table
st.subheader(f"Side-by-Side Peer Group Table ({len(merged_group)} Companies)")

cols_table = [
    "company_id", "company_name", "is_benchmark", "return_on_equity_pct",
    "return_on_capital_employed_pct", "net_profit_margin_pct", "debt_to_equity",
    "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr", "composite_quality_score"
]

df_table = merged_group[cols_table].rename(columns={
    "company_id": "Ticker",
    "company_name": "Company",
    "is_benchmark": "Benchmark?",
    "return_on_equity_pct": "ROE %",
    "return_on_capital_employed_pct": "ROCE %",
    "net_profit_margin_pct": "NPM %",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "revenue_cagr_5yr": "5Y Rev CAGR %",
    "pat_cagr_5yr": "5Y PAT CAGR %",
    "composite_quality_score": "Composite Score"
})

def highlight_benchmark(s):
    return ['background-color: #FFD966; font-weight: bold;' if s["Benchmark?"] == 1 else '' for _ in s]

st.dataframe(df_table.style.apply(highlight_benchmark, axis=1), use_container_width=True, hide_index=True)
