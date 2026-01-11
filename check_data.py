import pandas as pd
import numpy as np
import os

def find_anomalies(root_dir, output_csv="anomalies_report.csv"):
    """
    Scans CSV files in root_dir for data anomalies.
    1. Date Gaps: Checks if gap between trading days is > 10 days.
    2. Price Anomalies: Checks if (Prev_Close / Today_Close) > 1.4.
    """
    
    anomalies = []
    print(f"Scanning files in: {root_dir}")
    
    files_processed = 0
    
    # Walk through the directory and subdirectories
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.lower().endswith(".csv"):
                files_processed += 1
                file_path = os.path.join(dirpath, file)
                
                try:
                    # Read CSV
                    df = pd.read_csv(file_path)
                    
                    # Clean column names (remove extra spaces)
                    df.columns = [c.strip() for c in df.columns]
                    
                    # Check for essential columns
                    if 'TIMESTAMP' not in df.columns or 'CLOSE_PRICE' not in df.columns:
                        continue
                        
                    # Standardize Date format
                    df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')
                    # df = df.dropna(subset=['TIMESTAMP'])
                    
                    # Filter for Futures Stock (FUTSTK) if INSTRUMENT column exists
                    # This avoids processing Options data if present in same file
                    if 'INSTRUMENT' in df.columns:
                        df = df[df['INSTRUMENT'] == 'FUTSTK']
                    
                    if df.empty:
                        continue
                    
                    # --- CHECK 1: DATE CONSISTENCY ---
                    # Get unique dates sorted
                    # unique_dates = df['TIMESTAMP'].sort_values().unique()
                    
                    # if len(unique_dates) > 1:
                    #     # Calculate difference in days
                    #     date_diffs = np.diff(unique_dates).astype('timedelta64[D]').astype(int)
                        
                    #     # Define "Huge Gap" threshold (e.g., > 10 days)
                    #     gap_threshold = 10 
                    #     gap_indices = np.where(date_diffs > gap_threshold)[0]
                        
                    #     for idx in gap_indices:
                    #         start_date = unique_dates[idx]
                    #         end_date = unique_dates[idx+1]
                    #         days_gap = date_diffs[idx]
                            
                    #         anomalies.append({
                    #             'File': file,
                    #             'Symbol': df['SYMBOL'].iloc[0] if 'SYMBOL' in df.columns else file,
                    #             'Type': 'Huge Date Gap',
                    #             'Date': f"{pd.to_datetime(start_date).date()} to {pd.to_datetime(end_date).date()}",
                    #             'Details': f"Gap of {days_gap} days"
                    #         })
                            
                    # --- CHECK 2: VALUE CONSISTENCY (Corporate Actions) ---
                    # To check price continuity, we need a single continuous series.
                    # We pick the "Near Month" contract for each day (min Expiry Date).
                    
                    if 'EXP_DATE' in df.columns:
                        df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'], errors='coerce')
                        # Sort by Date then Expiry to pick nearest expiry first
                        df_sorted = df.sort_values(['TIMESTAMP', 'EXP_DATE'])
                        # Group by date and take the first row (Near Month Future)
                        daily_df = df_sorted.groupby('TIMESTAMP').first().reset_index()
                    else:
                        # Fallback if no expiry column
                        daily_df = df.sort_values('TIMESTAMP')
                    
                    # Sort by date again to ensure order for shift()
                    daily_df = daily_df.sort_values('TIMESTAMP')
                    
                    # Calculate Ratio: Previous Close / Current Close
                    daily_df['PREV_CLOSE'] = daily_df['CLOSE_PRICE'].shift(1)
                    daily_df['RATIO'] = daily_df['PREV_CLOSE'] / daily_df['CLOSE_PRICE']
                    
                    # Threshold defined by user: Ratio > 1.4 (Implies huge price drop/split)
                    anomaly_df = daily_df[daily_df['RATIO'] > 1.4]
                    
                    for _, row in anomaly_df.iterrows():
                        anomalies.append({
                            'File': file,
                            'Symbol': row['SYMBOL'] if 'SYMBOL' in df.columns else file,
                            'Type': 'Price Anomaly (Split/Unadjusted)',
                            'Date': row['TIMESTAMP'].date(),
                            'Details': f"Ratio: {row['RATIO']:.2f} (Prev: {row['PREV_CLOSE']}, Curr: {row['CLOSE_PRICE']})"
                        })
                        
                except Exception as e:
                    print(f"Error processing {file}: {e}")
                    anomalies.append({
                        'File': file,
                        'Symbol': 'ERROR',
                        'Type': 'Processing Error',
                        'Date': '-',
                        'Details': str(e)
                    })

    # Save to CSV
    if anomalies:
        result_df = pd.DataFrame(anomalies)
        result_df.to_csv(output_csv, index=False)
        print(f"\nProcessing Complete. {files_processed} files scanned.")
        print(f"Found {len(anomalies)} anomalies.")
        print(f"Results saved to: {os.path.abspath(output_csv)}")
    else:
        print("\nProcessing Complete. No anomalies found.")

# --- CONFIGURATION ---
# PASTE YOUR FOLDER PATH BELOW
folder_path = r"C:\Users\91702\Documents\programming\all_cash_stocks\Trading\sec_wise_futures_data"
# folder_path = r"C:\Users\91702\Documents\programming\app\data\sec_wise_futures_data"

if __name__ == "__main__":
    if os.path.exists(folder_path):
        find_anomalies(folder_path)
    else:
        print(f"Error: The path '{folder_path}' does not exist.")