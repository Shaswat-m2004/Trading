
# # # PROJECT_ROOT: C:\Users\91702\Documents\programming\all_cash_stocks\set
# # # RAW_PR: C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\pr
# # # RAW_CA: C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\ca
# # # RAW_FO: C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\fo
# # # CLEAN_CA: C:\Users\91702\Documents\programming\all_cash_stocks\set\clean
# # # STOCK_WISE_PR: C:\Users\91702\Documents\programming\all_cash_stocks\stock_wise
# # # STOCK_WISE_FO: C:\Users\91702\Documents\programming\all_cash_stocks\adjusted_futures_data_final
# # # SECTOR_MAP: C:\Users\91702\Documents\programming\Trading_Data_Transformation\step3_fo_to_fo_pair\data\sector\sector_master_map.csv
# # # SECTOR_OUTPUT: C:\Users\91702\Documents\programming\all_cash_stocks\sec_wise_futures_data
# # # REMAINING_CA: C:\Users\91702\Documents\programming\Trading_Data_Transformation\automation\remaning_ca
# # # LOG_FILE: C:\Users\91702\Documents\programming\Trading_Data_Transformation\automation\logs\Futures_Skipped_CA_Log.csv



# import os
# import glob
# import pandas as pd
# import multiprocessing
# from datetime import datetime

# # ---------------------------------------------------------
# # HELPER FUNCTIONS
# # ---------------------------------------------------------

# def clean_spaces(df):
#     """Headers aur String columns se extra spaces hatata hai."""
#     # 1. Clean Headers
#     df.columns = df.columns.str.strip()
    
#     # 2. Clean String Values
#     for col in df.select_dtypes(['object']).columns:
#         df[col] = df[col].astype(str).str.strip()
#     return df

# def normalize_date_column(series):
#     """
#     Ek robust function jo kisi bhi date format ko 'YYYY-MM-DD' mein convert karega.
#     Ye Indian context (dayfirst=True) ko prioritize karta hai.
#     """
#     # Coerce errors: Agar date garbage hai to NaT ban jayega
#     dt_series = pd.to_datetime(series, dayfirst=True, errors='coerce')
#     return dt_series.dt.strftime('%Y-%m-%d')

# # ---------------------------------------------------------
# # CASH (PR) DATA TASK - [UPDATED WITH DUPLICATE CHECK]
# # ---------------------------------------------------------
# # Sirf task_process_pr function de raha hu (baaki code same rahega)

# def task_process_pr(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER):
#     print(f"🔹 [PR Task {os.getpid()}] Started (Cash Data)...")
    
#     files = glob.glob(os.path.join(RAW_PR_FOLDER, "Pr*.csv"))
#     if not files: 
#         print("   -> No PR files found.")
#         return

#     column_mapping = {
#         'SYMBOL': 'Symbol', 'SERIES': 'Series', 'PREV_CL_PR': 'Prev Close',
#         'OPEN_PRICE': 'Open', 'HIGH_PRICE': 'High', 'LOW_PRICE': 'Low',
#         'CLOSE_PRICE': 'Close', 'NET_TRDQTY': 'Volume', 'NET_TRDVAL': 'Turnover', 'TRADES': 'Trades'
#     }
#     output_columns = ['Date', 'Prev Close', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover', 'Trades']

#     for file_path in files:
#         try:
#             file_name = os.path.basename(file_path)
#             try:
#                 raw_date_str = file_name[2:8]
#                 date_obj = datetime.strptime(raw_date_str, "%d%m%y")
#                 master_date = date_obj.strftime("%Y-%m-%d")
#             except ValueError: continue
            
#             df = None
#             for enc in ['utf-8', 'cp1252', 'latin1']:
#                 try:
#                     df = pd.read_csv(file_path, engine='python', encoding=enc, on_bad_lines='skip')
#                     break
#                 except UnicodeDecodeError: continue
            
#             if df is None: continue

#             df = clean_spaces(df)
#             if 'MKT' in df.columns: df = df[df['MKT'].isin(['N', 'Y'])]
#             if 'SERIES' in df.columns: df = df[df['SERIES'] == 'EQ']

#             present_cols = [c for c in column_mapping.keys() if c in df.columns]
#             df = df[present_cols].rename(columns=column_mapping)
#             df['Date'] = str(master_date)
            
#             for symbol, group_df in df.groupby('Symbol'):
#                 safe_symbol = "".join([c for c in str(symbol) if c.isalnum() or c in (' ', '-', '_')]).strip()
#                 if not safe_symbol: continue
                
#                 # FIX 1: Use .copy() to avoid SettingWithCopyWarning
#                 final_df = group_df[output_columns].copy()
#                 out_file = os.path.join(STOCK_WISE_PR_FOLDER, f"{safe_symbol}.csv")
                
#                 if os.path.exists(out_file):
#                     try:
#                         existing_df = pd.read_csv(out_file)
#                         final_df['Date'] = final_df['Date'].astype(str)
#                         if 'Date' in existing_df.columns:
#                             existing_df['Date'] = existing_df['Date'].astype(str)
#                             merged_result = final_df.merge(existing_df[['Date']], on='Date', how='left', indicator=True)
#                             new_rows = merged_result[merged_result['_merge'] == 'left_only'].drop(columns=['_merge'])
#                         else:
#                             new_rows = final_df

#                         if not new_rows.empty:
#                             # FIX 2: Append with newline=''
#                             with open(out_file, 'a', newline='') as f:
#                                 new_rows.to_csv(f, header=False, index=False)
#                     except Exception as e:
#                         print(f"Error appending Cash {symbol}: {e}")
#                 else:
#                     # FIX 3: New File Create with newline='' (Ye missing tha!)
#                     with open(out_file, 'w', newline='') as f:
#                         final_df.to_csv(f, header=True, index=False)

#         except Exception as e:
#             pass

#     print(f"🏁 [PR Task] Completed.")

# # ---------------------------------------------------------
# # FUTURES (FO) DATA TASK
# # ---------------------------------------------------------

# def task_process_fo(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER):
#     print(f"🔹 [FO Task {os.getpid()}] Started (Futures Data)...")
    
#     files = glob.glob(os.path.join(RAW_FO_CSV, "fo*.csv"))
#     if not files: 
#         print("   -> No FO files found.")
#         return
#     print(f"   -> Found {len(files)} FO files.")

#     def get_date_from_filename(fp):
#         try: 
#             fname = os.path.basename(fp).replace('fo','').replace('.csv','')
#             return datetime.strptime(fname, "%d%m%Y")
#         except: 
#             return datetime.min
            
#     files.sort(key=get_date_from_filename)

#     for file_path in files:
#         try:
#             date_obj = get_date_from_filename(file_path)
#             if date_obj == datetime.min: continue
            
#             timestamp_str = date_obj.strftime("%Y-%m-%d")
            
#             df = pd.read_csv(file_path)
#             df = clean_spaces(df)

#             if 'EXP_DATE' in df.columns and 'SYMBOL' in df.columns:
                
#                 # Robust Date Handling
#                 df['EXP_DATE'] = normalize_date_column(df['EXP_DATE'])
#                 df = df.dropna(subset=['EXP_DATE'])
#                 df.insert(0, 'TIMESTAMP', timestamp_str)
       
#                 for symbol, data in df.groupby('SYMBOL'):
#                     safe_symbol = "".join([c for c in symbol if c.isalnum() or c in (' ', '-', '_')]).strip()
#                     output_file = os.path.join(STOCK_WISE_FO_FOLDER, f"{safe_symbol}.csv")

#                     if os.path.exists(output_file):
#                         try:
#                             existing_df = pd.read_csv(output_file)

#                             # --- DUPLICATE CHECK LOGIC ---
#                             data['TIMESTAMP'] = data['TIMESTAMP'].astype(str)
#                             data['EXP_DATE'] = data['EXP_DATE'].astype(str)
                            
#                             merge_cols = ['TIMESTAMP', 'INSTRUMENT', 'SYMBOL', 'EXP_DATE']
#                             present_merge_cols = [c for c in merge_cols if c in data.columns and c in existing_df.columns]
                            
#                             if not present_merge_cols:
#                                 new_rows = data
#                             else:
#                                 merged_result = data.merge(existing_df[present_merge_cols], 
#                                                            on=present_merge_cols, 
#                                                            how='left', 
#                                                            indicator=True)
                                
#                                 new_rows = merged_result[merged_result['_merge'] == 'left_only'].drop(columns=['_merge'])

#                             if not new_rows.empty:
#                                 with open(output_file, 'a', newline='') as f:
#                                     new_rows.to_csv(f, header=False, index=False)
#                         except Exception as e:
#                             print(f"Error appending Futures {symbol}: {e}")
#                     else:
#                         data.to_csv(output_file, mode='w', header=True, index=False)

#         except Exception as e:
#             print(f"❌ Error processing file {file_path}: {e}")
#             pass
            
#     print("🏁 [FO Task] Completed.")

# # ---------------------------------------------------------
# # MAIN EXECUTION
# # ---------------------------------------------------------

# def start_append_engine(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER):
#     multiprocessing.freeze_support()
    
#     print("\n🚀 STARTING PARALLEL APPEND ENGINE (Robust Date Handling + Duplicate Checks)...")
    
#     p_cash = multiprocessing.Process(target=task_process_pr, args=(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER))
#     p_fut = multiprocessing.Process(target=task_process_fo, args=(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER))

#     p_cash.start()
#     p_fut.start()

#     p_cash.join()
#     p_fut.join()

#     print("\n✅✅✅ PROCESSING COMPLETE ✅✅✅")


# if __name__ == "__main__":
#     start_append_engine(
#         r"C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\pr",
#         r"C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\fo",
#         r"C:\Users\91702\Documents\programming\all_cash_stocks\stock_wise",
#         r"C:\Users\91702\Documents\programming\all_cash_stocks\adjusted_futures_data_final"
#     )



import os
import glob
import pandas as pd
import multiprocessing
from datetime import datetime

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def clean_spaces(df):
    """Headers aur String columns se extra spaces hatata hai."""
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def normalize_date_column(series):
    """Robust Date Conversion Function"""
    dt_series = pd.to_datetime(series, dayfirst=True, errors='coerce')
    return dt_series.dt.strftime('%Y-%m-%d')



def task_process_pr(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER):
    print(f"🔹 [PR Task {os.getpid()}] Started (Cash Data)...")
    
    files = glob.glob(os.path.join(RAW_PR_FOLDER, "Pr*.csv"))
    if not files: 
        print("   -> No PR files found.")
        return

    column_mapping = {
        'SYMBOL': 'Symbol', 'SERIES': 'Series', 'PREV_CL_PR': 'Prev Close',
        'OPEN_PRICE': 'Open', 'HIGH_PRICE': 'High', 'LOW_PRICE': 'Low',
        'CLOSE_PRICE': 'Close', 'NET_TRDQTY': 'Volume', 'NET_TRDVAL': 'Turnover', 'TRADES': 'Trades'
    }
    output_columns = ['Date', 'Prev Close', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover', 'Trades']
    
    all_raw_dfs = []
    
    for file_path in files:
        try:
            file_name = os.path.basename(file_path)
            try:
                # Date Parsing
                raw_date_str = file_name[2:8]
                date_obj = datetime.strptime(raw_date_str, "%d%m%y")
                master_date = date_obj.strftime("%Y-%m-%d")
            except ValueError: continue
            
            # Fast Read
            df = None
            for enc in ['utf-8', 'cp1252', 'latin1']:
                try:
                    df = pd.read_csv(file_path, engine='c', encoding=enc, on_bad_lines='skip')
                    break
                except: continue
            
            if df is None: continue

            df = clean_spaces(df)
            if 'MKT' in df.columns: df = df[df['MKT'].isin(['N', 'Y'])]
            if 'SERIES' in df.columns: df = df[df['SERIES'] == 'EQ']
            
            present_cols = [c for c in column_mapping.keys() if c in df.columns]
            df = df[present_cols].rename(columns=column_mapping)
            df['Date'] = str(master_date)
            
            # 🔥 Fix: Keep Symbol for Grouping
            cols_to_keep = [c for c in output_columns if c in df.columns]
            if 'Symbol' in df.columns and 'Symbol' not in cols_to_keep:
                cols_to_keep.append('Symbol')
            
            df = df[cols_to_keep]
            
            if 'Symbol' in df.columns:
                all_raw_dfs.append(df)
                
        except Exception as e:
            pass

    if not all_raw_dfs:
        print("   -> No valid data extracted from PR files.")
        return

    print("   -> Aggregating Cash Data...")
    big_df = pd.concat(all_raw_dfs, ignore_index=True)
    
    # In-memory deduplication (Safety)
    if 'Symbol' in big_df.columns and 'Date' in big_df.columns:
        big_df.drop_duplicates(subset=['Symbol', 'Date'], keep='last', inplace=True)

    unique_symbols = big_df['Symbol'].unique()
    print(f"   -> Processing {len(unique_symbols)} unique stocks...")

    for symbol, group_df in big_df.groupby('Symbol'):
        safe_symbol = "".join([c for c in str(symbol) if c.isalnum() or c in (' ', '-', '_')]).strip()
        if not safe_symbol: continue
        
        final_df = group_df[output_columns].copy()
        out_file = os.path.join(STOCK_WISE_PR_FOLDER, f"{safe_symbol}.csv")
        
        try:
            # ✅ LOGIC START
            if os.path.exists(out_file):
                # 1. File Hai -> Duplicate Check Karo
                existing_dates = pd.read_csv(out_file, usecols=['Date'])
                existing_dates['Date'] = existing_dates['Date'].astype(str)
                final_df['Date'] = final_df['Date'].astype(str)
                
                # Sirf naya data nikalo
                new_rows = final_df[~final_df['Date'].isin(existing_dates['Date'])]
                

                if not new_rows.empty:
                     with open(out_file, 'a', newline='') as f:
                         new_rows.to_csv( f, header=False, index=False, lineterminator='\n' )
            else:
                with open(out_file, 'w', newline='') as f:
                    final_df.to_csv( f, header=True, index=False, lineterminator='\n' )


            # ✅ LOGIC END
                    
        except Exception as e:
            print(f"Error processing Cash {symbol}: {e}")


    print(f"🏁 [PR Task] Completed.")

# ---------------------------------------------------------
# FUTURES (FO) DATA TASK - [OPTIMIZED: BATCH PROCESSING]
# ---------------------------------------------------------

def task_process_fo(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER):
    print(f"🔹 [FO Task {os.getpid()}] Started (Futures Data)...")
    
    files = glob.glob(os.path.join(RAW_FO_CSV, "fo*.csv"))
    if not files: 
        print("   -> No FO files found.")
        return
    
    # Sorting logic kept same
    def get_date_from_filename(fp):
        try: 
            fname = os.path.basename(fp).replace('fo','').replace('.csv','')
            return datetime.strptime(fname, "%d%m%Y")
        except: return datetime.min
    files.sort(key=get_date_from_filename)

    # --- STEP 1: READ ALL RAW FILES INTO MEMORY ---
    all_raw_dfs = []
    
    for file_path in files:
        try:
            date_obj = get_date_from_filename(file_path)
            if date_obj == datetime.min: continue
            timestamp_str = date_obj.strftime("%Y-%m-%d")
            
            # Engine 'c' for speed
            df = pd.read_csv(file_path, engine='c')
            df = clean_spaces(df)

            if 'EXP_DATE' in df.columns and 'SYMBOL' in df.columns:
                df['EXP_DATE'] = normalize_date_column(df['EXP_DATE'])
                df = df.dropna(subset=['EXP_DATE'])
                df.insert(0, 'TIMESTAMP', timestamp_str)
                
                all_raw_dfs.append(df)
        except Exception: pass

    if not all_raw_dfs:
        return

    # --- STEP 2: CONCATENATE ---
    print("   -> Aggregating Futures Data...")
    big_df = pd.concat(all_raw_dfs, ignore_index=True)

    # --- STEP 3: PROCESS PER STOCK ---
    # Ensure strict string types for key columns before grouping
    big_df['TIMESTAMP'] = big_df['TIMESTAMP'].astype(str)
    big_df['EXP_DATE'] = big_df['EXP_DATE'].astype(str)

    unique_symbols = big_df['SYMBOL'].unique()
    print(f"   -> Processing {len(unique_symbols)} unique futures symbols...")

    for symbol, data in big_df.groupby('SYMBOL'):
        safe_symbol = "".join([c for c in symbol if c.isalnum() or c in (' ', '-', '_')]).strip()
        output_file = os.path.join(STOCK_WISE_FO_FOLDER, f"{safe_symbol}.csv")
        
        try:
            if os.path.exists(output_file):
                # Optimization: Read only columns needed for Unique Identity
                merge_cols = ['TIMESTAMP', 'INSTRUMENT', 'SYMBOL', 'EXP_DATE']
                
                # Check if file has these columns first (by reading just header)
                header_df = pd.read_csv(output_file, nrows=0)
                present_merge_cols = [c for c in merge_cols if c in header_df.columns]
                
                if present_merge_cols:
                    existing_keys = pd.read_csv(output_file, usecols=present_merge_cols)
                    
                    # Ensure types match
                    for col in present_merge_cols:
                        existing_keys[col] = existing_keys[col].astype(str)
                        if col in data.columns:
                            data[col] = data[col].astype(str)

                    # Logic: Left Anti-Join using Merge (Logic preserved from your code)
                    new_rows = data.merge(existing_keys, on=present_merge_cols, how='left', indicator=True)
                    new_rows = new_rows[new_rows['_merge'] == 'left_only'].drop(columns=['_merge'])
                else:
                    new_rows = data # Append blind if columns mismatch
                
                if not new_rows.empty:
                    with open(output_file, 'a', newline='') as f:
                        new_rows.to_csv(f, header=False, index=False)
            else:
                with open(output_file, 'w', newline='') as f:
                    data.to_csv(f, header=True, index=False)

        except Exception as e:
            print(f"Error appending Futures {symbol}: {e}")

    print("🏁 [FO Task] Completed.")

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------

def start_append_engine(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER):
    multiprocessing.freeze_support()
    
    print("\n🚀 STARTING OPTIMIZED PARALLEL APPEND ENGINE...")
    print("ℹ️  Technique: Batch In-Memory Aggregation")
    
    p_cash = multiprocessing.Process(target=task_process_pr, args=(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER))
    p_fut = multiprocessing.Process(target=task_process_fo, args=(RAW_PR_FOLDER, RAW_FO_CSV, STOCK_WISE_PR_FOLDER, STOCK_WISE_FO_FOLDER))

    p_cash.start()
    p_fut.start()

    p_cash.join()
    p_fut.join()

    print("\n✅✅✅ PROCESSING COMPLETE ✅✅✅")


if __name__ == "__main__":
    start_append_engine(
        r"C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\pr",
        r"C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\fo",
        r"C:\Users\91702\Documents\programming\all_cash_stocks\stock_wise",
        r"C:\Users\91702\Documents\programming\all_cash_stocks\adjusted_futures_data_final"
    )