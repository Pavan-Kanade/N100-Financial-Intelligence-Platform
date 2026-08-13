import sys
import os
sys.path.insert(0, '.')
"""
Main Streamlit Application Entry Point for Nifty 100 Financial Intelligence Platform.
"""

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F4E78;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #595959;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #1F4E78;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📈 Nifty 100 Analytics")
st.sidebar.markdown("---")
st.sidebar.info("Use the sidebar menu to navigate between the 8 analytics screens.")

st.title("Welcome to Nifty 100 Financial Intelligence Platform")
st.markdown("### Select a screen from the sidebar menu to begin analysis.")
st.write("---")

st.markdown("""
### Available Modules:
- **01 Home**: Overview KPI tiles, sector breakdown, top quality stocks.
- **02 Company Profile**: Comprehensive 10-year financials, cards, and pros/cons.
- **03 Financial Screener**: Live multi-criteria stock filter & preset templates.
- **04 Peer Comparison**: Intra-group percentile rankings & radar charts.
- **05 Trend Analysis**: 10-year metric trajectory & YoY annotations.
- **06 Sector Analysis**: Revenue vs ROE bubble chart & sector medians.
- **07 Capital Allocation Map**: 8-pattern capital allocation treemap.
- **08 Annual Reports Repository**: BSE annual report PDF links & availability.
""")
