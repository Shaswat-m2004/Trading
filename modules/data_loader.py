


import pandas as pd
import os
import requests
import zipfile
import io
from datetime import datetime, timedelta

# Note: BASE_DIR is removed from here. It will be passed from app.py

# Attempt to locate an optional sector mapping file (Symbol -> Industry)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SECTOR_MAP_FILE = os.path.join(REPO_ROOT, "sector_master_map.csv")

# ==========================================
# 1. HELPER: FETCH ACTIVE LIST FROM NSE
# ==========================================

def fetch_and_store_active_list(base_dir):
    """
    Downloads active list and saves it in the base directory.
    """
    list_file_path = os.path.join(base_dir, "nse_fo_stocks.txt")
    print("🔄 Fetching active F&O list from NSE...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
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
                                    with open(list_file_path, "w") as txt_file:
                                        for stock in active_symbols:
                                            txt_file.write(f"{stock}\n")
                                    return set(active_symbols)
        except Exception as e:
            continue
            
    print("❌ Could not fetch data from NSE. Using local files only.")
    return set()

def get_active_symbols(base_dir):
    """
    Reads the active list from text file in base_dir.
    """
    list_file_path = os.path.join(base_dir, "nse_fo_stocks.txt")
    
    if os.path.exists(list_file_path):
        with open(list_file_path, "r") as f:
            symbols = [line.strip().upper() for line in f.readlines() if line.strip()]
            if symbols:
                return set(symbols)
    
    return fetch_and_store_active_list(base_dir)

# ==========================================
# 2. MAIN DATA LOADING FUNCTIONS
# ==========================================

def _load_sector_map(base_dir):
    """If `sector_master_map.csv` exists in repo, load it and return
    mapping {industry: [symbols]} but only include symbols that exist in base_dir."""
    if not os.path.exists(SECTOR_MAP_FILE):
        return None
    try:
        df = pd.read_csv(SECTOR_MAP_FILE)
        df['Symbol'] = df['Symbol'].astype(str).str.strip().str.upper()
        df['Industry'] = df['Industry'].astype(str).str.strip()

        # Determine available symbols in base_dir
        available = set()
        # If CSVs are in subfolders, search recursively for CSV names
        for root, _, files in os.walk(base_dir):
            for f in files:
                if f.endswith('.csv'):
                    available.add(f.replace('.csv', '').upper())

        sectors = {}
        for _, row in df.iterrows():
            sym = row['Symbol']
            ind = row['Industry']
            if sym in available:
                sectors.setdefault(ind, []).append(sym)

        # Keep only industries with at least one available symbol
        return {k: sorted(v) for k, v in sectors.items() if v}
    except Exception:
        return None


def get_sectors(base_dir):
    """Returns a list of available sector names.

    1) If a sector map CSV exists (Trading/sector_master_map.csv), use it.
    2) Else, if subfolders exist under base_dir, return those folders.
    3) Else fallback to ['ALL'].
    """
    if not os.path.exists(base_dir):
        return []

    # 1) Try sector map
    sector_map = _load_sector_map(base_dir)
    if sector_map:
        return sorted(list(sector_map.keys()))

    # 2) Subfolders
    dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if dirs:
        return sorted(dirs)

    # 3) Fallback
    return ["ALL"]

def get_stocks(base_dir, sector):
    """
    Returns a list of stock symbols in a given sector using base_dir.
    If sector map exists, use it (preferred). Supports pseudo-sector 'ALL'.
    """
    if not os.path.exists(base_dir):
        return []

    # Prefer sector map if available
    sector_map = _load_sector_map(base_dir)
    if sector_map:
        if sector == "ALL":
            # Flatten all symbols present in the map
            all_syms = sorted({s for syms in sector_map.values() for s in syms})
            return all_syms
        return sector_map.get(sector, [])

    # No sector map: fallback to file-system layout
    if sector == "ALL":
        sector_path = base_dir
    else:
        sector_path = os.path.join(base_dir, sector)

    if not os.path.exists(sector_path):
        return []

    local_files = [f.replace('.csv', '').upper() for f in os.listdir(sector_path) if f.endswith('.csv')]
    active_set = get_active_symbols(base_dir)

    if active_set:
        valid_stocks = [s for s in local_files if s in active_set]
        if not valid_stocks:
             return sorted(local_files)
        return sorted(valid_stocks)

    return sorted(local_files)

def load_pair_data(base_dir, sector, stock_a, stock_b):
    """
    Loads futures data for two stocks using base_dir.
    Supports 'ALL' sector where CSVs are directly in base_dir.
    """
    if sector == "ALL":
        path_a = os.path.join(base_dir, f"{stock_a}.csv")
        path_b = os.path.join(base_dir, f"{stock_b}.csv")
    else:
        path_a = os.path.join(base_dir, sector, f"{stock_a}.csv")
        path_b = os.path.join(base_dir, sector, f"{stock_b}.csv")

    def load_front_month(path):
        if not os.path.exists(path): return None
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['TIMESTAMP'])
        df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'])
        df = df[df['EXP_DATE'] >= df['Date']]
        df['expiry_gap'] = (df['EXP_DATE'] - df['Date']).dt.days
        df = df.sort_values(['Date', 'expiry_gap'])
        df = df.groupby('Date').first()
        return df

    try:
        df_a = load_front_month(path_a)
        df_b = load_front_month(path_b)

        if df_a is None or df_b is None: return None

        common_start = max(df_a.index.min(), df_b.index.min())
        df_a = df_a[df_a.index >= common_start]
        df_b = df_b[df_b.index >= common_start]

        merged_df = df_a.join(
            df_b,
            how='inner',
            lsuffix='_A',
            rsuffix='_B'
        )
        return merged_df

    except Exception as e:
        print(f"❌ Error loading pair data: {e}")
        return None