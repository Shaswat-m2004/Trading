# import os
# import json
# import time
# import re
# import pandas as pd
# from datetime import datetime, timedelta
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By

# # ================= CONFIGURATION =================
# BASE_DIR = r"C:\Users\91702\Documents\programming\all_cash_stocks\set"

# # Folders
# RAW_CA_FOLDER = os.path.join(BASE_DIR, "raw", "ca")
# OUTPUT_FOLDER = r"C:\Users\91702\Documents\programming\all_cash_stocks\set\clean"

# # Create directories
# os.makedirs(RAW_CA_FOLDER, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# # =================================================

# # --- 1. SETUP DRIVER (To mimic real browser) ---
# def init_driver():
#     options = Options()
#     # Real User-Agent taaki NSE block na kare
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     # options.add_argument("--headless")  # Agar background me chalana hai to uncomment karein
    
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

# # --- 2. FETCH TASK (Selenium Logic) ---
# def task_fetch_ca(start_date, end_date):
#     print(f"🔹 [Fetcher] Started. Opening Browser...")
#     driver = init_driver()
    
#     try:
#         # 1. Homepage visit karke Cookies set hone do
#         print("   -> Visiting Homepage for Cookies...")
#         driver.get("https://www.nseindia.com")
#         time.sleep(10)  # Thoda zyada wait taaki cookies ache se load ho jaye

#         current_start = start_date 

#         while current_start <= end_date:
#             # NSE allow max 365 days per request
#             current_end = min(current_start + timedelta(days=364), end_date)
#             from_d = current_start.strftime("%d-%m-%Y")
#             to_d = current_end.strftime("%d-%m-%Y")
            
#             file_name = f"Corporate_Actions_{from_d}_to_{to_d}.csv"
#             save_path = os.path.join(RAW_CA_FOLDER, file_name)

#             # Agar file pehle se hai to skip karo
#             if os.path.exists(save_path):
#                 print(f"   -> Skipping {from_d} to {to_d} (Already exists)")
#                 current_start = current_end + timedelta(days=1)
#                 continue

#             print(f"   -> Fetching: {from_d} to {to_d}")
#             api_url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_d}&to_date={to_d}"
            
#             driver.get(api_url)
#             time.sleep(3) # Page load wait
            
#             try:
#                 # Body tag se raw text (JSON) uthana
#                 content = driver.find_element(By.TAG_NAME, "body").text
#                 data = json.loads(content)
                
#                 if isinstance(data, list) and data:
#                     df = pd.DataFrame(data)
                    
#                     # Filter: Sirf Equity Series
#                     if "series" in df.columns:
#                         df = df[df["series"] == "EQ"]
                    
#                     if not df.empty:
#                         df.to_csv(save_path, index=False)
#                         print(f"✅ Saved CSV: {file_name} ({len(df)} rows)")
#                     else:
#                         print(f"⚠️ No EQ data found for this range.")
#                 else:
#                     print(f"⚠️ Empty or Invalid JSON received.")

#             except json.JSONDecodeError:
#                 print("❌ Failed to parse JSON. Maybe NSE blocked or Session expired.")
#             except Exception as e:
#                 print(f"⚠️ Error extracting data: {e}")

#             # Next Loop Preparation
#             current_start = current_end + timedelta(days=1)
#             time.sleep(2) # Polite delay

#     except Exception as e:
#         print(f"🛑 CRITICAL ERROR in Driver: {e}")
#     finally:
#         driver.quit()
#         print("🏁 [Fetcher] Browser Closed.")

# # --- 3. CLEAN TASK (Raw CSV -> Stock Wise Cleaned) ---
# def task_clean_ca():
    
#     KEEP_PATTERNS = re.compile(
#         r"""
#         bonus |
#         rights |
#         right\s*issue |
#         split |
#         sub[-\s]*division |
#         face\s*value |
#         demerger |
#         demerge |
#         special\s*div |
#         spl\s*div|
#         amalgamation
#         """,
#         re.IGNORECASE | re.VERBOSE
#     )

#     REJECT_PATTERNS = re.compile(
#         r"""
#         interim |
#         int\s*div
#         """,
#         re.IGNORECASE | re.VERBOSE
#     )

#     # ================== COLUMN MAP ==================
#     COLUMN_MAP = {
#         "exdate": "exDate",
#         "recdate": "recDate",
#         "bcstartdate": "bcStartDate",
#         "bcenddate": "bcEndDate",
#         "ndstartdate": "ndStartDate",
#         "ndenddate": "ndEndDate",
#         "cabroadcastdate": "caBroadcastDate",
#         "symbol": "symbol",
#         "series": "series",
#         "ind": "ind",
#         "faceval": "faceVal",
#         "subject": "subject",
#         "comp": "comp",
#         "isin": "isin",
#     }

#     FINAL_COLUMNS = list(COLUMN_MAP.keys())

#     # ================== PROCESS ==================

#     for file in os.listdir(RAW_CA_FOLDER):
#         if not file.endswith(".csv"):
#             continue

#         src_path = os.path.join(RAW_CA_FOLDER, file)
        
#         dst_file = get_next_ca_filename(CLEAN_CA_FOLDER)
#         dst_path = os.path.join(CLEAN_CA_FOLDER, dst_file)

#         try:
#             df = pd.read_csv(src_path)
#         except Exception:
#             print(f"❌ Skipped unreadable file: {file}")
#             continue

#         # --- Normalize columns ---
#         df.columns = df.columns.str.strip()

#         # --- SERIES EQ only ---
#         if "series" not in df.columns:
#             continue

#         df = df[df["series"] == "EQ"]

#         if df.empty:
#             continue

#         # --- Subject filtering ---
#         df["subject"] = df["subject"].astype(str)

#         keep_mask = df["subject"].str.contains(KEEP_PATTERNS, na=False)
#         reject_mask = df["subject"].str.contains(REJECT_PATTERNS, na=False)

#         df = df[keep_mask & ~reject_mask]

#         if df.empty:
#             continue

#         # --- Rename & reorder ---
#         df_clean = pd.DataFrame()

#         for new_col, old_col in COLUMN_MAP.items():
#             df_clean[new_col] = df.get(old_col, "")

#         # --- Date formatting ---
#         for c in ["exdate", "recdate"]:
#             df_clean[c] = pd.to_datetime(df_clean[c], errors="coerce").dt.strftime("%Y-%m-%d")

#         date_fill_cols = [
#             "bcstartdate", "bcenddate",
#             "ndstartdate", "ndenddate",
#             "cabroadcastdate"
#         ]
#         for c in date_fill_cols:
#             df_clean[c] = df_clean[c].fillna(0)

#         # --- Remove duplicates ---
#         df_clean = df_clean.drop_duplicates()
#         # --- Replace "-" with 0 everywhere ---
#         df_clean = df_clean.replace("-", 0)


#         # --- Save ---
#         df_clean.to_csv(dst_path, index=False)
#         print(f"✅ Cleaned CA saved: {file}")

#     print("\n🎉 Corporate Action cleaning completed safely.")


# # ================= MAIN EXECUTION =================
# if __name__ == "__main__":
#     # 1. Define Range (Last 2 Years for safety)
#     end_d = datetime.now() + timedelta(days=90) # Future data bhi
#     start_d = datetime.now() - timedelta(days=730) # Pichle 2 saal
    
#     # 2. Run Fetcher (Selenium)
#     task_fetch_ca(start_d, end_d)
    
#     # 3. Run Cleaner (Processing)
#     task_clean_ca()





# import os
# import pandas as pd
# import re

# # ================== PATHS ==================
# RAW_CA_FOLDER = r"C:\Users\91702\Documents\programming\Trading_Data_Transformation\automation\raw\ca_api"
# CLEAN_CA_FOLDER = r"C:\Users\91702\Documents\programming\Trading_Data_Transformation\automation\raw\clean_ca"

# os.makedirs(CLEAN_CA_FOLDER, exist_ok=True)

# # ================== REGEX RULES ==================

# # def get_next_ca_filename(folder):
# #     pattern = re.compile(r"corporate_action_data_(\d+)\.csv")
# #     max_num = 0

# #     for f in os.listdir(folder):
# #         match = pattern.match(f)
# #         if match:
# #             max_num = max(max_num, int(match.group(1)))

# #     return f"corporate_action_data_{max_num + 1}.csv"


# # def clean_ca_data():
    


# import os
# import json
# import time
# import re
# import pandas as pd
# from datetime import datetime, timedelta
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By

# # ================= CONFIGURATION =================
# # BASE_DIR = r"C:\Users\91702\Documents\programming\app\set"
# # RAW_CA_FOLDER = os.path.join(BASE_DIR, "raw", "ca")
# # OUTPUT_FOLDER = r"C:\Users\91702\Documents\programming\app\data\Corporate_Action_Stock_Wise_formated"

# BASE_DIR = r"C:\Users\91702\Documents\programming\all_cash_stocks\set"

# # Folders
# RAW_CA_FOLDER = os.path.join(BASE_DIR, "raw", "ca")
# OUTPUT_FOLDER = r"C:\Users\91702\Documents\programming\all_cash_stocks\set\clean"

# os.makedirs(RAW_CA_FOLDER, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# # =================================================

# def init_driver():
#     options = Options()
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     # options.add_argument("--headless") 
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

# # --- FETCHER (Same as before) ---
# def task_fetch_ca(start_date, end_date):
#     print(f"🔹 [Fetcher] Started. Opening Browser...")
#     driver = init_driver()
#     try:
#         driver.get("https://www.nseindia.com")
#         time.sleep(10)

#         current_start = start_date 
#         while current_start <= end_date:
#             current_end = min(current_start + timedelta(days=364), end_date)
#             from_d = current_start.strftime("%d-%m-%Y")
#             to_d = current_end.strftime("%d-%m-%Y")
            
#             file_name = f"Corporate_Actions_{from_d}_to_{to_d}.csv"
#             save_path = os.path.join(RAW_CA_FOLDER, file_name)

#             if os.path.exists(save_path):
#                 print(f"   -> Skipping {from_d} to {to_d}")
#                 current_start = current_end + timedelta(days=1)
#                 continue

#             print(f"   -> Fetching: {from_d} to {to_d}")
#             api_url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_d}&to_date={to_d}"
#             driver.get(api_url)
#             time.sleep(3)
            
#             try:
#                 content = driver.find_element(By.TAG_NAME, "body").text
#                 data = json.loads(content)
#                 if isinstance(data, list) and data:
#                     df = pd.DataFrame(data)
#                     if "series" in df.columns: df = df[df["series"] == "EQ"]
#                     if not df.empty: df.to_csv(save_path, index=False)
#             except: pass

#             current_start = current_end + timedelta(days=1)
#             time.sleep(2)
#     except Exception as e: print(e)
#     finally: driver.quit()

# # --- CLEANER (STRICT FORMATTING) ---
# def task_clean_ca():
#     print("\n🔹 [Cleaner] Starting Formatting Process...")
    
#     KEEP_PATTERNS = re.compile(r"bonus|rights|right\s*issue|split|sub[-\s]*division|face\s*value|demerger|demerge|special\s*div|spl\s*div|amalgamation", re.IGNORECASE)
#     REJECT_PATTERNS = re.compile(r"interim|int\s*div|final\s*div|interest|agm|egm|meeting", re.IGNORECASE)

#     # 1. Target Column Order (Jo aapko chahiye)
#     FINAL_COLUMNS = [
#         "exdate", "recdate", "bcstartdate", "bcenddate", 
#         "ndstartdate", "ndenddate", "cabroadcastdate", 
#         "symbol", "series", "ind", "faceval", "subject", "comp", "isin"
#     ]

#     files = [f for f in os.listdir(RAW_CA_FOLDER) if f.endswith(".csv")]
#     if not files: return

#     for file in files:
#         src_path = os.path.join(RAW_CA_FOLDER, file)
#         try:
#             df = pd.read_csv(src_path)
#             df.columns = df.columns.str.strip()
            
#             # Ensure Subject Exists
#             if 'purpose' in df.columns: df['subject'] = df['purpose']
#             if 'subject' not in df.columns: continue

#             # Regex Filter
#             keep_mask = df["subject"].str.contains(KEEP_PATTERNS, na=False)
#             reject_mask = df["subject"].str.contains(REJECT_PATTERNS, na=False)
#             df = df[keep_mask & ~reject_mask]
#             if df.empty: continue

#             # --- MAPPING LOGIC ---
#             df_clean = pd.DataFrame()

#             # Direct Mappings (NSE -> Output)
#             df_clean['exdate'] = df.get('exDate', '')
#             df_clean['recdate'] = df.get('recordDate', '')
#             df_clean['bcstartdate'] = df.get('bcStartDate', '0')
#             df_clean['bcenddate'] = df.get('bcEndDate', '0')
#             df_clean['ndstartdate'] = df.get('ndStartDate', '0')
#             df_clean['ndenddate'] = df.get('ndEndDate', '0')
#             df_clean['cabroadcastdate'] = df.get('broadcastDate', '0') # Often missing
            
#             df_clean['symbol'] = df.get('symbol', '')
#             df_clean['series'] = df.get('series', 'EQ')
#             df_clean['ind'] = df.get('industry', '0')       # NSE rarely sends this
#             df_clean['faceval'] = df.get('faceValue', '0.0')
#             df_clean['subject'] = df.get('subject', '')
#             df_clean['comp'] = df.get('companyName', '')
#             df_clean['isin'] = df.get('isin', '')           # NSE sends ISIN

#             # --- CLEANING VALUES ---
#             # 1. Dates ko sahi format karein: YYYY-MM-DD
#             # Aur agar date missing hai (Nan) toh wahan "0" ya waisa format rakhein
#             date_cols = ['exdate', 'recdate', 'bcstartdate', 'bcenddate', 'ndstartdate', 'ndenddate']
            
#             for col in date_cols:
#                 # Pehle datetime me convert karo
#                 temp_dates = pd.to_datetime(df_clean[col], errors='coerce')
#                 # Format change karo
#                 df_clean[col] = temp_dates.dt.strftime("%Y-%m-%d")
#                 # Jo NaT (Not a Time) hain unhe '0' kardo (jaisa aapke sample me hai)
#                 df_clean[col] = df_clean[col].fillna("0")

#             # 2. Fill Missing numeric/text values with '0' or '-'
#             df_clean['ind'] = df_clean['ind'].fillna('0')
#             df_clean['cabroadcastdate'] = df_clean['cabroadcastdate'].fillna('0')
#             df_clean['isin'] = df_clean['isin'].fillna('-')

#             # --- REORDERING & SAVING ---
#             # Sirf FINAL_COLUMNS list wale columns hi rakho aur usi order me
#             df_final = df_clean[FINAL_COLUMNS]

#             # Save Stock Wise
#             for symbol, grp in df_final.groupby("symbol"):
#                 safe_symbol = "".join([c for c in str(symbol) if c.isalnum() or c in (' ', '-', '_')]).strip()
#                 output_file = os.path.join(OUTPUT_FOLDER, f"{safe_symbol}.csv")
                
#                 if os.path.exists(output_file):
#                     existing = pd.read_csv(output_file)
#                     # Merge and Drop Duplicates
#                     combined = pd.concat([existing, grp], ignore_index=True)
#                 else:
#                     combined = grp
                
#                 # Deduplicate logic
#                 combined = combined.drop_duplicates(subset=["exdate", "subject"], keep="last")
#                 # Sort by Date
#                 combined = combined.sort_values("exdate")
                
#                 combined.to_csv(output_file, index=False)

#         except Exception as e:
#             pass
    
#     print("✅ Cleaning & Formatting Complete (Strict Format Applied).")

# # ================= MAIN =================
# if __name__ == "__main__":
#     end_d = datetime.now() 
#     start_d = datetime.now() - timedelta(days=16)
    
#     task_fetch_ca(start_d, end_d)
#     task_clean_ca()



import time, json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import os
import pandas as pd 
import re



# RAW_CA = r"C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\ca"
# os.makedirs(RAW_CA, exist_ok=True)

# def init_driver():
#     options = webdriver.ChromeOptions()
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
#     )
#     return webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=options
#     )

# def fetch_ca_api(start_date, end_date):
#     driver = init_driver()
#     print("🌐 NSE site open ho rahi hai (cookies)...")

#     try:
#         driver.get("https://www.nseindia.com")
#         time.sleep(10)

#         current_start = start_date + timedelta(days=1)

#         while current_start <= end_date:
#             current_end = min(current_start + timedelta(days=364), end_date)

#             from_d = current_start.strftime("%d-%m-%Y")
#             to_d = current_end.strftime("%d-%m-%Y")

#             file_name = f"Corporate_Actions_{from_d}_to_{to_d}.csv"
#             save_path = os.path.join(RAW_CA, file_name)

#             if os.path.exists(save_path):
#                 current_start = current_end + timedelta(days=1)
#                 continue

#             print(f"📥 CA {from_d} → {to_d}", end=" ")

#             api_url = (
#                 "https://www.nseindia.com/api/"
#                 f"corporates-corporateActions?index=equities"
#                 f"&from_date={from_d}&to_date={to_d}"
#             )

#             driver.get(api_url)
#             time.sleep(3)

#             content = driver.find_element("tag name", "body").text

#             try:
#                 data = json.loads(content)

#                 if isinstance(data, list) and data:
#                     df = pd.DataFrame(data)

#                     # 🔒 IMPORTANT: only EQ
#                     if "series" in df.columns:
#                         df = df[df["series"] == "EQ"]

#                     if not df.empty:
#                         df.to_csv(save_path, index=False)
#                         print("✅")
#                     else:
#                         print("⚠️ No EQ data")
#                 else:
#                     print("⚠️ Empty")

#             except json.JSONDecodeError:
#                 print("❌ Blocked")
#                 time.sleep(5)

#             current_start = current_end + timedelta(days=1)
#             time.sleep(2)

#     finally:
#         driver.quit()
#         print("🔚 CA fetch complete")



# ================== PATHS ==================


# ================== REGEX RULES ==================

def get_next_ca_filename(folder):
    pattern = re.compile(r"corporate_action_data_(\d+)\.csv")
    max_num = 0

    for f in os.listdir(folder):
        match = pattern.match(f)
        if match:
            max_num = max(max_num, int(match.group(1)))

    return f"corporate_action_data_{max_num + 1}.csv"


def clean_ca_data(RAW_CA_FOLDER=None, CLEAN_CA_FOLDER=None):
    # Resolve repo-relative defaults when None provided
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
    if RAW_CA_FOLDER is None:
        RAW_CA_FOLDER = os.path.join(REPO_ROOT, "set", "raw", "ca")
    if CLEAN_CA_FOLDER is None:
        CLEAN_CA_FOLDER = os.path.join(REPO_ROOT, "set", "clean")
    
    KEEP_PATTERNS = re.compile(
        r"""
        bonus |
        rights |
        right\s*issue |
        split |
        sub[-\s]*division |
        face\s*value |
        demerger |
        demerge |
        special\s*div |
        spl\s*div|
        amalgamation
        """,
        re.IGNORECASE | re.VERBOSE
    )

    REJECT_PATTERNS = re.compile(
        r"""
        interim |
        int\s*div
        """,
        re.IGNORECASE | re.VERBOSE
    )

    # ================== COLUMN MAP ==================
    COLUMN_MAP = {
        "exdate": "exDate",
        "recdate": "recDate",
        "bcstartdate": "bcStartDate",
        "bcenddate": "bcEndDate",
        "ndstartdate": "ndStartDate",
        "ndenddate": "ndEndDate",
        "cabroadcastdate": "caBroadcastDate",
        "symbol": "symbol",
        "series": "series",
        "ind": "ind",
        "faceval": "faceVal",
        "subject": "subject",
        "comp": "comp",
        "isin": "isin",
    }

    FINAL_COLUMNS = list(COLUMN_MAP.keys())

    # ================== PROCESS ==================

    for file in os.listdir(RAW_CA_FOLDER):
        if not file.endswith(".csv"):
            continue

        src_path = os.path.join(RAW_CA_FOLDER, file)
        
        dst_file = get_next_ca_filename(CLEAN_CA_FOLDER)
        dst_path = os.path.join(CLEAN_CA_FOLDER, dst_file)

        try:
            df = pd.read_csv(src_path)
        except Exception:
            print(f"❌ Skipped unreadable file: {file}")
            continue

        # --- Normalize columns ---
        df.columns = df.columns.str.strip()

        # --- SERIES EQ only ---
        if "series" not in df.columns:
            continue

        df = df[df["series"] == "EQ"]

        if df.empty:
            continue

        # --- Subject filtering ---
        df["subject"] = df["subject"].astype(str)

        keep_mask = df["subject"].str.contains(KEEP_PATTERNS, na=False)
        reject_mask = df["subject"].str.contains(REJECT_PATTERNS, na=False)

        df = df[keep_mask & ~reject_mask]

        if df.empty:
            continue

        # --- Rename & reorder ---
        df_clean = pd.DataFrame()

        for new_col, old_col in COLUMN_MAP.items():
            df_clean[new_col] = df.get(old_col, "")

        # --- Date formatting ---
        for c in ["exdate", "recdate"]:
            df_clean[c] = pd.to_datetime(df_clean[c], errors="coerce").dt.strftime("%Y-%m-%d")

        date_fill_cols = [
            "bcstartdate", "bcenddate",
            "ndstartdate", "ndenddate",
            "cabroadcastdate"
        ]
        for c in date_fill_cols:
            df_clean[c] = df_clean[c].fillna(0)

        # --- Remove duplicates ---
        df_clean = df_clean.drop_duplicates()
        # --- Replace "-" with 0 everywhere ---
        df_clean = df_clean.replace("-", 0)


        # --- Save ---
        df_clean.to_csv(dst_path, index=False)
        print(f"✅ Cleaned CA saved: {file}")

    print("\n🎉 Corporate Action cleaning completed safely.")


# if __name__ == '__main__':



if __name__ == '__main__':
#     # fetch_ca_api(datetime.strptime('2025-12-20', '%Y-%m-%d'), datetime.strptime('2025-12-31', '%Y-%m-%d'))
    clean_ca_data()
