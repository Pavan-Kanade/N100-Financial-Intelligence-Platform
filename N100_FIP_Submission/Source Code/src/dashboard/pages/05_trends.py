import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Trend Analysis Screen (05_trends.py)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.header("📉 Multi-Year Trend Analysis & Trajectory")

comp_df = get_companies()
company_options = [f"{r['id']} - {r['company_name']}" for _, r in comp_df.iterrows()]
selected_option = st.selectbox("Search or Select Company", options=company_options, index=0)
ticker = selected_option.split(" - ")[0].strip()

ratios_df = get_ratios(ticker=ticker)
pl_df = get_pl(ticker=ticker)

if ratios_df.empty:
    st.warning("No ratio history available for this ticker.")
    st.stop()

# Merge P&L metrics with ratios
merged_hist = pd.merge(ratios_df, pl_df[["year", "sales", "net_profit"]], on="year", how="left")
merged_hist = merged_hist.sort_values(by="year").reset_index(drop=True)

metric_choices = {
    "sales": "Revenue (sales Cr)",
    "net_profit": "Net Profit (Cr)",
    "return_on_equity_pct": "Return on Equity (ROE %)",
    "return_on_capital_employed_pct": "ROCE %",
    "net_profit_margin_pct": "Net Profit Margin %",
    "debt_to_equity": "Debt-to-Equity (D/E)",
    "free_cash_flow_cr": "Free Cash Flow (FCF Cr)",
    "operating_profit_margin_pct": "OPM %"
}

selected_metrics = st.multiselect(
    "Select Up to 3 Metrics to Overlay",
    options=list(metric_choices.keys()),
    default=["sales", "net_profit"],
    format_func=lambda x: metric_choices[x]
)

if not selected_metrics:
    st.info("Select at least 1 metric from the dropdown to display the trend chart.")
    st.stop()

if len(selected_metrics) > 3:
    st.warning("Maximum 3 metrics can be overlaid simultaneously. Showing first 3 selections.")
    selected_metrics = selected_metrics[:3]

fig_trend = go.Figure()

colors = ["#1F4E78", "#FF7F0E", "#2CA02C"]

for idx, m_col in enumerate(selected_metrics):
    if m_col in merged_hist.columns:
        s = merged_hist[m_col]
        # Calculate YoY % change
        yoy = s.pct_change() * 100.0
        
        text_labels = [
            f"{val:.1f}<br>({chg:+.1f}%)" if pd.notna(chg) else f"{val:.1f}"
            for val, chg in zip(s, yoy)
        ]

        fig_trend.add_trace(go.Scatter(
            x=merged_hist["year"],
            y=s,
            mode="lines+markers+text",
            name=metric_choices[m_col],
            text=text_labels,
            textposition="top center",
            line=dict(color=colors[idx % len(colors)], width=2.5)
        ))

fig_trend.update_layout(
    title=f"10-Year Trajectory for {ticker} with YoY % Change Annotations",
    xaxis_title="Financial Year",
    yaxis_title="Metric Value",
    hovermode="x unified",
    margin=dict(t=50, b=30, l=30, r=30)
)

st.plotly_chart(fig_trend, use_container_width=True)

st.write("---")
st.subheader("Historical Data Table")
st.dataframe(merged_hist[["year"] + selected_metrics], use_container_width=True, hide_index=True)
