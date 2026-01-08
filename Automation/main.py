
import os
import sys
import shutil
from datetime import datetime, timedelta

# --- FIX: Ensure we can find modules regardless of where this is run from ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- Custom Modules ---
# If these fail, check that find_date.py is in the same folder as main.py
from find_date import get_last_available_date, get_last_available_date_futures
from fetch_data import fetch_all_data
from set_ca import clean_ca_data
from append_data import start_append_engine
from adjustment_engine import run_engine
from set_sector_wise import organize_stocks_by_sector
from set_proxy import harmonize_futures_safely

# --- CONFIGURATION ---
# Make paths relative to the repository root (parent directory of this Automation folder)
BASE_ROOT = os.path.abspath(os.path.join(current_dir, ".."))
PROJECT_DIR = os.path.join(BASE_ROOT, "set")
DATA_DIR = BASE_ROOT
APP_DATA_DIR = os.path.join(BASE_ROOT, "Trading_Data_Transformation")

PATHS = {
    "PROJECT_ROOT": PROJECT_DIR,
    "RAW_PR": os.path.join(PROJECT_DIR, "raw", "pr"),
    "RAW_CA": os.path.join(PROJECT_DIR, "raw", "ca"),
    "RAW_FO": os.path.join(PROJECT_DIR, "raw", "fo"),
    "CLEAN_CA": os.path.join(PROJECT_DIR, "clean"),
    "STOCK_WISE_PR": os.path.join(DATA_DIR, "stock_wise"),
    "STOCK_WISE_FO": os.path.join(DATA_DIR, "adjusted_futures_data_final"),
    "SECTOR_MAP": os.path.join(APP_DATA_DIR, "step3_fo_to_fo_pair", "data", "sector", "sector_master_map.csv"),
    "SECTOR_OUTPUT": os.path.join(DATA_DIR, "sec_wise_futures_data"),
    "REMAINING_CA": os.path.join(APP_DATA_DIR, "automation", "remaning_ca"),
    "LOG_FILE": os.path.join(APP_DATA_DIR, "automation", "logs", "Futures_Skipped_CA_Log.csv"),
}

def remove_folder(path_to_remove, log_func=print):
    if os.path.exists(path_to_remove):
        try:
            shutil.rmtree(path_to_remove)
            log_func(f"🗑️  Deleted old folder: {path_to_remove}")
        except Exception as e:
            log_func(f"⚠️  Error deleting {path_to_remove}: {e}")

def ensure_directories(log_func=print):
    exclude_keys = ["SECTOR_MAP", "LOG_FILE", "PROJECT_ROOT"]
    dirs_to_create = [v for k, v in PATHS.items() if k not in exclude_keys]
    dirs_to_create.append(os.path.dirname(PATHS["LOG_FILE"]))
    for folder in dirs_to_create:
        os.makedirs(folder, exist_ok=True)

# --- MODIFIED MAIN FUNCTION ---
def main(status_callback=None):
    """
    Returns: (status_message, is_data_updated_boolean)
    """
    def log(message, is_success=False):
        if status_callback:
            status_callback(message, is_success)
        else:
            print(message)

    # 1. Calculate Dates
    log("--- Checking Data Freshness ---")
    try:
        last_cash_date = get_last_available_date(ADJUSTED_FOLDER=PATHS["STOCK_WISE_PR"])
        last_fo_date = get_last_available_date_futures(ADJUSTED_FOLDER=PATHS["STOCK_WISE_FO"])
    except Exception as e:
        log(f"Error reading dates: {e}")
        return f"Error reading dates: {e}", False

    start_date_cash = last_cash_date + timedelta(days=1)
    start_date_futures = last_fo_date + timedelta(days=1)
    end_date = datetime.now()

    cash_gap = (end_date - start_date_cash).days
    
    # Logic: If gap is 0 or 1, data is fresh enough
    if cash_gap <= -1:
        msg = f"✅ Data is up to date! (Last Date: {last_cash_date.date()})"
        log(msg, is_success=True)
        return msg, False # False means "No update ran"

    log(f"🚀 Data is old ({cash_gap} days gap). Starting Update...", is_success=False)

    # --- PIPELINE START ---
    try:
        log("Step 1/7: Cleaning staging area...")
        remove_folder(PATHS["PROJECT_ROOT"], log_func=log)
        
        log("Step 2/7: Preparing directories...")
        ensure_directories(log_func=log)

        log(f"Step 3/7: Fetching data...")
        fetch_all_data(start_date_cash, start_date_futures, end_date, PATHS["RAW_PR"], PATHS["RAW_CA"], PATHS["RAW_FO"])

        log("Step 4/7: Cleaning Corporate Actions...")
        clean_ca_data(PATHS["RAW_CA"], PATHS["CLEAN_CA"])

        log("Step 5/7: Appending Data...")
        start_append_engine(PATHS["RAW_PR"], PATHS["RAW_FO"], PATHS["STOCK_WISE_PR"], PATHS["STOCK_WISE_FO"])

        log("Step 6/7: Adjusting Futures...")
        # run_engine(PATHS["STOCK_WISE_PR"], PATHS["CLEAN_CA"], PATHS["STOCK_WISE_FO"], PATHS["REMAINING_CA"], PATHS["LOG_FILE"])
        run_engine()

        log("Step 7/7: Organizing Sectors...")
        remove_folder(PATHS["SECTOR_OUTPUT"], log_func=log)
        harmonize_futures_safely()
        organize_stocks_by_sector(PATHS["SECTOR_MAP"], PATHS["STOCK_WISE_FO"], PATHS["SECTOR_OUTPUT"])
        
        success_msg = "✅ Data Update Pipeline Completed Successfully!"
        log(success_msg, is_success=True)
        return success_msg, True

    except Exception as e:
        err_msg = f"❌ Pipeline Failed: {str(e)}"
        log(err_msg)
        return err_msg, False

if __name__ == "__main__":
    main()
    # for k,p in PATHS.items():
    #     print(f"{k}: {p}")