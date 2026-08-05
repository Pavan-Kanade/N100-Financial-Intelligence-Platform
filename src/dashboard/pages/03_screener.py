import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Financial Stock Screener Screen (03_screener.py)
"""

import streamlit as st
import pandas as pd
from src.screener.engine import ScreenerEngine

st.header("🔍 Interactive Financial Stock Screener")

engine = ScreenerEngine()
preset_configs = engine.config.get("presets", {})

st.sidebar.subheader("Filter Controls")

# Preset Selector Buttons
st.markdown("#### Preset Templates")
p_cols = st.columns(3)

if p_cols[0].button("Quality Compounder"):
    st.session_state["roe_min"] = 15.0
    st.session_state["de_max"] = 1.0
    st.session_state["fcf_min"] = 0.0
    st.session_state["rev_cagr_min"] = 10.0

if p_cols[1].button("Value Pick"):
    st.session_state["pe_max"] = 30.0
    st.session_state["pb_max"] = 4.0
    st.session_state["de_max"] = 2.0
    st.session_state["div_min"] = 0.5

if p_cols[2].button("Growth Accelerator"):
    st.session_state["pat_cagr_min"] = 20.0
    st.session_state["rev_cagr_min"] = 15.0
    st.session_state["de_max"] = 2.0

p_cols2 = st.columns(3)
if p_cols2[0].button("Dividend Champion"):
    st.session_state["div_min"] = 2.0
    st.session_state["fcf_min"] = 0.0

if p_cols2[1].button("Debt-Free Blue Chip"):
    st.session_state["de_max"] = 0.1
    st.session_state["roe_min"] = 12.0

if p_cols2[2].button("Turnaround Watch"):
    st.session_state["rev_cagr_min"] = 10.0
    st.session_state["fcf_min"] = 0.0

st.write("---")

# Sliders in Sidebar
st.sidebar.markdown("### Metric Threshold Sliders")

roe_min = st.sidebar.slider("Minimum ROE (%)", 0.0, 50.0, float(st.session_state.get("roe_min", 0.0)))
de_max = st.sidebar.slider("Maximum D/E Ratio", 0.0, 10.0, float(st.session_state.get("de_max", 10.0)))
fcf_min = st.sidebar.slider("Minimum FCF (₹ Cr)", -1000.0, 20000.0, float(st.session_state.get("fcf_min", -1000.0)))
rev_cagr_min = st.sidebar.slider("Minimum 5Y Rev CAGR (%)", -10.0, 50.0, float(st.session_state.get("rev_cagr_min", -10.0)))
pat_cagr_min = st.sidebar.slider("Minimum 5Y PAT CAGR (%)", -10.0, 50.0, float(st.session_state.get("pat_cagr_min", -10.0)))
opm_min = st.sidebar.slider("Minimum OPM (%)", 0.0, 60.0, 0.0)
pe_max = st.sidebar.slider("Maximum P/E Ratio", 0.0, 150.0, float(st.session_state.get("pe_max", 150.0)))
pb_max = st.sidebar.slider("Maximum P/B Ratio", 0.0, 40.0, float(st.session_state.get("pb_max", 40.0)))
div_min = st.sidebar.slider("Minimum Dividend Yield (%)", 0.0, 10.0, float(st.session_state.get("div_min", 0.0)))
icr_min = st.sidebar.slider("Minimum Interest Coverage (ICR)", 0.0, 50.0, 0.0)

filters = {
    "return_on_equity_pct": {"min": roe_min},
    "debt_to_equity": {"max": de_max},
    "free_cash_flow_cr": {"min": fcf_min},
    "revenue_cagr_5yr": {"min": rev_cagr_min},
    "pat_cagr_5yr": {"min": pat_cagr_min},
    "operating_profit_margin_pct": {"min": opm_min},
    "pe_ratio": {"max": pe_max},
    "pb_ratio": {"max": pb_max},
    "dividend_yield_pct": {"min": div_min},
    "interest_coverage": {"min": icr_min}
}

base_df = engine.get_merged_dataset("2023-03")
filtered_df = engine.apply_filters(base_df, filters)

# Result Count Label
st.markdown(f"### 📋 **{len(filtered_df)} companies** match your filter criteria")

if not filtered_df.empty:
    cols_display = [
        "company_id", "company_name", "broad_sector", "composite_quality_score",
        "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
        "revenue_cagr_5yr", "pat_cagr_5yr", "pe_ratio", "pb_ratio", "dividend_yield_pct"
    ]
    valid_cols = [c for c in cols_display if c in filtered_df.columns]
    
    df_show = filtered_df[valid_cols].copy()
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # CSV Download Button
    csv_bytes = df_show.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Screener Results as CSV",
        data=csv_bytes,
        file_name="screener_results.csv",
        mime="text/csv"
    )
else:
    st.warning("No companies match the current filter combinations. Try loosening the slider constraints.")
