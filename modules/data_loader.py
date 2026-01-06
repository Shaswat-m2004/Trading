

# import pandas as pd
# import os
# import requests
# import zipfile
# import io
# from datetime import datetime, timedelta

# # --- UPDATE THIS PATH ---
# BASE_DIR = r"C:\Users\91702\Documents\programming\Trading_Data_Transformation\step3_fo_to_fo_pair\data\sector_wise_stocks"

# # File to store the active list (saved in the same folder as this script)
# LIST_FILE_PATH = "nse_fo_stocks.txt"

# # ==========================================
# # 1. HELPER: FETCH ACTIVE LIST FROM NSE
# # ==========================================
# def fetch_and_store_active_list():
#     """
#     Downloads the daily Bhavcopy (ZIP) from NSE, extracts active FUTSTK symbols,
#     and saves them to a text file.
#     Handles Holidays: Checks today, then goes back up to 5 days if data is missing.
#     """
#     print("🔄 Fetching active F&O list from NSE...")
    
#     # Headers zaruri hain taaki NSE humein bot na samjhe
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#     }
    
#     # Try today and past 4 days (to handle weekends/holidays)
#     for i in range(5):
#         date_check = datetime.now() - timedelta(days=i)
#         date_str = date_check.strftime("%d%m%Y") # Format: 28122025
        
#         # URL Logic
#         url = f"https://nsearchives.nseindia.com/archives/fo/mkt/fo{date_str}.zip"
#         expected_csv_name = f"fo{date_str}.csv"
        
#         try:
#             # Request bhejo
#             r = requests.get(url, headers=headers, timeout=10)
            
#             if r.status_code == 200:
#                 print(f"✅ Data found for date: {date_str}")
                
#                 # Zip file ko memory mein open kro
#                 with zipfile.ZipFile(io.BytesIO(r.content)) as z:
#                     if expected_csv_name in z.namelist():
#                         with z.open(expected_csv_name) as f:
#                             df = pd.read_csv(f)
                            
#                             # --- CLEANING ---
#                             df.columns = df.columns.str.strip().str.upper()
                            
#                             if 'INSTRUMENT' in df.columns and 'SYMBOL' in df.columns:
#                                 df['INSTRUMENT'] = df['INSTRUMENT'].astype(str).str.strip().str.upper()
#                                 df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip().str.upper()
                                
#                                 # Sirf 'FUTSTK' wale symbols filter kro
#                                 active_symbols = sorted(df[df['INSTRUMENT'] == 'FUTSTK']['SYMBOL'].unique())
                                
#                                 # --- SAVE TO TEXT FILE ---
#                                 if active_symbols:
#                                     with open(LIST_FILE_PATH, "w") as txt_file:
#                                         for stock in active_symbols:
#                                             txt_file.write(f"{stock}\n")
                                    
#                                     print(f"✅ Active list updated with {len(active_symbols)} stocks.")
#                                     return set(active_symbols)
#             else:
#                 print(f"⚠️ Market closed or data missing for {date_str}. Checking previous day...")

#         except Exception as e:
#             print(f"⚠️ Error checking date {date_str}: {e}")
#             continue
            
#     print("❌ Could not fetch data from NSE (Tried last 5 days). Using local files only.")
#     return set()

# def get_active_symbols():
#     """
#     Reads the active list from text file. If missing, fetches from NSE.
#     """
#     # 1. Pehle check kro file already hai kya
#     if os.path.exists(LIST_FILE_PATH):
#         # Optional: Aap chaho to check kr sakte ho file purani to nahi hai
#         # Abhi ke liye hum assume krte hain file sahi hai
#         with open(LIST_FILE_PATH, "r") as f:
#             symbols = [line.strip().upper() for line in f.readlines() if line.strip()]
#             if symbols:
#                 return set(symbols)
    
#     # 2. Agar file nahi hai, to NSE se fetch kro
#     return fetch_and_store_active_list()

# # ==========================================
# # 2. MAIN DATA LOADING FUNCTIONS
# # ==========================================

# def get_sectors():
#     """Returns a list of available sector folders."""
#     if not os.path.exists(BASE_DIR):
#         return []
#     return [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]

# def get_stocks(sector):
#     """
#     Returns a list of stock symbols in a given sector.
#     FILTERS: Only returns stocks that are currently active in NSE Futures.
#     """
#     sector_path = os.path.join(BASE_DIR, sector)
#     if not os.path.exists(sector_path):
#         return []
    
#     # 1. Local Folder mein jo CSV files hain unhe list kro
#     local_files = [f.replace('.csv', '').upper() for f in os.listdir(sector_path) if f.endswith('.csv')]
    
#     # 2. NSE Active List Mangvao
#     active_set = get_active_symbols()
    
#     # 3. Intersection Logic (Jo stock Local bhi hai AUR Active bhi hai)
#     if active_set:
#         valid_stocks = [s for s in local_files if s in active_set]
        
#         # Fallback: Agar NSE list empty aayi (Internet issue), toh saare local files dikha do
#         if not valid_stocks and not active_set:
#              return sorted(local_files)
             
#         return sorted(valid_stocks)
    
#     # Agar fetch fail ho gaya to sab dikha do
#     return sorted(local_files)



# def load_pair_data(sector, stock_a, stock_b):
#     """a
#     Loads futures data for two stocks.
#     - Keeps proxy rows (0 volume, 0 OI allowed)
#     - Selects ONE contract per day (nearest expiry)
#     - Aligns full common history
#     """

#     path_a = os.path.join(BASE_DIR, sector, f"{stock_a}.csv")
#     path_b = os.path.join(BASE_DIR, sector, f"{stock_b}.csv")

#     def load_front_month(path):
#         df = pd.read_csv(path)

#         # --- Parse dates ---
#         df['Date'] = pd.to_datetime(df['TIMESTAMP'])
#         df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'])

#         # --- Keep valid contracts only ---
#         df = df[df['EXP_DATE'] >= df['Date']]

#         # --- Pick nearest expiry per day (NO averaging) ---
#         df['expiry_gap'] = (df['EXP_DATE'] - df['Date']).dt.days
#         df = df.sort_values(['Date', 'expiry_gap'])
#         df = df.groupby('Date').first()

#         # print(df.head())
#         check = df[pd.to_datetime(df['TIMESTAMP'])>=pd.to_datetime("2021-01-01")]

#         print("Data Check Post 2021-01-01:")
#         print(check.head())

#         return df

#     try:
#         # ===== LOAD BOTH STOCKS =====
#         df_a = load_front_month(path_a)
#         df_b = load_front_month(path_b)

#         # ===== ALIGN START DATE =====
#         common_start = max(df_a.index.min(), df_b.index.min())
#         df_a = df_a[df_a.index >= common_start]
#         df_b = df_b[df_b.index >= common_start]

#         # ===== MERGE (INNER = TRUE OVERLAP ONLY) =====
#         merged_df = df_a.join(
#             df_b,
#             how='inner',
#             lsuffix='_A',
#             rsuffix='_B'
#         )
#         print(merged_df['CLOSE_PRICE_A'].head())
#         print("-"*40)
#         print(merged_df['CLOSE_PRICE_B'].head())
#         return merged_df

#     except Exception as e:
#         print(f"❌ Error loading pair data ({stock_a}, {stock_b}): {e}")
#         return None


import pandas as pd
import os
import requests
import zipfile
import io
from datetime import datetime, timedelta

# Note: BASE_DIR is removed from here. It will be passed from app.py

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

def get_sectors(base_dir):
    """Returns a list of available sector folders."""
    if not os.path.exists(base_dir):
        return []
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

def get_stocks(base_dir, sector):
    """
    Returns a list of stock symbols in a given sector using base_dir.
    """
    sector_path = os.path.join(base_dir, sector)
    if not os.path.exists(sector_path):
        return []
    
    local_files = [f.replace('.csv', '').upper() for f in os.listdir(sector_path) if f.endswith('.csv')]
    active_set = get_active_symbols(base_dir)
    
    if active_set:
        valid_stocks = [s for s in local_files if s in active_set]
        if not valid_stocks and not active_set:
             return sorted(local_files)
        return sorted(valid_stocks)
    
    return sorted(local_files)

def load_pair_data(base_dir, sector, stock_a, stock_b):
    """
    Loads futures data for two stocks using base_dir.
    """
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