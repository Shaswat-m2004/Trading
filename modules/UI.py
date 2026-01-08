
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import requests
import zipfile
import io
from datetime import datetime, timedelta

# ================= CONFIGURATION =================
# Default to repository-relative data folder. You can override with env var TRADING_DATA_DIR.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATA_FOLDER = os.environ.get('TRADING_DATA_DIR', os.path.join(REPO_ROOT, 'adjusted_futures_data_final'))
# Store the active list inside the modules folder to avoid polluting working directories
LIST_FILE_PATH = os.path.join(CURRENT_DIR, "nse_fo_stocks.txt")
# =================================================

# Page Setup
st.set_page_config(page_title="Futures Analysis Pro", layout="wide", page_icon="📈")

# Dark Theme CSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stSelectbox, .stRadio, .stMultiSelect { color: black !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600*6) # Cache for 6 hours
def fetch_and_store_active_list():
    """
    Downloads the daily Bhavcopy (ZIP), extracts active FUTSTK symbols,
    and saves them to a text file.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Try today and past 4 days (to handle weekends/holidays)
    for i in range(5):
        date_check = datetime.now() - timedelta(days=i)
        date_str = date_check.strftime("%d%m%Y") # e.g. 24122025
        
        # URL Logic
        url = f"https://nsearchives.nseindia.com/archives/fo/mkt/fo{date_str}.zip"
        expected_csv_name = f"fo{date_str}.csv"
        
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    # Check if the correct CSV is inside
                    if expected_csv_name in z.namelist():
                        with z.open(expected_csv_name) as f:
                            df = pd.read_csv(f)
                            
                            # --- CLEANING ---
                            df.columns = df.columns.str.strip().str.upper()
                            
                            if 'INSTRUMENT' in df.columns and 'SYMBOL' in df.columns:
                                # Clean data rows (strip spaces & uppercase)
                                df['INSTRUMENT'] = df['INSTRUMENT'].astype(str).str.strip().str.upper()
                                df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip().str.upper()
                                
                                # Filter for Futures Stocks
                                active_symbols = sorted(df[df['INSTRUMENT'] == 'FUTSTK']['SYMBOL'].unique())
                                
                                # --- SAVE TO TEXT FILE ---
                                if active_symbols:
                                    with open(LIST_FILE_PATH, "w") as txt_file:
                                        for stock in active_symbols:
                                            txt_file.write(f"{stock}\n")
                                    return active_symbols
        except Exception:
            continue
            
    return []

@st.cache_data
def get_stock_list():
    if not os.path.exists(DATA_FOLDER): return []
    
    # 1. Get all local CSV files
    # Only pick files that end in .csv and are NOT our list file
    local_files = [f.replace('.csv', '') for f in os.listdir(DATA_FOLDER) 
                   if f.endswith('.csv') and f != LIST_FILE_PATH]
    
    # 2. Try to read from the saved Text File first
    active_symbols = []
    if os.path.exists(LIST_FILE_PATH):
        with open(LIST_FILE_PATH, "r") as f:
            active_symbols = [line.strip().upper() for line in f.readlines() if line.strip()]
    
    # 3. If Text File doesn't exist or is empty, try Fetching new data
    if not active_symbols:
        active_symbols = fetch_and_store_active_list()
        
    # 4. Filter: Show only files that are in the Active List
    if active_symbols:
        active_set = set(active_symbols)
        filtered_files = [f for f in local_files if f.upper() in active_set]
        
        if filtered_files:
            return sorted(filtered_files)
    
    # Fallback: If everything fails, show all local files
    return sorted(local_files)

@st.cache_data
def load_stock_data(symbol):
    file_path = os.path.join(DATA_FOLDER, f"{symbol}.csv")
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
    # FIXED: No more SettingWithCopyWarning
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

def plot_chart(df, title, rollover_dates=None):
    all_dates = pd.date_range(start=df['TIMESTAMP'].min(), end=df['TIMESTAMP'].max())
    dt_breaks = all_dates.difference(df['TIMESTAMP']).strftime("%Y-%m-%d").tolist()

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f'Price Action', 'Volume', 'Open Interest')
    )

    fig.add_trace(go.Candlestick(
        x=df['TIMESTAMP'], open=df['OPEN_PRICE'], high=df['HI_PRICE'],
        low=df['LO_PRICE'], close=df['CLOSE_PRICE'], name='OHLC'
    ), row=1, col=1)

    if rollover_dates:
        for date in rollover_dates:
            fig.add_vline(x=date, line_width=1, line_dash="dash", line_color="rgba(255, 255, 0, 0.5)", row=1, col=1)

    colors = ['#00FF80' if row['CLOSE_PRICE'] >= row['OPEN_PRICE'] else '#FF4136' for i, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df['TIMESTAMP'], y=df['NO_OF_CONT'], name='Volume', marker_color=colors), row=2, col=1)

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

def main():
    st.title("📈 Harmonized Futures Dashboard")
    
    with st.sidebar:
        st.header("Configuration")
        
        # --- Check Status of Active List ---
        if os.path.exists(LIST_FILE_PATH):
            last_mod = datetime.fromtimestamp(os.path.getmtime(LIST_FILE_PATH)).strftime('%Y-%m-%d')
            st.success(f"✅ Active List Loaded\n(Updated: {last_mod})")
            
            # Button to force refresh
            if st.button("🔄 Force Update List"):
                st.cache_data.clear() # Clear Streamlit cache
                fetch_and_store_active_list() # Fetch new
                st.rerun() # Refresh page
        else:
            st.warning("⚠️ No Active List found.\nFetching now...")
            
        stock_list = get_stock_list()
        st.caption(f"Showing {len(stock_list)} Listed Stocks")

    if not stock_list:
        st.error(f"No active stock data found in {DATA_FOLDER}")
        return

    selected_stock = st.sidebar.selectbox("Select Asset", stock_list)

    if selected_stock:
        df = load_stock_data(selected_stock)
        
        if df is not None:
            view_mode = st.sidebar.radio("View Mode", ["Continuous Futures", "Specific Contract Expiry"])

            if view_mode == "Continuous Futures":
                col1, col2 = st.columns(2)
                with col1:
                    period = st.selectbox("Time Range", ["6 Months", "1 Year", "3 Years", "All Time"], index=1)
                with col2:
                    ctype = st.selectbox("Contract", ["Near Month (Current)", "Next Month", "Far Month"])
                
                rank = {"Near Month (Current)": 0, "Next Month": 1, "Far Month": 2}[ctype]
                cont_df = get_continuous_data(df, rank)
                chart_df = filter_data_by_period(cont_df, period)
                
                if not chart_df.empty:
                    rollovers = get_rollover_dates(chart_df)
                    plot_chart(chart_df, f"{selected_stock} - {ctype} Continuous", rollovers)
                else:
                    st.warning("Not enough data.")

            else:
                avail_exp = sorted(df['EXP_DATE'].dropna().unique())
                exp_opts = [pd.Timestamp(dt).strftime('%d-%b-%Y') for dt in avail_exp]
                sel_exp_str = st.sidebar.selectbox("Select Expiry", exp_opts)
                
                if sel_exp_str:
                    sel_dt = avail_exp[exp_opts.index(sel_exp_str)]
                    chart_df = df[df['EXP_DATE'] == sel_dt].sort_values('TIMESTAMP')
                    if not chart_df.empty:
                        plot_chart(chart_df, f"{selected_stock} - Expiry: {sel_exp_str}")
                    else:
                        st.warning("No data.")

if __name__ == "__main__":
    main()