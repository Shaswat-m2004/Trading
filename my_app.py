import streamlit as st
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import zipfile
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import our UI Modules
import chart_studio
import pipeline_gui
# Import Helper to fetch lists for Sidebar
from modules import data_loader 

# --- CONFIGURATION (Must be the first Streamlit command) ---
st.set_page_config(layout="wide", page_title="Pro Quant Pair Studio", page_icon="⚡")

# --- GLOBAL STYLING (Dark Theme from Futures Pro) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stSelectbox, .stRadio, .stMultiSelect { color: black !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 📂 PATH CONFIGURATIONS
# ==========================================

# 1. Path for Chart Studio (Sector Wise Data)
BASE_DIR = os.path.join(os.path.dirname(__file__), "sec_wise_futures_data")

# 2. Path for Automation Pipeline
PIPELINE_FILE_PATH = os.path.join(os.path.dirname(__file__), "Automation", "main.py")

# 3. Paths for Futures Dashboard (New Section)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assuming 'adjusted_futures_data_final' is in the root directory alongside this script
FUTURES_DATA_FOLDER = os.path.join(CURRENT_DIR, 'adjusted_futures_data_final')
LIST_FILE_PATH = os.path.join(CURRENT_DIR, "nse_fo_stocks.txt")

# ==========================================
# 🧠 HELPER FUNCTIONS FOR FUTURES DASHBOARD
# ==========================================

@st.cache_data(ttl=3600*6)
def fetch_and_store_active_list():
    """Downloads Bhavcopy, extracts active FUTSTK symbols, saves to txt."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    for i in range(5):
        date_check = datetime.now() - timedelta(days=i)
        date_str = date_check.strftime("%d%m%Y")
        url = f"https://nsearchives.nseindia.com/archives/fo/mkt/fo{date_str}.zip"
        expected_csv_name = f"fo{date_str}.csv"
        
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    if expected_csv_name in z.namelist():
                        with z.open(expected_csv_name) as f:
                            df = pd.read_csv(f)
                            df.columns = df.columns.str.strip().str.upper()
                            if 'INSTRUMENT' in df.columns and 'SYMBOL' in df.columns:
                                df['INSTRUMENT'] = df['INSTRUMENT'].astype(str).str.strip().str.upper()
                                df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip().str.upper()
                                active_symbols = sorted(df[df['INSTRUMENT'] == 'FUTSTK']['SYMBOL'].unique())
                                if active_symbols:
                                    with open(LIST_FILE_PATH, "w") as txt_file:
                                        for stock in active_symbols:
                                            txt_file.write(f"{stock}\n")
                                    return active_symbols
        except Exception:
            continue
    return []

@st.cache_data
def get_stock_list_futures():
    """Gets list of stocks for the Futures Dashboard."""
    if not os.path.exists(FUTURES_DATA_FOLDER): return []
    local_files = [f.replace('.csv', '') for f in os.listdir(FUTURES_DATA_FOLDER) 
                   if f.endswith('.csv') and f != LIST_FILE_PATH]
    
    active_symbols = []
    if os.path.exists(LIST_FILE_PATH):
        with open(LIST_FILE_PATH, "r") as f:
            active_symbols = [line.strip().upper() for line in f.readlines() if line.strip()]
    
    if not active_symbols:
        active_symbols = fetch_and_store_active_list()
        
    if active_symbols:
        active_set = set(active_symbols)
        filtered_files = [f for f in local_files if f.upper() in active_set]
        if filtered_files: return sorted(filtered_files)
    
    return sorted(local_files)

@st.cache_data
def load_single_stock_data(symbol):
    """Loads CSV for a single stock."""
    file_path = os.path.join(FUTURES_DATA_FOLDER, f"{symbol}.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip().str.upper()
        df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'])
        try:
            df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'], dayfirst=True, errors='coerce')
        except:
            df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'], format='mixed', dayfirst=True)
        return df
    return None

def get_continuous_data(df, contract_rank=0):
    df_sorted = df.sort_values(by=['TIMESTAMP', 'EXP_DATE'])
    def pick_rank(group):
        if len(group) > contract_rank: return group.iloc[contract_rank]
        else: return group.iloc[-1]
    return df_sorted.groupby('TIMESTAMP').apply(pick_rank, include_groups=False).reset_index(drop=False)

def get_rollover_dates(df):
    prev_exp = df['EXP_DATE'].shift(1)
    rollover_mask = (df['EXP_DATE'] != prev_exp) & (prev_exp.notnull())
    return df.loc[rollover_mask, 'TIMESTAMP'].tolist()

def filter_data_by_period(df, period):
    if df.empty: return df
    last_date = df['TIMESTAMP'].max()
    if period == "6 Months": start = last_date - pd.DateOffset(months=6)
    elif period == "1 Year": start = last_date - pd.DateOffset(years=1)
    elif period == "3 Years": start = last_date - pd.DateOffset(years=3)
    else: return df
    return df[df['TIMESTAMP'] >= start]

def plot_futures_chart(df, title, rollover_dates=None):
    all_dates = pd.date_range(start=df['TIMESTAMP'].min(), end=df['TIMESTAMP'].max())
    dt_breaks = all_dates.difference(df['TIMESTAMP']).strftime("%Y-%m-%d").tolist()

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f'Price Action', 'Volume', 'Open Interest')
    )
    # Price
    fig.add_trace(go.Candlestick(
        x=df['TIMESTAMP'], open=df['OPEN_PRICE'], high=df['HI_PRICE'],
        low=df['LO_PRICE'], close=df['CLOSE_PRICE'], name='OHLC'
    ), row=1, col=1)

    # Rollover Lines
    if rollover_dates:
        for date in rollover_dates:
            fig.add_vline(x=date, line_width=1, line_dash="dash", line_color="rgba(255, 255, 0, 0.5)", row=1, col=1)

    # Volume
    colors = ['#00FF80' if row['CLOSE_PRICE'] >= row['OPEN_PRICE'] else '#FF4136' for i, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df['TIMESTAMP'], y=df['NO_OF_CONT'], name='Volume', marker_color=colors), row=2, col=1)

    # OI
    oi_col = next((c for c in df.columns if 'OPEN_INT' in c), None)
    if oi_col:
        fig.add_trace(go.Bar(x=df['TIMESTAMP'], y=df[oi_col], name='Open Interest', marker_color='#636EFA'), row=3, col=1)

    fig.update_layout(
        template='plotly_dark', height=800, xaxis_rangeslider_visible=False,
        hovermode='x unified', paper_bgcolor='#0E1117', plot_bgcolor='#0E1117',
        title_text=title, margin=dict(l=50, r=50, t=50, b=50)
    )
    fig.update_xaxes(rangebreaks=[dict(values=dt_breaks)], showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 🚀 MAIN PAGE LOGIC
# ==========================================

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["📈 Chart Studio", "⚙️ Data Pipeline", "📊 Futures Dashboard"])

st.sidebar.divider()

# --- 1. CHART STUDIO (Existing) ---
if page == "📈 Chart Studio":
    st.sidebar.header("1. Select Pair")
    
    # 1. Get Sectors
    sectors = data_loader.get_sectors(BASE_DIR)
    selected_sector = st.sidebar.selectbox("Select Sector", sectors)
    
    stock_a, stock_b = None, None
    
    # 2. Get Stocks based on Sector
    if selected_sector:
        stocks = data_loader.get_stocks(BASE_DIR, selected_sector)
        col1, col2 = st.sidebar.columns(2)
        with col1:
            stock_a = st.selectbox("Stock A (Long)", stocks, index=0)
        with col2:
            stock_b = st.selectbox("Stock B (Short)", stocks, index=1 if len(stocks) > 1 else 0)
            
    st.sidebar.divider()
    
    # 3. Strategy Parameters
    with st.sidebar.expander("⚙️ Strategy Parameters", expanded=True):
        lookback = st.number_input("Lookback (SMA)", min_value=5, max_value=200, value=20)
        std_dev_mult = st.slider("Std Dev Multiplier", 0.5, 4.0, 2.0, 0.1)
        norm_start_date = st.date_input("Performance Start Date", datetime.strptime("2017-01-01", "%Y-%m-%d"))

    # Run Module
    chart_studio.run(BASE_DIR, selected_sector, stock_a, stock_b, lookback, std_dev_mult, norm_start_date)

# --- 2. DATA PIPELINE (Existing) ---
elif page == "⚙️ Data Pipeline":
    pipeline_gui.run(PIPELINE_FILE_PATH)

# --- 3. FUTURES DASHBOARD (New Section) ---
elif page == "📊 Futures Dashboard":
    st.title("📈 Harmonized Futures Dashboard")
    
    # Futures Specific Sidebar
    st.sidebar.header("Configuration")
    
    # Check Active List
    if os.path.exists(LIST_FILE_PATH):
        last_mod = datetime.fromtimestamp(os.path.getmtime(LIST_FILE_PATH)).strftime('%Y-%m-%d')
        st.sidebar.success(f"✅ Active List Loaded\n(Updated: {last_mod})")
        if st.sidebar.button("🔄 Force Update List"):
            st.cache_data.clear()
            fetch_and_store_active_list()
            st.rerun()
    else:
        st.sidebar.warning("⚠️ No Active List found. Fetching now...")
    
    stock_list = get_stock_list_futures()
    st.sidebar.caption(f"Showing {len(stock_list)} Listed Stocks")

    if not stock_list:
        st.error(f"No active stock data found in {FUTURES_DATA_FOLDER}")
    else:
        selected_stock = st.sidebar.selectbox("Select Asset", stock_list)

        if selected_stock:
            df = load_single_stock_data(selected_stock)
            
            if df is not None:
                view_mode = st.sidebar.radio("View Mode", ["Continuous Futures", "Specific Contract Expiry"])

                if view_mode == "Continuous Futures":
                    c1, c2 = st.columns(2)
                    with c1:
                        period = st.selectbox("Time Range", ["6 Months", "1 Year", "3 Years", "All Time"], index=1)
                    with c2:
                        ctype = st.selectbox("Contract", ["Near Month (Current)", "Next Month", "Far Month"])
                    
                    rank = {"Near Month (Current)": 0, "Next Month": 1, "Far Month": 2}[ctype]
                    cont_df = get_continuous_data(df, rank)
                    chart_df = filter_data_by_period(cont_df, period)
                    
                    if not chart_df.empty:
                        rollovers = get_rollover_dates(chart_df)
                        plot_futures_chart(chart_df, f"{selected_stock} - {ctype} Continuous", rollovers)
                    else:
                        st.warning("Not enough data.")

                else: # Specific Expiry
                    avail_exp = sorted(df['EXP_DATE'].dropna().unique())
                    exp_opts = [pd.Timestamp(dt).strftime('%d-%b-%Y') for dt in avail_exp]
                    sel_exp_str = st.sidebar.selectbox("Select Expiry", exp_opts)
                    
                    if sel_exp_str:
                        sel_dt = avail_exp[exp_opts.index(sel_exp_str)]
                        chart_df = df[df['EXP_DATE'] == sel_dt].sort_values('TIMESTAMP')
                        if not chart_df.empty:
                            plot_futures_chart(chart_df, f"{selected_stock} - Expiry: {sel_exp_str}")
                        else:
                            st.warning("No data.")

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.markdown("### 🟢 System Status")
st.sidebar.caption("Engine: Online")