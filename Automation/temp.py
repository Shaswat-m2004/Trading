# import os
# import glob
# import pandas as pd
# import multiprocessing
# from datetime import datetime

# # ---------------------------------------------------------
# # CLEANING LOGIC FOR CASH (EQUITY)
# # ---------------------------------------------------------
# def clean_cash_folder(FOLDER_PATH):
#     print(f"🧹 [Cash Cleaner] Scanning folder: {FOLDER_PATH}")
#     files = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))
    
#     if not files:
#         print("   -> No files found to clean.")
#         return

#     count = 0
#     for file_path in files:
#         try:
#             # 1. Read Data
#             df = pd.read_csv(file_path)
            
#             # 2. Drop Empty Rows (Blank Lines fix)
#             df = df.dropna(how='all') 
            
#             # 3. Standardize Date
#             if 'Date' in df.columns:
#                 # Convert to datetime objects
#                 df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
#                 # Remove rows with invalid dates
#                 df = df.dropna(subset=['Date'])
#                 # Format strictly to YYYY-MM-DD string
#                 df['Date'] = df['Date'].dt.strftime('%Y-%d-%m')
                
#                 # 4. Remove Duplicates (Keep Last entry)
#                 original_len = len(df)
#                 df = df.drop_duplicates(subset=['Date'], keep='last')
                
#                 # 5. Sort by Date (Chronological Order)
#                 df = df.sort_values(by='Date')
                
#                 # 6. Save back (Overwrite)
#                 # newline='' is crucial for Windows to prevent blank lines
#                 df.to_csv(file_path, index=False)
                
#                 count += 1
#                 if count % 100 == 0:
#                     print(f"   -> Cleaned {count} Cash files...")

#         except Exception as e:
#             print(f"❌ Error cleaning {os.path.basename(file_path)}: {e}")

#     print(f"✅ [Cash Cleaner] Finished. Cleaned {count} files.")


# # ---------------------------------------------------------
# # CLEANING LOGIC FOR FUTURES (FO)
# # ---------------------------------------------------------
# def clean_futures_folder(FOLDER_PATH):
#     print(f"🧹 [Futures Cleaner] Scanning folder: {FOLDER_PATH}")
#     files = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))
    
#     if not files:
#         print("   -> No files found to clean.")
#         return

#     count = 0
#     for file_path in files:
#         try:
#             # 1. Read Data
#             df = pd.read_csv(file_path)
            
#             # 2. Drop Empty Rows
#             df = df.dropna(how='all')

#             # Check necessary columns
#             if 'TIMESTAMP' in df.columns and 'EXP_DATE' in df.columns:
                
#                 # 3. Standardize Dates (Timestamp & Expiry)
#                 df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], dayfirst=True, errors='coerce')
#                 df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'], dayfirst=True, errors='coerce')
                
#                 # Remove invalid dates
#                 df = df.dropna(subset=['TIMESTAMP', 'EXP_DATE'])
                
#                 # Convert back to string YYYY-MM-DD
#                 df['TIMESTAMP'] = df['TIMESTAMP'].dt.strftime('%Y-%m-%d')
#                 df['EXP_DATE'] = df['EXP_DATE'].dt.strftime('%Y-%m-%d')

#                 # 4. Remove Duplicates
#                 # Futures unique key: Timestamp + Symbol + Expiry + Instrument
#                 # Agar ek din mein same expiry ke 2 rows hain, toh duplicate hai
#                 subset_cols = ['TIMESTAMP', 'SYMBOL', 'EXP_DATE', 'INSTRUMENT']
#                 # Filter subset cols to only those present in df
#                 actual_subset = [c for c in subset_cols if c in df.columns]
                
#                 df = df.drop_duplicates(subset=actual_subset, keep='last')

#                 # 5. Sort (Primary: Date, Secondary: Expiry)
#                 df = df.sort_values(by=['TIMESTAMP', 'EXP_DATE'])

#                 # 6. Save back
#                 df.to_csv(file_path, index=False)
                
#                 count += 1
#                 if count % 100 == 0:
#                     print(f"   -> Cleaned {count} Futures files...")
            
#         except Exception as e:
#             print(f"❌ Error cleaning {os.path.basename(file_path)}: {e}")

#     print(f"✅ [Futures Cleaner] Finished. Cleaned {count} files.")


# # ---------------------------------------------------------
# # MAIN EXECUTION
# # ---------------------------------------------------------
# if __name__ == "__main__":
#     multiprocessing.freeze_support()
    
#     # 🔴 INPUT YOUR FOLDER PATHS HERE
#     CASH_FOLDER = r"C:\Users\91702\Documents\programming\all_cash_stocks\stock_wise"
#     FUTURES_FOLDER = r"C:\Users\91702\Documents\programming\all_cash_stocks\adjusted_futures_data_final"
    
#     print("\n🚀 STARTING ONE-TIME DEEP CLEANING PROCESS...")
#     print("⚠️  Ensure you have a backup before proceeding!\n")
    
#     # Running in Parallel to save time
#     p1 = multiprocessing.Process(target=clean_cash_folder, args=(CASH_FOLDER,))
#     p2 = multiprocessing.Process(target=clean_futures_folder, args=(FUTURES_FOLDER,))
    
#     p1.start()
#     p2.start()
    
#     p1.join()
#     p2.join()
    
#     print("\n✨✨✨ ALL FILES ARE NOW SQUEAKY CLEAN! ✨✨✨")


import pandas as pd

# Define the file path
file_path = r"C:\Users\91702\Documents\programming\Trading_Data_Transformation\step2\Adjusted_Futures_Data_2\MCX.csv"

try:
    # 1. Read the CSV file
    df = pd.read_csv(file_path)

    # 2. Convert 'EXP_DATE' column to datetime objects
    # dayfirst=True tells pandas that the date is in DD/MM/YYYY format initially
    df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'], dayfirst=True)

    # 3. Format it back to string in YYYY-MM-DD format
    df['EXP_DATE'] = df['EXP_DATE'].dt.strftime('%Y-%m-%d')

    # 4. Save the modified data back to the CSV (overwriting the original)
    df.to_csv(file_path, index=False)

    print(f"Success! File saved at: {file_path}")
    print("New Data Head:")
    print(df.head())

except Exception as e:
    print(f"An error occurred: {e}")