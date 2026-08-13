import sys
import os

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

"""
Annual Reports Repository Screen (08_reports.py)
"""

import streamlit as st
import pandas as pd
from src.dashboard.utils.db import get_companies, get_documents

st.header("📚 Annual Reports Repository & BSE Links")

comp_df = get_companies()
company_options = [f"{r['id']} - {r['company_name']}" for _, r in comp_df.iterrows()]
selected_option = st.selectbox("Search or Select Company Ticker", options=company_options, index=0)

ticker = selected_option.split(" - ")[0].strip()

docs_df = get_documents(ticker=ticker)

st.subheader(f"Annual Report Archive for {ticker}")

if docs_df.empty:
    st.warning("No annual report document links found for this company.")
else:
    for idx, row in docs_df.iterrows():
        yr = row.get("year", "N/A")
        url = row.get("annual_report", "")

        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"### **FY {yr}**")
        with col2:
            if pd.notna(url) and str(url).startswith("http"):
                st.markdown(f"🔗 [Download / View FY {yr} Annual Report PDF]({url})")
            else:
                st.error("Report unavailable")

        st.markdown("---")
