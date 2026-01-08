

import streamlit as st
import os
from datetime import datetime

# Import our UI Modules
import chart_studio
import pipeline_gui

# Import Helper to fetch lists for Sidebar
from modules import data_loader 

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Pro Quant Pair Studio", page_icon="⚡")

# 1. Path where your Adjusted Futures Data lives (For Chart Studio)
BASE_DIR = os.path.join(os.path.dirname(__file__), "adjusted_futures_data_final")

# 2. Path where your Automation Pipeline 'main.py' lives (For Pipeline GUI)
PIPELINE_FILE_PATH = os.path.join(os.path.dirname(__file__), "Automation", "main.py")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["📈 Chart Studio", "⚙️ Data Pipeline"])

st.sidebar.divider()

# --- PAGE ROUTING LOGIC ---

if page == "📈 Chart Studio":
    # ==========================================
    # SIDEBAR CONTROLS FOR CHART STUDIO
    # ==========================================
    st.sidebar.header("1. Select Pair")
    
    # 1. Get Sectors
    sectors = data_loader.get_sectors(BASE_DIR)
    selected_sector = st.sidebar.selectbox("Select Sector", sectors)
    
    stock_a = None
    stock_b = None
    
    # 2. Get Stocks based on Sector
    if selected_sector:
        stocks = data_loader.get_stocks(BASE_DIR, selected_sector)
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            stock_a = st.selectbox("Stock A (Long)", stocks, index=0)
        with col2:
            stock_b = st.selectbox(
                "Stock B (Short)", 
                stocks, 
                index=1 if len(stocks) > 1 else 0
            )
            
    st.sidebar.divider()
    
    # 3. Strategy Parameters
    with st.sidebar.expander("⚙️ Strategy Parameters", expanded=True):
        lookback = st.number_input("Lookback (SMA)", min_value=5, max_value=200, value=20)
        std_dev_mult = st.slider("Std Dev Multiplier", 0.5, 4.0, 2.0, 0.1)
        norm_start_date = st.date_input(
            "Performance Start Date", 
            datetime.strptime("2017-01-01", "%Y-%m-%d")
        )

    # ==========================================
    # RUN CHART STUDIO
    # ==========================================
    # Pass all sidebar inputs to the module
    chart_studio.run(
        BASE_DIR, 
        selected_sector, 
        stock_a, 
        stock_b, 
        lookback, 
        std_dev_mult, 
        norm_start_date
    )

elif page == "⚙️ Data Pipeline":
    # No extra sidebar controls needed for pipeline for now
    pipeline_gui.run(PIPELINE_FILE_PATH)

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.markdown("### 🟢 System Status")
st.sidebar.caption("Engine: Online")