import os
import pandas as pd

# Use repository-relative paths so this module works when run from the Trading folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
ADJUSTED_FOLDER_CASH = os.path.join(REPO_ROOT, "stock_wise")
ADJUSTED_FOLDER_FUTURES = os.path.join(REPO_ROOT, "adjusted_futures_data_final")

stock = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'HDFC', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK']

def get_last_available_date(ADJUSTED_FOLDER):
    last_dates = []

    for stk in stock:
        path = os.path.join(ADJUSTED_FOLDER, f"{stk}.csv")

        try:
            df = pd.read_csv(path)
        except:
            continue

        if 'Date' in df.columns:
            d = pd.to_datetime(df['Date'], errors='coerce')
            last_dates.append(d.max())

    return max(last_dates)

def get_last_available_date_futures(ADJUSTED_FOLDER):
    last_dates = []

    path = os.path.join(ADJUSTED_FOLDER, f"NIFTY.csv")

    try:
        df = pd.read_csv(path)
    except:
        return print("NIFTY.csv not found")

    
    if 'TIMESTAMP' in df.columns:
        d = pd.to_datetime(df['TIMESTAMP'], errors='coerce')
        last_dates.append(d.max())

    return max(last_dates)

if __name__ == "__main__":

    data = get_last_available_date(ADJUSTED_FOLDER=ADJUSTED_FOLDER_CASH)
    print("Last available date in adjusted data for cash:", data)
    data = get_last_available_date_futures(ADJUSTED_FOLDER=ADJUSTED_FOLDER_FUTURES)
    print("Last available date in adjusted data for futures:", data)