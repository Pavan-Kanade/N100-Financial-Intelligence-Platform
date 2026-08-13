import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Company Profile Screen (02_profile.py)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_bs, get_cf, get_sectors, get_prosandcons

st.header("🏢 Company Financial Profile & Deep Dive")

comp_df = get_companies()
sec_df = get_sectors()

# Company Search Box / Dropdown
company_options = [f"{r['id']} - {r['company_name']}" for _, r in comp_df.iterrows()]
selected_option = st.selectbox("Search or Select Company Ticker", options=company_options, index=0)

ticker = selected_option.split(" - ")[0].strip()

# Retrieve Company Data
comp_match = comp_df[comp_df["id"] == ticker]

if comp_match.empty:
    st.error(f"Ticker '{ticker}' not found - please try another.")
    st.stop()

comp_info = comp_match.iloc[0]
sec_match = sec_df[sec_df["company_id"] == ticker]
sec_info = sec_match.iloc[0] if not sec_match.empty else {"broad_sector": "N/A", "sub_sector": "N/A"}

# 1. Company Profile Header Card
st.markdown(f"""
<div style="background-color: #F1F5F9; padding: 1.2rem; border-radius: 8px; border-left: 6px solid #1F4E78; margin-bottom: 1.5rem;">
    <h2 style="margin: 0; color: #1F4E78;">{comp_info['company_name']} ({ticker})</h2>
    <p style="margin: 0.3rem 0; font-size: 1rem; color: #475569;">
        <b>Sector:</b> {sec_info['broad_sector']} | <b>Industry:</b> {sec_info['sub_sector']} | <b>Face Value:</b> ₹{comp_info.get('face_value', 'N/A')}
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; color: #334155;">
        {comp_info.get('about_company', 'No description available.')}
    </p>
</div>
""", unsafe_allow_html=True)

# Retrieve Ratios & P&L
ratios_df = get_ratios(ticker=ticker)
pl_df = get_pl(ticker=ticker)
pc_df = get_prosandcons(ticker=ticker)

latest_r = ratios_df.iloc[-1] if not ratios_df.empty else {}

# 2. 6 KPI Metric Tiles
c1, c2, c3, c4, c5, c6 = st.columns(6)

roe_v = latest_r.get("return_on_equity_pct")
roce_v = latest_r.get("return_on_capital_employed_pct")
npm_v = latest_r.get("net_profit_margin_pct")
de_v = latest_r.get("debt_to_equity")
cagr_v = latest_r.get("revenue_cagr_5yr")
fcf_v = latest_r.get("free_cash_flow_cr")

c1.metric("ROE", f"{roe_v:.1f}%" if pd.notna(roe_v) else "N/A")
c2.metric("ROCE", f"{roce_v:.1f}%" if pd.notna(roce_v) else "N/A")
c3.metric("Net Margin", f"{npm_v:.1f}%" if pd.notna(npm_v) else "N/A")
c4.metric("D/E Ratio", f"{de_v:.2f}" if pd.notna(de_v) else "N/A")
c5.metric("5Y Rev CAGR", f"{cagr_v:.1f}%" if pd.notna(cagr_v) else "N/A")
c6.metric("FCF (Cr)", f"₹{fcf_v:,.0f}" if pd.notna(fcf_v) else "N/A")

st.write("---")

# 3. Charts Section
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("10-Year Revenue & Net Profit (₹ Cr)")
    if not pl_df.empty:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=pl_df["year"], y=pl_df["sales"], name="Revenue", marker_color="#1F4E78"))
        fig_bar.add_trace(go.Bar(x=pl_df["year"], y=pl_df["net_profit"], name="Net Profit", marker_color="#2CA02C"))
        fig_bar.update_layout(barmode="group", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No P&L history available.")

with col_right:
    st.subheader("10-Year ROE vs ROCE Trajectory (%)")
    if not ratios_df.empty:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=ratios_df["year"], y=ratios_df["return_on_equity_pct"], mode="lines+markers", name="ROE %", line=dict(color="#1F4E78", width=2)))
        fig_line.add_trace(go.Scatter(x=ratios_df["year"], y=ratios_df["return_on_capital_employed_pct"], mode="lines+markers", name="ROCE %", line=dict(color="#FF7F0E", width=2, dash="dash")))
        fig_line.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No ratio history available.")

st.write("---")

# 4. Pros and Cons Badges
st.subheader("Qualitative Investment Insights (Pros & Cons)")
if not pc_df.empty:
    pros_text = pc_df.iloc[0].get("pros", "")
    cons_text = pc_df.iloc[0].get("cons", "")

    p_col, c_col = st.columns(2)
    with p_col:
        st.markdown("#### ✅ Strengths & Pros")
        if pros_text:
            for item in str(pros_text).split("\n"):
                if item.strip():
                    st.success(f"✔️ {item.strip()}")
        else:
            st.info("No explicit pros logged.")

    with c_col:
        st.markdown("#### ❌ Key Risk Factors & Cons")
        if cons_text:
            for item in str(cons_text).split("\n"):
                if item.strip():
                    st.error(f"⚠️ {item.strip()}")
        else:
            st.info("No explicit cons logged.")
else:
    st.info("Qualitative pros & cons not available for this ticker.")
