import requests
import zipfile
import io
import os
import time
import json
import glob
import pandas as pd
from datetime import datetime, timedelta
import multiprocessing  
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Connection": "keep-alive"
}

# ==========================================
# 1️⃣ PROCESS 1: PR FILES (Network Bound)
# ==========================================
def task_fetch_pr(start_date, end_date,RAW_PR):
    print(f"🔹 [PR Process {os.getpid()}] Started...")
    current = start_date 
    
    while current <= end_date:
        if current.weekday() >= 5: # Skip Weekends
            current += timedelta(days=1)
            continue

        d = current.strftime("%d%m%y")
        pr_path = os.path.join(RAW_PR, f"Pr{d}.csv")

        if os.path.exists(pr_path):
            current += timedelta(days=1)
            continue

        url = f"https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR{d}.zip"
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    pd_file = next(f for f in z.namelist() if f.lower().startswith("pd"))
                    with z.open(pd_file) as f:
                        open(pr_path, "wb").write(f.read())
                print(f"✅ [PR] Done: {current.date()}")
        except Exception as e:
            print(f"⚠️ [PR] Error {current.date()}: {e}")

        current += timedelta(days=1)
    print("🏁 [PR Process] Completed")

# ==========================================
# 2️⃣ PROCESS 2: CA FILES (Selenium/Browser)
# ==========================================
def init_driver():
    # Driver process ke andar hi initialize karna padta hai
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    # options.add_argument("--headless") # Uncomment if you don't want to see browser
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def task_fetch_ca(start_date = datetime.strptime("07-01-2026", "%d-%m-%Y"), end_date = datetime.strptime("08-01-2026", "%d-%m-%Y"), RAW_CA=None):
    # Resolve repo-relative default
    if RAW_CA is None:
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
        RAW_CA = os.path.join(REPO_ROOT, "set", "raw", "ca")
    print(f"🔹 [CA Process {os.getpid()}] Started (Browser Opening)...")
    driver = init_driver()
    
    try:
        driver.get("https://www.nseindia.com")
        time.sleep(5) 

        current_start = start_date 

        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=364), end_date)
            from_d = current_start.strftime("%d-%m-%Y")
            to_d = current_end.strftime("%d-%m-%Y")
            
            file_name = f"Corporate_Actions_{from_d}_to_{to_d}.csv"
            save_path = os.path.join(RAW_CA, file_name)

            if os.path.exists(save_path):
                current_start = current_end + timedelta(days=1)
                continue

            api_url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_d}&to_date={to_d}"
            driver.get(api_url)
            time.sleep(3)
            
            try:
                content = driver.find_element("tag name", "body").text
                data = json.loads(content)
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    if "series" in df.columns:
                        df = df[df["series"] == "EQ"]
                    if not df.empty:
                        df.to_csv(save_path, index=False)
                        print(f"✅ [CA] Saved: {from_d} to {to_d}")
            except:
                pass

            current_start = current_end + timedelta(days=1)
            time.sleep(2)

    except Exception as e:
        print(f"⚠️ [CA] Critical Error: {e}")
    finally:
        driver.quit()
        print("🏁 [CA Process] Completed")

# ==========================================
# 3️⃣ PROCESS 3: FO FETCH + HEAVY PANDAS
# ==========================================
def task_fo_complete(start_date, end_date,RAW_FO_CSV):
    print(f"🔹 [FO Process {os.getpid()}] Started (Download + Processing)...")
    
    # --- PART A: DOWNLOADING ---
    current = start_date
    while current <= end_date:
        d = current.strftime("%d%m%Y")
        url = f"https://nsearchives.nseindia.com/archives/fo/mkt/fo{d}.zip"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    z.extractall(RAW_FO_CSV)
                print(f"✅ [FO] Downloaded: {d}")
        except:
            pass
        current += timedelta(days=1)
            
    print("🏁 [FO Process] All Done")


# ==========================================
# 🚀 MAIN ENTRY POINT
# ==========================================

def fetch_all_data(start_date_for_cash,start_date_for_futures,end_date,RAW_PR, RAW_CA, RAW_FO_CSV):
    multiprocessing.freeze_support() 
    
    print(f"🚀 Launching 3 Parallel Processes for {start_date_for_cash.date()} to {end_date.date()}...\n")
    print(f"🚀 Launching 3 Parallel Processes for {start_date_for_futures.date()} to {end_date.date()}...\n")

    # Creating separate PROCESSES (not threads)
    p1 = multiprocessing.Process(target=task_fetch_pr, args=(start_date_for_cash, end_date, RAW_PR))
    p2 = multiprocessing.Process(target=task_fetch_ca, args=(start_date_for_cash, end_date,RAW_CA))
    p3 = multiprocessing.Process(target=task_fo_complete, args=(start_date_for_futures, end_date,RAW_FO_CSV))

    # Starting them
    p1.start()
    p2.start()
    p3.start()

    # Waiting for them to finish
    p1.join()
    p2.join()
    p3.join()

    print("\n🎉🎉🎉 SARA KAAM KHATAM! (Everything Synced) 🎉🎉🎉")

if __name__ == "__main__":
    # Windows mein multiprocessing ke liye ye line zaroori hai
#    fetch_all_data()
    task_fetch_ca()
    # task_fo_complete(datetime.strptime("07-01-2026", "%d-%m-%Y"), datetime.strptime("08-01-2026", "%d-%m-%Y"),r"C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\fo")
    # task_fetch_pr(datetime.strptime("02-01-2026", "%d-%m-%Y"), datetime.strptime("08-01-2026", "%d-%m-%Y"),r"C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\pr")