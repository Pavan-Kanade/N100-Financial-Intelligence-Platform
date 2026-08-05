import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Capital Allocation Map Screen (07_capital.py)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_ratios, get_companies, get_sectors

st.header("🧩 Capital Allocation Framework & Treemap")

ratios_df = get_ratios(year="2023-03")
comp_df = get_companies()
sec_df = get_sectors()

merged = pd.merge(ratios_df, comp_df[["id", "company_name"]].rename(columns={"id": "company_id"}), on="company_id", how="inner")
merged = pd.merge(merged, sec_df, on="company_id", how="left")

merged["capital_allocation_pattern"] = merged["capital_allocation_pattern"].fillna("MODERATE_CAPEX")

st.subheader("Interactive Treemap: 92 Companies Grouped by Capital Allocation Pattern")

pattern_counts = merged.groupby("capital_allocation_pattern")["company_id"].count().reset_index()

fig_tree = px.treemap(
    merged,
    path=["capital_allocation_pattern", "broad_sector", "company_id"],
    values="free_cash_flow_cr",
    color="capital_allocation_pattern",
    hover_name="company_name",
    hover_data=["return_on_equity_pct", "capex_cr", "free_cash_flow_cr"],
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig_tree.update_layout(margin=dict(t=30, b=30, l=30, r=30))

st.plotly_chart(fig_tree, use_container_width=True)

st.write("---")

# Drill-down Selector
st.subheader("Filter Companies by Capital Allocation Pattern")

all_patterns = sorted(merged["capital_allocation_pattern"].unique().tolist())
selected_pattern = st.selectbox("Select Capital Allocation Pattern", options=all_patterns, index=0)

pattern_filtered = merged[merged["capital_allocation_pattern"] == selected_pattern]

st.markdown(f"#### **{len(pattern_filtered)} companies** classified as **{selected_pattern}**")

cols_show = ["company_id", "company_name", "broad_sector", "free_cash_flow_cr", "capex_cr", "capex_intensity_category", "cfo_quality_category"]

st.dataframe(
    pattern_filtered[cols_show].rename(columns={
        "company_id": "Ticker",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "free_cash_flow_cr": "FCF (Cr)",
        "capex_cr": "CapEx (Cr)",
        "capex_intensity_category": "CapEx Intensity",
        "cfo_quality_category": "CFO Quality"
    }),
    use_container_width=True,
    hide_index=True
)
