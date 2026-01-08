

import pandas as pd
import os
import shutil  # Added for efficient file copying

# --- CONFIGURATION: PATHS ---


def organize_stocks_by_sector(SECTOR_MAP_PATH,SOURCE_DIR,OUTPUT_DIR):
    # 1. Create Base Output Directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created base directory: {OUTPUT_DIR}")

    # 2. Load the Sector Master Map
    print("Loading Sector Map...")
    try:
        sector_df = pd.read_csv(SECTOR_MAP_PATH)
        sector_df.columns = sector_df.columns.str.strip()
        
        # Identify the correct column for Sector/Industry
        sector_col_name = 'Industry' if 'Industry' in sector_df.columns else 'Sector'
        
        # Create Dictionary: {'RELIANCE': 'Oil & Gas', 'TCS': 'IT Services'}
        sector_dict = dict(zip(sector_df['Symbol'].str.upper().str.strip(), 
                               sector_df[sector_col_name].str.strip()))
        
        print(f"Sector Map Loaded. Found {len(sector_dict)} symbols.")
        
    except Exception as e:
        print(f"CRITICAL ERROR loading Sector Map: {e}")
        return

    # 3. Process Files
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.csv')]
    print(f"Found {len(files)} stock files. Starting organization...")

    success_count = 0
    missing_sector_count = 0

    for filename in files:
        try:
            # Derive Symbol
            symbol = filename.replace('.csv', '').upper().strip()
            
            # Lookup Sector
            raw_sector = sector_dict.get(symbol, "Unknown_Sector")
            
            if raw_sector == "Unknown_Sector":
                missing_sector_count += 1
                # Optional: Print warning only for unknown stocks
                # print(f"Sector unknown for: {symbol}")

            # SANITIZE FOLDER NAME (Important!)
            # Replaces characters like '/' which are invalid in folder names (e.g. "Oil & Gas" is fine, but "Auto / Ancillary" needs fix)
            safe_sector_name = raw_sector.replace('/', '-').replace('\\', '-').strip()
            
            # Define Sector Folder Path
            sector_folder_path = os.path.join(OUTPUT_DIR, safe_sector_name)
            
            # Create Sector Folder if it doesn't exist
            if not os.path.exists(sector_folder_path):
                os.makedirs(sector_folder_path)
            
            # Define Source and Destination Paths
            source_file = os.path.join(SOURCE_DIR, filename)
            destination_file = os.path.join(sector_folder_path, filename)
            
            # COPY the file (Faster and safer than read_csv -> to_csv if no data change is needed)
            shutil.copy2(source_file, destination_file)
            
            success_count += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # 4. Final Report
    print("-" * 30)
    print("ORGANIZATION COMPLETE")
    print(f"Total Files Organized: {success_count}")
    print(f"Files placed in 'Unknown_Sector': {missing_sector_count}")
    print(f"Root Output Directory: {OUTPUT_DIR}")

# if __name__ == "__main__":
#     organize_stocks_by_sector()