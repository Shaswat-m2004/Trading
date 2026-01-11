import pandas as pd
import os

def manual_futures_adjustment():
    print("=== MANUAL FUTURES DATA ADJUSTMENT TOOL ===")
    
    # 1. User Inputs
    file_path = "C:\\Users\\91702\\Documents\\programming\\all_cash_stocks\\Trading\\adjusted_futures_data_final\\INFIBEAM.csv".strip('"')
    
    if not os.path.exists(file_path):
        print("❌ Error: File nahi mili!")
        return

    date_str = "2017-08-31".strip('"')
    
    print("\n[Factor Note: Agar Price 11.35 se 7.4 hua hai, to Factor 1.53 daalein]")
    try:
        factor = 9.78
    except ValueError:
        print("❌ Error: Factor number hona chahiye.")
        return

    # 2. Read Data
    try:
        print("\nReading File...")
        df = pd.read_csv(file_path)
        
        # Clean Headers (Remove spaces)
        df.columns = df.columns.str.strip().str.upper()
        
        # Identify Columns from your sample
        date_col = 'TIMESTAMP' if 'TIMESTAMP' in df.columns else 'DATE'
        
        # Price Columns to DIVIDE
        price_cols = [c for c in ['OPEN_PRICE', 'HI_PRICE', 'LO_PRICE', 'CLOSE_PRICE', 'OPEN', 'HIGH', 'LOW', 'CLOSE'] if c in df.columns]
        
        # Quantity Columns to MULTIPLY (Volume, OI)
        # Note: 'OPEN_INT*' ko bhi handle karega
        qty_cols = [c for c in ['TRD_QTY', 'OPEN_INT', 'OPEN_INT*', 'VOLUME', 'OI', 'QUANTITY'] if c in df.columns]

        if not date_col:
            print("❌ Error: 'TIMESTAMP' ya 'DATE' column nahi mila.")
            return

        # Date Convert
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        cutoff_date = pd.to_datetime(date_str)
        
        if pd.isna(cutoff_date):
            print("❌ Error: Date format galat hai.")
            return

        # 3. Apply Logic
        # Filter: Dates STRICTLY BEFORE input date
        mask = df[date_col] < cutoff_date
        affected_rows = mask.sum()
        
        if affected_rows == 0:
            print(f"⚠️ Warning: {date_str} se pehle koi data nahi mila.")
            return

        print(f"\nAdjusting {affected_rows} rows before {date_str}...")
        
        # Logic: Price kam karna hai (Divide), Quantity badhani hai (Multiply)
        
        # A. Adjust Prices
        for col in price_cols:
            # Divide by factor and round to 2 decimals
            df.loc[mask, col] = (df.loc[mask, col] / factor).round(2)
            
        # B. Adjust Quantities
        for col in qty_cols:
            # Multiply by factor and round to nearest integer
            # fillna(0) lagaya taaki agar koi blank ho to error na aaye
            df.loc[mask, col] = (df.loc[mask, col] * factor).fillna(0).round(0).astype('int64')

        # 4. Save File
        # Overwrite same file or create new? Let's create new for safety first.
        output_path = file_path
        
        # Agar aapko same file replace karni hai, to niche wali line uncomment karein:
        # output_path = file_path 
        
        df.to_csv(output_path, index=False)
        
        print("\n✅ PROCESS COMPLETE!")
        print(f"Modified Columns (Price / {factor}): {price_cols}")
        print(f"Modified Columns (Qty * {factor}): {qty_cols}")
        print(f"File Saved at: {output_path}")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    manual_futures_adjustment()