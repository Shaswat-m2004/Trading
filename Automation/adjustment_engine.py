# # import os
# # import re
# # import pandas as pd
# # from datetime import datetime

# # # ================= PATHS =================
# # PRICE_DIR = r"C:\Users\91702\Documents\programming\app\data\NSE500_Adjusted_Data"
# # CLEAN_CA_FOLDER = r"C:\Users\91702\Documents\programming\all_cash_stocks\set\clean\DCMSRIND.csv"
# # REMAINING_CA_DIR = r"C:\Users\91702\Documents\programming\Trading_Data_Transformation\automation\remaning_ca"

# # os.makedirs(REMAINING_CA_DIR, exist_ok=True)

# # # ================= NORMALIZATION =================

# # def get_latest_ca_file(folder):
# #     pattern = re.compile(r"corporate_action_data_(\d+)\.csv")
# #     latest_file = None
# #     max_num = -1

# #     for f in os.listdir(folder):
# #         match = pattern.match(f)
# #         if match:
# #             num = int(match.group(1))
# #             if num > max_num:
# #                 max_num = num
# #                 latest_file = f

# #     return os.path.join(folder, latest_file) if latest_file else None


# # def normalize_subject(s):
# #     s = str(s).lower()

# #     replacements = {
# #         'spl div': 'special dividend',
# #         'sd': 'special dividend',
# #         'dvd': 'dividend',
# #         'div': 'dividend',
# #         'spl': 'split',
# #         'sp ': 'split ',
# #         'subdiv': 'split',
# #         'bon': 'bonus',
# #         'bns': 'bonus',
# #         'rts': 'rights'
# #     }

# #     for k, v in replacements.items():
# #         s = s.replace(k, v)

# #     return s


# # # ================= PARSERS =================

# # def parse_rights(subject, face_val):
# #     parts = re.split(r'\/|&|\band\b', subject, flags=re.IGNORECASE)
# #     total_new, total_cash = 0.0, 0.0

# #     for part in parts:
# #         ratio = re.search(r'(\d+)\s*:\s*(\d+)', part)
# #         premium = re.search(r'(?:rs\.?|re\.?)\s*(\d+(?:\.\d+)?)', part, re.I)

# #         if ratio:
# #             new, held = map(float, ratio.groups())
# #             if held == 0:
# #                 continue
# #             price = face_val + (float(premium.group(1)) if premium else 0.0)
# #             frac = new / held
# #             total_new += frac
# #             total_cash += frac * price

# #     return (total_new, total_cash) if total_new > 0 else (None, None)


# # def identify_action(subject, face_val):
# #     s = normalize_subject(subject)

# #     if any(x in s for x in ['demerger', 'scheme', 'amalgamation', 'nclt']):
# #         return 'STOP', None

# #     if 'split' in s:
# #         m = re.search(r'from.*?(?:rs|re)\s*(\d+).*?to.*?(?:rs|re)\s*(\d+)', s)
# #         if m:
# #             old, new = max(map(float, m.groups())), min(map(float, m.groups()))
# #             return 'SPLIT', new / old

# #     if 'bonus' in s:
# #         m = re.search(r'(\d+)\s*:\s*(\d+)', s)
# #         if m:
# #             new, held = map(float, m.groups())
# #             return 'BONUS', held / (new + held)

# #     if 'rights' in s:
# #         return 'RIGHTS', parse_rights(subject, face_val)

# #     if 'dividend' in s:
# #         amounts = re.findall(r'(?:rs|re)\s*(\d+(?:\.\d+)?)', s)
# #         return 'DIVIDEND', sum(map(float, amounts)) if amounts else None

# #     return 'IGNORE', None


# # # ================= MAIN ENGINE =================

# # def run_adjustment_engine():
# #     print("🚀 Adjustment Engine Started")

# #     skipped_actions = []

# #     try:
# #         ca_file = get_latest_ca_file(CLEAN_CA_FOLDER)

# #         if not ca_file:
# #             print("⚠️ No cleaned corporate action file found")
# #             return

# #         try:
# #             ca = pd.read_csv(ca_file)
# #             print(f"📄 Using CA file: {os.path.basename(ca_file)}")
# #         except Exception:
# #             print("❌ Failed to read CA file")
# #             return

# #     except Exception:
# #         ca = pd.DataFrame()

# #     if ca.empty:
# #         print("⚠️ Corporate Action file empty or missing")
# #         today_folder = os.path.join(REMAINING_CA_DIR, datetime.today().strftime("%Y-%m-%d"))
# #         os.makedirs(today_folder, exist_ok=True)
# #         return

# #     ca.columns = ca.columns.str.lower()
# #     # normalize symbol values for case-insensitive matching
# #     if 'symbol' in ca.columns:
# #         ca['symbol'] = ca['symbol'].astype(str).str.lower()
# #     ca['exdate'] = pd.to_datetime(ca.get('exdate'), errors='coerce')
# #     ca = ca.dropna(subset=['exdate']).sort_values('exdate', ascending=False)

# #     for price_file in os.listdir(PRICE_DIR):
# #         if not price_file.endswith(".csv"):
# #             continue

# #         symbol = price_file.replace(".csv", "")
# #         price_path = os.path.join(PRICE_DIR, price_file)

# #         df = pd.read_csv(price_path)

# #         # Keep original column casing to restore later
# #         original_cols_map = {col.lower(): col for col in df.columns}
# #         # Normalize columns to lowercase for case-insensitive processing
# #         df.columns = [c.lower() for c in df.columns]

# #         # Require date column (case-insensitive)
# #         if 'date' not in df.columns:
# #             continue

# #         df['date'] = pd.to_datetime(df['date'], errors='coerce')
# #         df = df.dropna(subset=['date']).sort_values('date').reset_index(drop=True)

# #         # symbol matching: compare lowercase symbol names
# #         original_symbol = symbol
# #         symbol = symbol.lower()
# #         ca_sym = ca[ca['symbol'] == symbol]

# #         for _, row in ca_sym.iterrows():
# #             exdate = row['exdate']
# #             subject = row['subject']
# #             face_val = float(row['faceval']) if pd.notna(row.get('faceval')) else 10

# #             hist_mask = df['date'] < exdate
# #             if not hist_mask.any():
# #                 skipped_actions.append(row)
# #                 continue

# #             # Use lowercase 'close' column
# #             if 'close' not in df.columns:
# #                 skipped_actions.append(row)
# #                 continue

# #             cum_close = df.loc[hist_mask].iloc[-1]['close']
# #             action, param = identify_action(subject, face_val)

# #             factor = 1.0

# #             if action == 'STOP':
# #                 skipped_actions.append(row)
# #                 break

# #             if action in ['SPLIT', 'BONUS'] and param:
# #                 factor = param

# #             elif action == 'DIVIDEND' and param and cum_close > 0:
# #                 factor = (cum_close - param) / cum_close

# #             elif action == 'RIGHTS' and param and param[0] is not None:
# #                 new, cash = param
# #                 terp = (cum_close + cash) / (1 + new)
# #                 factor = terp / cum_close
# #             else:
# #                 skipped_actions.append(row)
# #                 continue

# #             if factor <= 0 or factor == 1:
# #                 skipped_actions.append(row)
# #                 continue

# #             for col in ['open', 'high', 'low', 'close', 'prev close']:
# #                 if col in df.columns:
# #                     df.loc[hist_mask, col] *= factor

# #             if action in ['SPLIT', 'BONUS'] and 'volume' in df.columns:
# #                 df.loc[hist_mask, 'volume'] /= factor

# #             ex_mask = df['date'] == exdate
# #             if ex_mask.any() and 'prev close' in df.columns:
# #                 df.loc[ex_mask, 'prev close'] *= factor

# #         # Restore original column casing where possible
# #         df.columns = [original_cols_map.get(c, c) for c in df.columns]
# #         df.round(2).to_csv(price_path, index=False)
# #         print(f"✅ Adjusted: {original_symbol}")

# #     # ===== SAVE SKIPPED CA =====
# #     today = datetime.today().strftime("%Y-%m-%d")

# #     if skipped_actions:
# #         out_file = os.path.join(REMAINING_CA_DIR, f"{today}.csv")
# #         pd.DataFrame(skipped_actions).to_csv(out_file, index=False)
# #         print(f"📌 Skipped CA saved: {out_file}")
# #     else:
# #         empty_dir = os.path.join(REMAINING_CA_DIR, today)
# #         os.makedirs(empty_dir, exist_ok=True)
# #         print("📂 No skipped CA — empty folder created")

# #     print("🎉 Adjustment Engine Completed")


# # if __name__ == "__main__":
# #     run_adjustment_engine()




# import os
# import re
# import pandas as pd
# from datetime import datetime
# import multiprocessing

# # ================= PATHS =================

# BASE_ROOT = r"C:\Users\91702\Documents\programming"
# PROJECT_DIR = os.path.join(BASE_ROOT, "all_cash_stocks", "set")
# DATA_DIR = os.path.join(BASE_ROOT, "all_cash_stocks")
# APP_DATA_DIR = os.path.join(BASE_ROOT, "Trading_Data_Transformation")

# PATHS = {
#     "PROJECT_ROOT": PROJECT_DIR,
#     "RAW_PR": os.path.join(PROJECT_DIR, "raw", "pr"),
#     "RAW_CA": os.path.join(PROJECT_DIR, "raw", "ca"),
#     "RAW_FO": os.path.join(PROJECT_DIR, "raw", "fo"),
#     "CLEAN_CA": os.path.join(PROJECT_DIR, "clean"),
#     "STOCK_WISE_PR": os.path.join(DATA_DIR, "stock_wise"),
#     "STOCK_WISE_FO": os.path.join(DATA_DIR, "adjusted_futures_data_final"),
#     "SECTOR_MAP": os.path.join(APP_DATA_DIR, "step3_fo_to_fo_pair", "data", "sector", "sector_master_map.csv"),
#     "SECTOR_OUTPUT": os.path.join(DATA_DIR, "sec_wise_futures_data"),
#     "REMAINING_CA": os.path.join(APP_DATA_DIR, "automation", "remaning_ca"),
#     "LOG_FILE": os.path.join(APP_DATA_DIR, "automation", "logs", "Futures_Skipped_CA_Log.csv"),
# }



# # ================= NORMALIZATION =================

# def get_latest_ca_file(folder):
#     pattern = re.compile(r"corporate_action_data_(\d+)\.csv")
#     latest_file = None
#     max_num = -1

#     for f in os.listdir(folder):
#         match = pattern.match(f)
#         if match:
#             num = int(match.group(1))
#             if num > max_num:
#                 max_num = num
#                 latest_file = f

#     return os.path.join(folder, latest_file) if latest_file else None


# def normalize_subject(s):
#     s = str(s).lower()

#     replacements = {
#         'spl div': 'special dividend',
#         'sd': 'special dividend',
#         'dvd': 'dividend',
#         'div': 'dividend',
#         'spl': 'split',
#         'sp ': 'split ',
#         'subdiv': 'split',
#         'bon': 'bonus',
#         'bns': 'bonus',
#         'rts': 'rights'
#     }

#     for k, v in replacements.items():
#         s = s.replace(k, v)

#     return s


# # ================= PARSERS =================

# def parse_rights(subject, face_val):
#     parts = re.split(r'\/|&|\band\b', subject, flags=re.IGNORECASE)
#     total_new, total_cash = 0.0, 0.0

#     for part in parts:
#         ratio = re.search(r'(\d+)\s*:\s*(\d+)', part)
#         premium = re.search(r'(?:rs\.?|re\.?)\s*(\d+(?:\.\d+)?)', part, re.I)

#         if ratio:
#             new, held = map(float, ratio.groups())
#             if held == 0:
#                 continue
#             price = face_val + (float(premium.group(1)) if premium else 0.0)
#             frac = new / held
#             total_new += frac
#             total_cash += frac * price

#     return (total_new, total_cash) if total_new > 0 else (None, None)


# # def identify_action(subject, face_val):
# #     s = normalize_subject(subject)

# #     if any(x in s for x in ['demerger', 'scheme', 'amalgamation', 'nclt']):
# #         return 'STOP', None

# #     if 'split' in s:
# #         m = re.search(r'from.*?(?:rs|re)\s*(\d+).*?to.*?(?:rs|re)\s*(\d+)', s)
# #         if m:
# #             old, new = max(map(float, m.groups())), min(map(float, m.groups()))
# #             return 'SPLIT', new / old

# #     if 'bonus' in s:
# #         m = re.search(r'(\d+)\s*:\s*(\d+)', s)
# #         if m:
# #             new, held = map(float, m.groups())
# #             return 'BONUS', held / (new + held)

# #     if 'rights' in s:
# #         return 'RIGHTS', parse_rights(subject, face_val)

# #     if 'dividend' in s:
# #         amounts = re.findall(r'(?:rs|re)\s*(\d+(?:\.\d+)?)', s)
# #         return 'DIVIDEND', sum(map(float, amounts)) if amounts else None

#     # return 'IGNORE', None


# # ================= MAIN ENGINE =================

# def run_adjustment_engine(PRICE_DIR,CLEAN_CA_FOLDER,REMAINING_CA_DIR,FUTURES_DATA_DIR,LOG_FILE):
#     print("🚀 Adjustment Engine Started")

#     skipped_actions = []

#     try:
#         ca_file = get_latest_ca_file(CLEAN_CA_FOLDER)

#         if not ca_file:
#             print("⚠️ No cleaned corporate action file found")
#             return

#         try:
#             ca = pd.read_csv(ca_file)
#             print(f"📄 Using CA file: {os.path.basename(ca_file)}")
#         except Exception:
#             print("❌ Failed to read CA file")
#             return

#     except Exception:
#         ca = pd.DataFrame()

#     if ca.empty:
#         print("⚠️ Corporate Action file empty or missing")
#         today_folder = os.path.join(REMAINING_CA_DIR, datetime.today().strftime("%Y-%m-%d"))
#         os.makedirs(today_folder, exist_ok=True)
#         return

#     ca.columns = ca.columns.str.lower()
#     # normalize symbol values for case-insensitive matching
#     if 'symbol' in ca.columns:
#         ca['symbol'] = ca['symbol'].astype(str).str.lower()
#     ca['exdate'] = pd.to_datetime(ca.get('exdate'), errors='coerce')
#     ca = ca.dropna(subset=['exdate']).sort_values('exdate', ascending=False)

#     for price_file in os.listdir(PRICE_DIR):
#         if not price_file.endswith(".csv"):
#             continue

#         symbol = price_file.replace(".csv", "")
#         price_path = os.path.join(PRICE_DIR, price_file)

#         df = pd.read_csv(price_path)

#         # Keep original column casing to restore later
#         original_cols_map = {col.lower(): col for col in df.columns}
#         # Normalize columns to lowercase for case-insensitive processing
#         df.columns = [c.lower() for c in df.columns]

#         # Require date column (case-insensitive)
#         if 'date' not in df.columns:
#             continue

#         df['date'] = pd.to_datetime(df['date'], errors='coerce')
#         df = df.dropna(subset=['date']).sort_values('date').reset_index(drop=True)

#         # symbol matching: compare lowercase symbol names
#         original_symbol = symbol
#         symbol = symbol.lower()
#         ca_sym = ca[ca['symbol'] == symbol]

#         for _, row in ca_sym.iterrows():
#             exdate = row['exdate']
#             subject = row['subject']
#             face_val = float(row['faceval']) if pd.notna(row.get('faceval')) else 10

#             hist_mask = df['date'] < exdate
#             if not hist_mask.any():
#                 skipped_actions.append(row)
#                 continue

#             # Use lowercase 'close' column
#             if 'close' not in df.columns:
#                 skipped_actions.append(row)
#                 continue

#             cum_close = df.loc[hist_mask].iloc[-1]['close']
#             action, param = identify_action(subject, face_val)

#             factor = 1.0

#             if action == 'STOP':
#                 skipped_actions.append(row)
#                 break

#             if action in ['SPLIT', 'BONUS'] and param:
#                 factor = param

#             elif action == 'DIVIDEND' and param and cum_close > 0:
#                 factor = (cum_close - param) / cum_close

#             elif action == 'RIGHTS' and param and param[0] is not None:
#                 new, cash = param
#                 terp = (cum_close + cash) / (1 + new)
#                 factor = terp / cum_close
#             else:
#                 skipped_actions.append(row)
#                 continue

#             if factor <= 0 or factor == 1:
#                 skipped_actions.append(row)
#                 continue

#             for col in ['open', 'high', 'low', 'close', 'prev close']:
#                 if col in df.columns:
#                     df.loc[hist_mask, col] *= factor

#             if action in ['SPLIT', 'BONUS'] and 'volume' in df.columns:
#                 df.loc[hist_mask, 'volume'] /= factor

#             ex_mask = df['date'] == exdate
#             if ex_mask.any() and 'prev close' in df.columns:
#                 df.loc[ex_mask, 'prev close'] *= factor

#         # Restore original column casing where possible
#         df.columns = [original_cols_map.get(c, c) for c in df.columns]
#         df.round(2).to_csv(price_path, index=False)
#         print(f"✅ Adjusted: {original_symbol}")

#     # ===== SAVE SKIPPED CA =====
#     today = datetime.today().strftime("%Y-%m-%d")

#     if skipped_actions:
#         out_file = os.path.join(REMAINING_CA_DIR, f"{today}.csv")
#         pd.DataFrame(skipped_actions).to_csv(out_file, index=False)
#         print(f"📌 Skipped CA saved: {out_file}")
#     else:
#         empty_dir = os.path.join(REMAINING_CA_DIR, today)
#         os.makedirs(empty_dir, exist_ok=True)
#         print("📂 No skipped CA — empty folder created")

#     print("🎉 Adjustment Engine Completed")




# import pandas as pd
# import os
# import re
# import tempfile
# import shutil



# def normalize_subject(subject):
#     s = str(subject).lower()

#     replacements = {
#         'spl div': 'special dividend',
#         'sd': 'special dividend',
#         'dvd': 'dividend',
#         ' div ': ' dividend ',
#         'spl': 'split',
#         'sub div': 'split',
#         'sub-division': 'split',
#         'subdivision': 'split',
#         'bon': 'bonus',
#         'bns': 'bonus',
#         'rts': 'rights'
#     }

#     for k, v in replacements.items():
#         s = s.replace(k, v)

#     return s


# def parse_rights(subject, face_val):
#     parts = re.split(r'\/|&|\band\b', subject, flags=re.IGNORECASE)
#     total_new, total_cash = 0.0, 0.0

#     for part in parts:
#         ratio = re.search(r'(\d+)\s*:\s*(\d+)', part)
#         premium = re.search(r'(?:rs\.?|re\.?)\s*(\d+(?:\.\d+)?)', part, re.I)

#         if ratio:
#             new, held = map(float, ratio.groups())
#             if held == 0:
#                 continue

#             price = face_val + (float(premium.group(1)) if premium else 0.0)
#             frac = new / held
#             total_new += frac
#             total_cash += frac * price

#     return (total_new, total_cash) if total_new > 0 else (None, None)


# def identify_action(subject, face_val):
#     s = normalize_subject(subject)

#     # ---- STOP actions ----
#     stop_words = [
#         'demerger', 'amalgamation', 'scheme',
#         'capital reduction', 'consolidation',
#         'partly paid', 'nclt'
#     ]
#     if any(w in s for w in stop_words):
#         return 'STOP', None

#     # ---- SPLIT ----
#     if 'split' in s:
#         m = re.search(r'from.*?(?:rs|re)\s*(\d+(?:\.\d+)?).*?to.*?(?:rs|re)\s*(\d+(?:\.\d+)?)', s)
#         if m:
#             old, new = max(map(float, m.groups())), min(map(float, m.groups()))
#             return 'SPLIT', new / old

#     # ---- BONUS ----
#     if 'bonus' in s:
#         m = re.search(r'(\d+)\s*:\s*(\d+)', s)
#         if m:
#             new, held = map(float, m.groups())
#             return 'BONUS', held / (new + held)

#     # ---- RIGHTS ----
#     if 'rights' in s:
#         return 'RIGHTS', parse_rights(subject, face_val)

#     # ---- DIVIDEND ----
#     if 'dividend' in s:
#         amts = re.findall(r'(?:rs|re)\s*(\d+(?:\.\d+)?)', s)
#         return 'DIVIDEND', sum(map(float, amts)) if amts else None

#     return 'IGNORE', None


# def atomic_write(df, path):
#     with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="") as tmp:
#         temp_path = tmp.name
#         df.to_csv(temp_path, index=False)
#     shutil.move(temp_path, path)

# # ================= MAIN =================

# def process_futures_data(PRICE_DIR,CLEAN_CA_FOLDER,REMAINING_CA_DIR,FUTURES_DATA_DIR,LOG_FILE):
#     skipped_log = []
#     print("1")

#     ca_file = get_latest_ca_file(CLEAN_CA_FOLDER)
#     if not ca_file:
#         print("❌ No cleaned CA file found. Exiting safely.")
#         return
    

#     print(f"📄 Using CA File: {os.path.basename(ca_file)}")

#     df_ca = pd.read_csv(ca_file)
#     df_ca.columns = df_ca.columns.str.lower().str.strip()

#     if 'series' in df_ca.columns:
#         df_ca = df_ca[df_ca['series'] == 'EQ']

#     print("2")

#     df_ca['exdate'] = pd.to_datetime(df_ca['exdate'], errors='coerce')
#     df_ca = df_ca.dropna(subset=['exdate'])
#     print("3")

#     for symbol, ca_grp in df_ca.groupby('symbol'):
#         fut_path = os.path.join(FUTURES_DATA_DIR, f"{symbol.upper()}.csv")
#         print("4")

#         if not os.path.exists(fut_path):
#             continue

#         df_fut = pd.read_csv(fut_path)
#         if 'TIMESTAMP' not in df_fut.columns:
#             continue
#         print("5")

#         df_fut['TIMESTAMP'] = pd.to_datetime(df_fut['TIMESTAMP'], errors='coerce')
#         df_fut = df_fut.sort_values('TIMESTAMP').reset_index(drop=True)
#         print("6")

#         ca_grp = ca_grp.sort_values('exdate', ascending=False)
#         modified = False
#         print("7")

#         for _, row in ca_grp.iterrows():
#             exdate = row['exdate']
#             subject = row['subject']
#             face_val = float(row['faceval']) if pd.notna(row['faceval']) and row['faceval'] else 10

#             mask = df_fut['TIMESTAMP'] < exdate
#             if not mask.any():
#                 continue
#             print("8")

#             cum_close = df_fut.loc[mask].iloc[-1]['CLOSE_PRICE']
#             action, param = identify_action(subject, face_val)

#             factor = 1.0

#             if action == 'STOP':
#                 skipped_log.append({'Symbol': symbol, 'ExDate': exdate, 'Subject': subject})
#                 break

#             print("9")
#             if action in ['SPLIT', 'BONUS'] and param:
#                 factor = param

#             elif action == 'DIVIDEND' and param and cum_close > 0:
#                 factor = (cum_close - param) / cum_close

#             elif action == 'RIGHTS' and param[0] is not None:
#                 new, cash = param
#                 terp = (cum_close + cash) / (1 + new)
#                 factor = terp / cum_close

#             else:
#                 skipped_log.append({'Symbol': symbol, 'ExDate': exdate, 'Subject': subject})
#                 continue

#             print("10")
#             if factor <= 0 or factor == 1:
#                 continue

#             modified = True
#             print("11")

#             for col in ['OPEN_PRICE', 'HI_PRICE', 'LO_PRICE', 'CLOSE_PRICE']:
#                 if col in df_fut.columns:
#                     df_fut.loc[mask, col] *= factor
#             print("12")

#             if action in ['SPLIT', 'BONUS']:
#                 for col in df_fut.columns:
#                     if any(x in col for x in ['QTY', 'OPEN_INT', 'NO_OF_CONT']):
#                         df_fut.loc[mask, col] /= factor
#             print("13")

#         if modified:
#             atomic_write(df_fut.round(2), fut_path)
#             print(f"✅ Adjusted Futures: {symbol}")

#     if skipped_log:
#         pd.DataFrame(skipped_log).to_csv(LOG_FILE, index=False)
#         print(f"📌 Skipped CA logged: {LOG_FILE}")


# def run_engine(PRICE_DIR,CLEAN_CA_FOLDER,REMAINING_CA_DIR,FUTURES_DATA_DIR,LOG_FILE):
#     multiprocessing.freeze_support()

#     p_cash = multiprocessing.Process(target=  process_futures_data, args=(PRICE_DIR,CLEAN_CA_FOLDER,REMAINING_CA_DIR,FUTURES_DATA_DIR,LOG_FILE))
#     p_fut = multiprocessing.Process(target= run_adjustment_engine, args = (PRICE_DIR,CLEAN_CA_FOLDER,REMAINING_CA_DIR,FUTURES_DATA_DIR,LOG_FILE))

#     p_cash.start()
#     p_fut.start()

#     p_cash.join()
#     p_fut.join()

#     print("\n✅✅✅ Adjustment COMPLETE ✅✅✅")


# if __name__ == "__main__":
#     run_engine(PATHS["STOCK_WISE_PR"], PATHS["CLEAN_CA"], PATHS["REMAINING_CA"],PATHS["STOCK_WISE_FO"], PATHS["LOG_FILE"])
  


# # PROJECT_ROOT: C:\Users\91702\Documents\programming\all_cash_stocks\set
# # RAW_PR: C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\pr
# # RAW_CA: C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\ca
# # RAW_FO: C:\Users\91702\Documents\programming\all_cash_stocks\set\raw\fo
# # CLEAN_CA: C:\Users\91702\Documents\programming\all_cash_stocks\set\clean
# # STOCK_WISE_PR: C:\Users\91702\Documents\programming\all_cash_stocks\stock_wise
# # STOCK_WISE_FO: C:\Users\91702\Documents\programming\all_cash_stocks\adjusted_futures_data_final
# # SECTOR_MAP: C:\Users\91702\Documents\programming\Trading_Data_Transformation\step3_fo_to_fo_pair\data\sector\sector_master_map.csv
# # SECTOR_OUTPUT: C:\Users\91702\Documents\programming\all_cash_stocks\sec_wise_futures_data
# # REMAINING_CA: C:\Users\91702\Documents\programming\Trading_Data_Transformation\automation\remaning_ca
# # LOG_FILE: C:\Users\91702\Documents\programming\Trading_Data_Transformation\automation\logs\Futures_Skipped_CA_Log.csv

  
    








import os
import re
import pandas as pd
from datetime import datetime
import multiprocessing
import shutil
import tempfile

# ================= PATHS =================
# Make paths relative to the Trading folder so the engine can be run from here
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PROJECT_DIR = os.path.join(REPO_ROOT, "set")
DATA_DIR = REPO_ROOT
APP_DATA_DIR = os.path.join(REPO_ROOT, "Trading_Data_Transformation")

PATHS = {
    "STOCK_WISE_PR": os.path.join(DATA_DIR, "stock_wise"),
    "STOCK_WISE_FO": os.path.join(DATA_DIR, "adjusted_futures_data_final"),
    "CLEAN_CA": os.path.join(PROJECT_DIR, "clean"),
    "LOG_FILE": os.path.join(DATA_DIR, "automation", "logs", "corporate_logs.csv"),
}

# ================= HELPER FUNCTIONS =================

def get_latest_ca_file(folder):
    pattern = re.compile(r"corporate_action_data_(\d+)\.csv")
    latest_file = None
    max_num = -1
    for f in os.listdir(folder):
        match = pattern.match(f)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
                latest_file = f
    return os.path.join(folder, latest_file) if latest_file else None

def normalize_subject(s):
    s = str(s).lower()
    replacements = {
        'spl div': 'special dividend', 'sd': 'special dividend', 'dvd': 'dividend', 'div': 'dividend',
        'spl': 'split', 'sub div': 'split', 'sub-division': 'split', 'subdivision': 'split',
        'bon': 'bonus', 'bns': 'bonus', 'rts': 'rights'
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s

def atomic_write(df, path):
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="") as tmp:
        temp_path = tmp.name
        df.to_csv(temp_path, index=False)
    shutil.move(temp_path, path)

# ================= IDENTIFY ACTION LOGIC =================

def identify_action(subject, face_val):
    s = normalize_subject(subject)
    
    # STOP words
    stop_words = ['demerger', 'amalgamation', 'scheme', 'capital reduction', 'consolidation', 'nclt']
    if any(w in s for w in stop_words):
        return 'STOP', None

    if 'split' in s:
        m = re.search(r'from.*?(?:rs|re)\s*(\d+(?:\.\d+)?).*?to.*?(?:rs|re)\s*(\d+(?:\.\d+)?)', s)
        if m:
            old, new = max(map(float, m.groups())), min(map(float, m.groups()))
            return 'SPLIT', new / old

    if 'bonus' in s:
        m = re.search(r'(\d+)\s*:\s*(\d+)', s)
        if m:
            new, held = map(float, m.groups())
            return 'BONUS', held / (new + held)

    if 'dividend' in s:
        amts = re.findall(r'(?:rs|re)\s*(\d+(?:\.\d+)?)', s)
        if amts: return 'DIVIDEND', sum(map(float, amts))

    if 'rights' in s:
        return 'STOP', None 

    return 'IGNORE', None

# ================= PHASE 1: INTERACTIVE RESOLUTION (UPDATED) =================

def resolve_actions_interactively(ca_path, log_path):
    print(f"\n🔍 [Phase 1] Scanning Corporate Actions from: {os.path.basename(ca_path)}")
    
    # 1. Load CA Data
    df_ca = pd.read_csv(ca_path)
    df_ca.columns = df_ca.columns.str.lower().str.strip()
    df_ca['exdate'] = pd.to_datetime(df_ca['exdate'], errors='coerce')
    df_ca = df_ca.dropna(subset=['exdate'])
    
    # 2. Load Existing Logs
    if os.path.exists(log_path):
        df_log = pd.read_csv(log_path)
        # Create a dictionary for fast lookup
        # Key: Symbol + Date
        df_log['key'] = df_log['symbol'] + "_" + df_log['date_of_corporate_action'].astype(str)
        log_dict = df_log.set_index('key').to_dict('index')
    else:
        df_log = pd.DataFrame(columns=['symbol', 'subject', 'date_of_corporate_action', 'status_for_cash', 'status_for_futures'])
        log_dict = {}

    approved_factors = {}
    rows_to_remove = []
    
    # We will build a list of NEW or UPDATED log entries
    # This list starts with existing data to preserve history
    final_log_data = df_log.to_dict('records') 
    
    # Helper to update/add log entry in the list
    def upsert_log(symbol, date, subject, stat_c, stat_f):
        # Check if exists in current list
        found = False
        for entry in final_log_data:
            if entry['symbol'] == symbol and entry['date_of_corporate_action'] == date:
                entry['subject'] = subject # Ensure subject is updated/stored
                entry['status_for_cash'] = stat_c
                entry['status_for_futures'] = stat_f
                found = True
                break
        if not found:
            final_log_data.append({
                'symbol': symbol,
                'subject': subject,
                'date_of_corporate_action': date,
                'status_for_cash': stat_c,
                'status_for_futures': stat_f
            })

    # 3. Iterate CAs
    for idx, row in df_ca.iterrows():
        symbol = row['symbol']
        exdate = row['exdate']
        subject = row['subject']
        face_val = float(row.get('faceval', 10)) if pd.notna(row.get('faceval')) else 10
        exdate_str = exdate.strftime('%Y-%m-%d')
        key = f"{symbol}_{exdate_str}"

        # Check existing status
        current_status = log_dict.get(key, {'status_for_cash': 'Pending', 'status_for_futures': 'Pending'})
        s_cash = current_status.get('status_for_cash', 'Pending')
        s_fut = current_status.get('status_for_futures', 'Pending')

        # If both are fully processed (Adjusted or Removed), skip
        if s_cash in ['Adjusted', 'Removed'] and s_fut in ['Adjusted', 'Removed']:
            continue

        # Determine Factor
        action, factor = identify_action(subject, face_val)
        
        # Trigger Condition: 
        # 1. Action is STOP (Complex)
        # 2. OR User explicitly marked it 'Unadjusted' previously (Retry logic)
        # 3. OR It's a new entry (Pending) but Factor is None (Unknown logic)
        needs_input = (action == 'STOP') or (s_cash == 'Unadjusted') or (s_fut == 'Unadjusted')

        if needs_input:
            print("\n" + "="*60)
            print(f"⚠️  ACTION REQUIRES ATTENTION")
            print(f"📌 Symbol: {symbol} | Date: {exdate_str}")
            print(f"📝 Subject: {subject}")
            print(f"🔄 Detected: {action} | Auto-Factor: {factor}")
            print("-" * 60)
            print("   [1] Enter Factor (Adjust)")
            print("   [2] Skip (Mark as Unadjusted)")
            print("   [3] REMOVE (Delete from CA File)")
            
            while True:
                choice = input("👉 Choice: ").strip()
                
                if choice == '1':
                    try:
                        user_fac = float(input("   Enter Factor: "))
                        factor = user_fac
                        if action == 'STOP': action = 'MANUAL'
                        # Set status to pending so Phase 2 picks it up
                        s_cash, s_fut = 'Pending', 'Pending'
                        break
                    except ValueError: print("   ❌ Invalid number.")
                
                elif choice == '2':
                    factor = None
                    # ✅ HERE IS THE FIX: Explicitly set status to Unadjusted
                    s_cash, s_fut = 'Unadjusted', 'Unadjusted'
                    print(f"   -> Skipped. Logged as Unadjusted.")
                    break
                
                elif choice == '3':
                    rows_to_remove.append(idx)
                    factor = None
                    s_cash, s_fut = 'Removed', 'Removed'
                    break
                else:
                    print("   ❌ Invalid choice.")

        # 4. If we have a factor (Auto or Manual), add to Todo List
        if factor is not None:
            approved_factors[(symbol, exdate_str)] = {
                'factor': factor, 
                'action': action,
                'status_cash': s_cash, # Pass current status so we don't re-do adjusted ones
                'status_fut': s_fut
            }
        
        # 5. Update the Log Data immediately (In Memory)
        # This captures 'Unadjusted', 'Removed', and 'Pending'
        upsert_log(symbol, exdate_str, subject, s_cash, s_fut)

    # 6. Apply Removals
    if rows_to_remove:
        print(f"\n🗑️ Removing {len(rows_to_remove)} rows from Main CA File...")
        df_ca.drop(rows_to_remove).to_csv(ca_path, index=False)

    # 7. Write Logs to Disk (Crucial for Skipped items)
    # We write everything now. Phase 3 will just update 'Pending' to 'Adjusted' later.
    pd.DataFrame(final_log_data).to_csv(log_path, index=False)
    print(f"✅ Logs updated with current decisions: {log_path}")

    return approved_factors

# ================= PHASE 2: PARALLEL EXECUTION =================

def process_market_data(mode, data_dir, approved_factors, log_queue):
    print(f"🔹 [{mode}] Task Started...")
    
    # Organize factors by Symbol
    symbol_actions = {}
    for (sym, date), data in approved_factors.items():
        # Optimization: Don't process if log says "Adjusted"
        if mode == 'CASH' and data['status_cash'] == 'Adjusted': continue
        if mode == 'FUTURES' and data['status_fut'] == 'Adjusted': continue

        if sym not in symbol_actions: symbol_actions[sym] = []
        symbol_actions[sym].append({
            'exdate': pd.to_datetime(date),
            'factor': data['factor'],
            'action': data['action'],
            'date_str': date
        })

    count = 0
    for file in os.listdir(data_dir):
        if not file.endswith(".csv"): continue
        symbol = file.replace(".csv", "").upper()
        
        # Case Insensitive Lookup
        matched_actions = None
        for k in symbol_actions.keys():
            if k.upper() == symbol:
                matched_actions = symbol_actions[k]
                actual_symbol_key = k
                break
        
        if not matched_actions: continue

        path = os.path.join(data_dir, file)
        try:
            df = pd.read_csv(path)
            
            # Determine Date Column
            date_col = 'TIMESTAMP' if mode == 'FUTURES' else 'Date'
            if date_col not in df.columns:
                for c in df.columns:
                    if c.lower() in ['date', 'timestamp']:
                        date_col = c
                        break
            
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.sort_values(date_col).reset_index(drop=True)
            
            modified = False
            matched_actions.sort(key=lambda x: x['exdate'], reverse=True)

            for item in matched_actions:
                exdate = item['exdate']
                factor = item['factor']
                action = item['action']
                
                mask = df[date_col] < exdate
                if not mask.any(): continue
                
                # Apply Price
                price_cols = ['OPEN_PRICE', 'HI_PRICE', 'LO_PRICE', 'CLOSE_PRICE'] if mode == 'FUTURES' else ['Open', 'High', 'Low', 'Close', 'Prev Close']
                existing_cols = [c for c in price_cols if c in df.columns]
                
                if factor != 1.0:
                    for col in existing_cols:
                        df.loc[mask, col] *= factor
                    modified = True

                # Apply Volume (Splits/Bonus)
                if action in ['SPLIT', 'BONUS', 'MANUAL']: 
                    vol_cols = ['OPEN_INT', 'TRD_QTY', 'NO_OF_CONT'] if mode == 'FUTURES' else ['Volume']
                    existing_vol = [c for c in vol_cols if c in df.columns]
                    for col in existing_vol:
                        df.loc[mask, col] /= factor
                    modified = True
                
                # Log Success
                log_queue.put({'symbol': actual_symbol_key, 'date': item['date_str'], 'type': mode})

            if modified:
                atomic_write(df.round(2), path)
                count += 1

        except Exception as e:
            print(f"❌ Error {symbol}: {e}")

    print(f"🏁 [{mode}] Completed. Adjusted {count} files.")

# ================= PHASE 3: FINAL LOG UPDATE =================

def update_logs_final(log_path, processed_events):
    """Updates status from 'Pending' to 'Adjusted' based on successful processing"""
    if not processed_events: return

    df = pd.read_csv(log_path) # File exists because Phase 1 created/updated it

    for event in processed_events:
        sym = event['symbol']
        date = event['date']
        typ = event['type']
        
        mask = (df['symbol'] == sym) & (df['date_of_corporate_action'] == date)
        if mask.any():
            col = 'status_for_cash' if typ == 'CASH' else 'status_for_futures'
            df.loc[mask, col] = 'Adjusted'

    df.to_csv(log_path, index=False)
    print("✅ Final Logs Updated (Pending -> Adjusted).")

def run_engine():
    ca_path = get_latest_ca_file(PATHS["CLEAN_CA"])
    if not ca_path:
        print("❌ No CA File Found.")
        return

    # --- PHASE 1 ---
    factors = resolve_actions_interactively(ca_path, PATHS["LOG_FILE"])
    
    if not factors:
        print("✅ No pending adjustments found.")
        return

    # --- PHASE 2 ---
    print("\n🚀 Starting Parallel Adjustment Engine...")
    manager = multiprocessing.Manager()
    log_queue = manager.Queue()

    p1 = multiprocessing.Process(target=process_market_data, args=('CASH', PATHS["STOCK_WISE_PR"], factors, log_queue))
    p2 = multiprocessing.Process(target=process_market_data, args=('FUTURES', PATHS["STOCK_WISE_FO"], factors, log_queue))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    # --- PHASE 3 ---
    events = []
    while not log_queue.empty():
        events.append(log_queue.get())
    
    update_logs_final(PATHS["LOG_FILE"], events)
    print("\n✅✅✅ Process Complete ✅✅✅")

if __name__ == "__main__":
    run_engine()