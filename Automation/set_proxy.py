
# import pandas as pd
# import os
# import glob
# from tqdm import tqdm

# # ================= CONFIGURATION =================

# FUTURES_FOLDER = r"C:\Users\91702\Documents\programming\all_cash_stocks\adjusted_futures_data_final"
# CASH_FOLDER    = r"C:\Users\91702\Documents\programming\all_cash_stocks\stock_wise"
# NIFTY_FILE     = os.path.join(FUTURES_FOLDER, "NIFTY.csv")

# # ================= HELPERS =================

# def load_cash(symbol):
#     """Loads and cleans Cash/Equity Data"""
#     path = os.path.join(CASH_FOLDER, f"{symbol}.csv")
#     if not os.path.exists(path): return None
    
#     try:
#         df = pd.read_csv(path)
#         df.columns = df.columns.str.strip().str.title()
        
#         # Smart Date Detection
#         date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp']), None)
#         if not date_col: return None
        
#         df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
#         df = df.dropna(subset=['Date'])
        
#         # Remove duplicates, keeping the last update
#         df = df.drop_duplicates(subset=['Date'], keep='last')
#         return df.set_index('Date').sort_index()
#     except Exception:
#         return None

# def load_nifty():
#     """Loads Nifty Data to act as the Master Timeline"""
#     df = pd.read_csv(NIFTY_FILE)
#     df.columns = df.columns.str.strip().str.upper()
#     df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'])
#     df['EXP_DATE']  = pd.to_datetime(df['EXP_DATE'], dayfirst=True, errors='coerce')
#     return df.sort_values(['TIMESTAMP', 'EXP_DATE'])

# def build_master_calendar(nifty_df):
#     """Returns unique sorted list of all trading days"""
#     return sorted(nifty_df['TIMESTAMP'].dropna().unique())

# def build_expiry_map(nifty_df):
#     """Returns Dictionary: { Date -> [List of Active Expiries (Near, Next, Far)] }"""
#     exp_map = {}
#     for d, g in nifty_df.groupby('TIMESTAMP'):
#         active_exps = sorted([x for x in g['EXP_DATE'] if pd.notnull(x)])
#         exp_map[d] = active_exps
#     return exp_map

# # ================= MAIN LOGIC =================

# def harmonize_futures_safely():
    
#     print("⏳ Loading Nifty Master Timeline...")
#     nifty_df = load_nifty()
#     master_dates = build_master_calendar(nifty_df)
#     expiry_map   = build_expiry_map(nifty_df)

#     files = glob.glob(os.path.join(FUTURES_FOLDER, "*.csv"))
#     print(f"🚀 Harmonizing {len(files)} futures files with 'Smart Gap Fill'...")

#     for file in tqdm(files):
#         symbol = os.path.basename(file).replace(".csv", "")
#         if symbol.upper() == "NIFTY": continue

#         # 1. Load Existing Futures
#         try:
#             df_fut = pd.read_csv(file)
#             df_fut.columns = df_fut.columns.str.strip().str.upper()
#             df_fut['TIMESTAMP'] = pd.to_datetime(df_fut['TIMESTAMP'])
#             df_fut['EXP_DATE'] = pd.to_datetime(df_fut['EXP_DATE'], errors='coerce')
            
#             # Clean "Ghost" rows where Expiry is missing
#             df_fut = df_fut.dropna(subset=['EXP_DATE'])
            
#         except Exception as e:
#             print(f"❌ Corrupt Futures File {symbol}: {e}")
#             continue
        
#         # 2. Load Cash Data
#         cash = load_cash(symbol)
#         if cash is None: continue 

#         # Quick lookup for existing data to speed up the loop
#         existing_data = set(zip(df_fut['TIMESTAMP'], df_fut['EXP_DATE']))
        
#         new_rows = []
#         df_fut = df_fut.sort_values('TIMESTAMP')

#         # 3. Iterate Over EVERY Nifty Trading Day
#         for dt in master_dates:
            
#             # If Stock Cash didn't trade today, skip
#             if dt not in cash.index: continue

#             # Get the Active Expiries for today (from Nifty's Homework)
#             todays_expiries = expiry_map.get(dt, [])
#             if not todays_expiries: continue

#             cash_row = cash.loc[dt]

#             # CHECK ALL 3 EXPIRIES
#             for exp in todays_expiries:
#                 key = (dt, exp)
                
#                 # If Real Data exists, hands off!
#                 if key in existing_data:
#                     continue 
                
#                 # --- SYNTHETIC PROXY LOGIC ---
                
#                 # Find the most recent previous future for THIS specific expiry
#                 prev_fut = df_fut[
#                     (df_fut['EXP_DATE'] == exp) & 
#                     (df_fut['TIMESTAMP'] < dt)
#                 ]
                
#                 base_price = 0.0
                
#                 if prev_fut.empty:
#                     # CASE: Phase 1 or 3 (No history for this expiry)
#                     # Use Cash Price (Basis = 0)
#                     base_price = cash_row['Close']
                
#                 else:
#                     # CASE: Phase 2 (Active Gap) - The Fix is Here 🛠️
#                     prev_close = prev_fut.iloc[-1]['CLOSE_PRICE']
#                     last_fut_date = prev_fut.iloc[-1]['TIMESTAMP']
                    
                   
#                     if last_fut_date in cash.index:
#                         prev_cash_price = cash.loc[last_fut_date]['Close']
                        
#                         # 2. Calculate the TRUE Delta (Market move over the gap)
#                         delta = cash_row['Close'] - prev_cash_price
                        
#                         # 3. Apply Delta to preserve the Basis
#                         base_price = prev_close + delta
#                     else:
#                         # Fallback if Cash was missing on that old date
#                         base_price = cash_row['Close']

#                 # Create the Synthetic Row
#                 new_row = {
#                     'TIMESTAMP': dt,
#                     'SYMBOL': symbol,
#                     'EXP_DATE': exp,
#                     # Simulating OHLC using Cash Volatility
#                     'OPEN_PRICE': round(base_price + (cash_row['Open'] - cash_row['Close']), 2),
#                     'HI_PRICE':   round(base_price + (cash_row['High'] - cash_row['Close']), 2),
#                     'LO_PRICE':   round(base_price + (cash_row['Low']  - cash_row['Close']), 2),
#                     'CLOSE_PRICE': round(base_price, 2),
#                     # Flags: Zero Volume = Synthetic
#                     'TRD_QTY': 0, 'OPEN_INT': 0, 'NO_OF_CONT': 0, 'TRD_VAL': 0
#                 }

#                 if new_row['LO_PRICE'] <= 0: new_row['LO_PRICE'] = 0.05
#                 new_rows.append(new_row)

#         if new_rows:

#             df_final = pd.concat([df_fut, pd.DataFrame(new_rows)], ignore_index=True)
#             df_final = df_final.sort_values(['TIMESTAMP', 'EXP_DATE'])
            
#             # Atomic Save
#             df_final.to_csv(file, index=False)

#     print("✅ All gaps filled. Your data is now continuous and faithful.")

# if __name__ == "__main__":
#     harmonize_futures_safely()




import pandas as pd
import numpy as np
import os
import glob
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from functools import partial

# ================= CONFIGURATION =================

# Repository-relative folders (assumes this file lives in Trading/Automation)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
FUTURES_FOLDER = os.path.join(REPO_ROOT, "adjusted_futures_data_final")
CASH_FOLDER    = os.path.join(REPO_ROOT, "stock_wise")
NIFTY_FILE     = os.path.join(FUTURES_FOLDER, "NIFTY.csv")

# ================= 1. FAST LOADERS =================

def load_nifty_master_schedule():
    """
    Creates a master DataFrame of [TIMESTAMP, EXP_DATE] containing 
    every valid expiry for every trading day based on NIFTY data.
    """
    print("⏳ Building Master Timeline from Nifty...")
    try:
        df = pd.read_csv(NIFTY_FILE, usecols=['TIMESTAMP', 'EXP_DATE'])
        df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'])
        df['EXP_DATE']  = pd.to_datetime(df['EXP_DATE'], dayfirst=True, errors='coerce')
        
        # Drop invalid rows and duplicates
        df = df.dropna().drop_duplicates().sort_values(['TIMESTAMP', 'EXP_DATE'])
        return df
    except Exception as e:
        print(f"❌ Critical Error loading Nifty: {e}")
        return pd.DataFrame()

def load_cash_fast(symbol):
    """Loads Cash data with minimal overhead."""
    path = os.path.join(CASH_FOLDER, f"{symbol}.csv")
    if not os.path.exists(path): return None
    
    try:
        df = pd.read_csv(path)
        # Normalize columns fast
        cols = {c: c.strip().title() for c in df.columns}
        df = df.rename(columns=cols)
        
        # Find Date column
        date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp']), None)
        if not date_col: return None
        
        df['TIMESTAMP'] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Keep only essential columns for calculation to save RAM
        req_cols = ['TIMESTAMP', 'Open', 'High', 'Low', 'Close']
        df = df[req_cols].dropna(subset=['TIMESTAMP']).drop_duplicates(subset=['TIMESTAMP'], keep='last')
        
        # Rename for easier merging
        return df.rename(columns={
            'Open': 'C_OPEN', 'High': 'C_HIGH', 'Low': 'C_LOW', 'Close': 'C_CLOSE'
        })
    except:
        return None

# ================= 2. WORKER LOGIC (VECTORIZED) =================

def process_single_stock(file_path, master_schedule):
    symbol = os.path.basename(file_path).replace(".csv", "")
    if symbol.upper() == "NIFTY": return None

    # --- A. Load Data ---
    cash_df = load_cash_fast(symbol)
    if cash_df is None or cash_df.empty: return None

    try:
        fut_df = pd.read_csv(file_path)
        fut_df.columns = fut_df.columns.str.strip().str.upper()
        fut_df['TIMESTAMP'] = pd.to_datetime(fut_df['TIMESTAMP'])
        fut_df['EXP_DATE']  = pd.to_datetime(fut_df['EXP_DATE'], errors='coerce')
        fut_df = fut_df.dropna(subset=['EXP_DATE'])
    except:
        return f"Corrupt: {symbol}"

    # --- B. Create The 'Perfect' Timeline ---
    # 1. Filter Master Schedule to only include dates where this Stock existed (via Cash data)
    #    This replicates: "if dt not in cash.index: continue"
    valid_dates = set(cash_df['TIMESTAMP'])
    stock_schedule = master_schedule[master_schedule['TIMESTAMP'].isin(valid_dates)].copy()
    stock_schedule['SYMBOL'] = symbol # Fill symbol column

    # --- C. Merge Data ---
    # 1. Merge Schedule with Actual Futures (Left Join keeps the Skeleton, brings in Data)
    merged = pd.merge(
        stock_schedule, 
        fut_df, 
        on=['TIMESTAMP', 'EXP_DATE', 'SYMBOL'], 
        how='left'
    )

    # 2. Merge with Cash Data (on Timestamp) to get Reference Prices
    merged = pd.merge(merged, cash_df, on='TIMESTAMP', how='left')

    # --- D. Gap Detection & Filling Logic ---
    # We only care about rows where Futures Data is Missing (NaN in CLOSE_PRICE)
    
    # Calculate 'Basis' (Difference between Future and Cash) for EXISTING rows
    # Logic: Basis = Future_Close - Cash_Close
    merged['BASIS'] = merged['CLOSE_PRICE'] - merged['C_CLOSE']

    # --- E. Forward Fill Basis ---
    # Group by Expiry to ensure we only carry forward values within the same contract
    # ffill() propagates the last valid Basis to the gap rows
    merged['BASIS'] = merged.groupby('EXP_DATE')['BASIS'].ffill()
    
    # Handle Phase 1 (No history for expiry): Fill initial NaNs with 0 (Future = Cash)
    merged['BASIS'] = merged['BASIS'].fillna(0)

    # --- F. Reconstruct Synthetic OHLC ---
    # Identify rows that need filling (where CLOSE_PRICE is NaN)
    mask = merged['CLOSE_PRICE'].isna()
    
    if not mask.any():
        return None # No gaps found

    # Close = Cash_Close + Basis (This is mathematically identical to your delta logic)
    merged.loc[mask, 'CLOSE_PRICE'] = merged.loc[mask, 'C_CLOSE'] + merged.loc[mask, 'BASIS']

    # Calculate Open/High/Low using Cash Volatility
    # Fut_High = Fut_Close + (Cash_High - Cash_Close)
    merged.loc[mask, 'OPEN_PRICE'] = round(merged.loc[mask, 'CLOSE_PRICE'] + (merged.loc[mask, 'C_OPEN'] - merged.loc[mask, 'C_CLOSE']), 2)
    merged.loc[mask, 'HI_PRICE']   = round(merged.loc[mask, 'CLOSE_PRICE'] + (merged.loc[mask, 'C_HIGH'] - merged.loc[mask, 'C_CLOSE']), 2)
    merged.loc[mask, 'LO_PRICE']   = round(merged.loc[mask, 'CLOSE_PRICE'] + (merged.loc[mask, 'C_LOW']  - merged.loc[mask, 'C_CLOSE']), 2)
    
    # Sanity check: Low Price > 0
    merged.loc[mask & (merged['LO_PRICE'] <= 0), 'LO_PRICE'] = 0.05

    # Fill Zero Values for Volume/OI
    cols_to_zero = ['TRD_QTY', 'OPEN_INT', 'NO_OF_CONT', 'TRD_VAL']
    for col in cols_to_zero:
        if col not in merged.columns: merged[col] = 0
        merged.loc[mask, col] = 0

    # --- G. Cleanup & Save ---
    # Rounding
    price_cols = ['OPEN_PRICE', 'HI_PRICE', 'LO_PRICE', 'CLOSE_PRICE']
    merged[price_cols] = merged[price_cols].round(2)

    # Drop helper columns
    final_df = merged.drop(columns=['C_OPEN', 'C_HIGH', 'C_LOW', 'C_CLOSE', 'BASIS'])
    
    # Sort
    final_df = final_df.sort_values(['TIMESTAMP', 'EXP_DATE'])
    
    # Atomic Save
    final_df.to_csv(file_path, index=False)
    
    return f"Fixed: {symbol}"

# ================= 3. ORCHESTRATOR =================

def harmonize_futures_safely():
    # 1. Load Master Schedule ONCE
    master_schedule = load_nifty_master_schedule()
    if master_schedule.empty: return

    # 2. Get Files
    files = glob.glob(os.path.join(FUTURES_FOLDER, "*.csv"))
    print(f"🚀 Starting Parallel Harmonization for {len(files)} stocks...")

    # 3. Parallel Processing
    # Use roughly 75% of CPUs to keep system responsive
    max_workers = max(1, os.cpu_count() - 1) 
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Create a partial function to fix the master_schedule argument
        worker = partial(process_single_stock, master_schedule=master_schedule)
        
        # Use tqdm to show progress bar for the iterator
        results = list(tqdm(executor.map(worker, files), total=len(files)))

    # 4. Summary
    fixed_count = sum(1 for r in results if r and "Fixed" in r)
    err_count = sum(1 for r in results if r and "Corrupt" in r)
    
    print("\n" + "="*40)
    print(f"✅ Processing Complete.")
    print(f"🔹 Files Updated: {fixed_count}")
    print(f"🔹 Files Corrupt: {err_count}")
    print(f"🔹 Files Skipped/Clean: {len(files) - fixed_count - err_count}")
    print("="*40)

if __name__ == "__main__":
    harmonize_futures_safely()