import pandas as pd
import os
import logging

# ================= CONFIGURATION =================
# Jahan tumhari current CSV files rakhi hain
INPUT_DIR = r"C:\Users\91702\Documents\programming\all_cash_stocks\Trading\Futures_data"

# Jahan nayi files save hongi (Safety ke liye alag folder rakha hai)
OUTPUT_DIR = r"C:\Users\91702\Documents\programming\all_cash_stocks\Trading\Futures_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(message)s")

# ================= MAPPING DICTIONARY =================
# Left side: Jo abhi file mein hai
# Right side: Jo tumhe chahiye
COLUMN_MAPPING = {
    "TIMESTAMP": "TIMESTAMP",
    "EXP_DATE": "EXP_DATE",   # Check krna agar tumhare data me EXPIRY_DT hai to yahan change kr dena
    "SYMBOL": "SYMBOL",
    "INSTRUMENT": "INSTRUMENT",
    "OPEN": "OPEN_PRICE",
    "HIGH": "HI_PRICE",
    "LOW": "LO_PRICE",
    "CLOSE": "CLOSE_PRICE",
    "OPEN_INT": "OPEN_INT*",  # Ye star wala ban jayega
    "TURNOVER": "TRD_VAL",
    "VOLUME": "TRD_QTY",
    "CONTRACTS": "NO_OF_CONT",
    "TRADES": "NO_OF_TRADE"
}

# List of final columns order (jo tumhe chahiye)
FINAL_ORDER = [
    "TIMESTAMP", "EXP_DATE", "SYMBOL", "INSTRUMENT", 
    "OPEN_PRICE", "HI_PRICE", "LO_PRICE", "CLOSE_PRICE", 
    "OPEN_INT*", "TRD_VAL", "TRD_QTY", "NO_OF_CONT", 
    "NO_OF_TRADE", "OPEN_INT"  # Last me wapis OPEN_INT manga hai tumne
]

def rename_columns():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    print(f"🚀 Starting renaming process for {len(files)} files...")

    for file in files:
        in_path = os.path.join(INPUT_DIR, file)
        out_path = os.path.join(OUTPUT_DIR, file)

        try:
            # 1. Read Data
            df = pd.read_csv(in_path)
            
            # Columns clean kar lete hain (spaces remove)
            df.columns = df.columns.str.upper().str.strip()

            # *Note on Expiry:* Agar tumhare purane data me column ka naam 'EXPIRY_DT' hai
            # aur tumhe 'EXP_DATE' chahiye, to pehle use rename map me adjust krna padega.
            if "EXPIRY_DT" in df.columns:
                df.rename(columns={"EXPIRY_DT": "EXP_DATE"}, inplace=True)

            # 2. Rename Columns based on Mapping
            # (Jo columns map me nahi hain wo waise hi rahenge)
            df.rename(columns=COLUMN_MAPPING, inplace=True)

            # 3. Handle Special Case: Duplicate OPEN_INT
            # Abhi hamare paas 'OPEN_INT*' hai (kyunki rename ho gaya).
            # Tumhe last me normal 'OPEN_INT' bhi chahiye.
            if "OPEN_INT*" in df.columns:
                df["OPEN_INT"] = df["OPEN_INT*"] # Copy data to new column

            # 4. Reorder columns strictly as per requirement
            # Sirf wahi columns rakhenge jo FINAL_ORDER me hain
            # (Agar koi column missing hua to error avoid krne ke liye check lagayenge)
            available_cols = [c for c in FINAL_ORDER if c in df.columns]
            df = df[available_cols]

            # 5. Save
            df.to_csv(out_path, index=False)
            print(f"✅ Renamed: {file}")

        except Exception as e:
            print(f"❌ Failed {file}: {e}")

    print("\n🎉 All files processed! Check 'Futures_Renamed' folder.")

if __name__ == "__main__":
    rename_columns()