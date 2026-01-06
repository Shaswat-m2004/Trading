# import pandas as pd
# import numpy as np

# def calculate_pair_metrics(df, window=5, std_dev_multiplier=2.0):
#     """
#     Calculates Price Ratio, Mean, and Bollinger Bands.
#     """
#     # 1. Calculate Ratio (Stock A / Stock B)
#     # Using 'CLOSE_PRICE' assuming that's the column name in your CSVs
#     if 'CLOSE_PRICE_A' not in df.columns or 'CLOSE_PRICE_B' not in df.columns:
#         return df # Return empty or original if columns missing
        
#     df['Ratio'] = df['CLOSE_PRICE_A'] / df['CLOSE_PRICE_B']

#     # 2. Calculate Rolling Mean (SMA)
#     df['Mean'] = df['Ratio'].rolling(window=window).mean()

#     # 3. Calculate Standard Deviation
#     df['StdDev'] = df['Ratio'].rolling(window=window).std()

#     # 4. Calculate Upper & Lower Bands
#     df['Upper_Band'] = df['Mean'] + (df['StdDev'] * std_dev_multiplier)
#     df['Lower_Band'] = df['Mean'] - (df['StdDev'] * std_dev_multiplier)

#     # Clean up NaNs created by rolling window
#     if 'CLOSE_PRICE_A' not in df.columns or 'CLOSE_PRICE_B' not in df.columns:
#         return df
        
#     df['Ratio'] = df['CLOSE_PRICE_A'] / df['CLOSE_PRICE_B']
#     df['Mean'] = df['Ratio'].rolling(window=window).mean()
#     df['StdDev'] = df['Ratio'].rolling(window=window).std()
#     df['Upper_Band'] = df['Mean'] + (df['StdDev'] * std_dev_multiplier)
#     df['Lower_Band'] = df['Mean'] - (df['StdDev'] * std_dev_multiplier)

#     # --- NEW ADDITIONS ---

#     # 5. Z-Score Calculation (Step 10)
#     # Z = (Current Price - Mean) / StdDev
#     # Isse humein pata chalta hai ki hum "Mean" se kitne Sigma dur hain
#     df['Z_Score'] = (df['Ratio'] - df['Mean']) / df['StdDev']

#     # 6. RSI of Ratio (Step 7) - 14 Period Default
#     delta = df['Ratio'].diff()
#     gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
#     loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
#     rs = gain / loss
#     df['RSI'] = 100 - (100 / (1 + rs))

#     return df

#     # return df.dropna()

# # ==========================================
# # NEW: NORMALIZED PERFORMANCE CALCULATION
# # ==========================================
# def calculate_normalized_performance(df, start_date):
#     """
#     Filters data from a start date and normalizes both stock prices to start at 100.
#     Formula: (Current Price / Initial Price) * 100
#     """
#     # 1. Ensure start_date is datetime
#     start_dt = pd.to_datetime(start_date)

#     # 2. Filter data from that date onwards
#     norm_df = df[df.index >= start_dt].copy()

#     if norm_df.empty:
#          # If selected date is too recent and has no data
#          return pd.DataFrame()

#     # 3. Get the closing prices of the VERY FIRST day in the filtered data
#     initial_price_a = norm_df['CLOSE_PRICE_A'].iloc[0]
#     initial_price_b = norm_df['CLOSE_PRICE_B'].iloc[0]

#     # 4. Apply Normalization Formula to create new columns
#     norm_df['Norm_A'] = (norm_df['CLOSE_PRICE_A'] / initial_price_a) * 100
#     norm_df['Norm_B'] = (norm_df['CLOSE_PRICE_B'] / initial_price_b) * 100
    
#     return norm_df

# def generate_trade_signals(df, z_threshold=2.0, rsi_upper=70, rsi_lower=30):
#     """
#     Generates Buy/Sell signals based on Z-Score and RSI confluence.
#     Returns the dataframe with 'Signal' and 'Signal_Label' columns.
#     """
#     # Copy dataframe to avoid SettingWithCopyWarning
#     df = df.copy()
    
#     # Initialize Signal Column (0 = Hold/Neutral)
#     df['Signal'] = 0
#     df['Signal_Label'] = "No Signal"

#     # --- LONG ENTRY RULES (Buy A, Sell B) ---
#     # Condition: Z-Score < -Threshold AND RSI < 30 (Oversold)
#     long_condition = (df['Z_Score'] <= -z_threshold) & (df['RSI'] <= rsi_lower)
    
#     df.loc[long_condition, 'Signal'] = 1
#     df.loc[long_condition, 'Signal_Label'] = "ENTRY LONG"

#     # --- SHORT ENTRY RULES (Sell A, Buy B) ---
#     # Condition: Z-Score > +Threshold AND RSI > 70 (Overbought)
#     short_condition = (df['Z_Score'] >= z_threshold) & (df['RSI'] >= rsi_upper)
    
#     df.loc[short_condition, 'Signal'] = -1
#     df.loc[short_condition, 'Signal_Label'] = "ENTRY SHORT"

#     return df

# def calculate_dominance_stats(norm_df):
#     """
#     Calculates the percentage of days Stock A vs Stock B was leading 
#     in performance (Normalized Basis).
#     Returns: A dictionary with Historical and Recent (3 Month) percentages.
#     """
#     if norm_df.empty:
#         return None

#     # --- 1. HISTORICAL (Full Selected Period) ---
#     total_days = len(norm_df)
#     # Count days where Stock A > Stock B
#     days_a_led = len(norm_df[norm_df['Norm_A'] > norm_df['Norm_B']])
    
#     hist_a_pct = (days_a_led / total_days) * 100
#     hist_b_pct = 100 - hist_a_pct

#     # --- 2. RECENT (Last 3 Months) ---
#     # Determine the date 3 months ago from the last available date
#     last_date = norm_df.index.max()
#     three_months_ago = last_date - pd.DateOffset(months=3)
    
#     recent_df = norm_df[norm_df.index >= three_months_ago]
    
#     if not recent_df.empty:
#         rec_total = len(recent_df)
#         rec_days_a_led = len(recent_df[recent_df['Norm_A'] > recent_df['Norm_B']])
        
#         rec_a_pct = (rec_days_a_led / rec_total) * 100
#         rec_b_pct = 100 - rec_a_pct
#     else:
#         # Fallback if less than 3 months of data exists
#         rec_a_pct = hist_a_pct
#         rec_b_pct = hist_b_pct

#     return {
#         "hist_a": hist_a_pct,
#         "hist_b": hist_b_pct,
#         "rec_a": rec_a_pct,
#         "rec_b": rec_b_pct
#     }

# def backtest_strategy(df):
#     """
#     Simulates trading based on signals and calculates P&L.
#     Assumes: 
#     - Entry on Signal (+1/-1)
#     - Exit when Z-Score crosses 0 (Mean Reversion)
#     """
#     df = df.copy()
    
#     # 1. Position Logic
#     # Hum ek 'Position' column banayenge. 
#     # 1 = Long Ratio (Buy A, Sell B)
#     # -1 = Short Ratio (Sell A, Buy B)
#     # 0 = No Position
    
#     col_name = 'Position'
#     df[col_name] = 0
    
#     current_pos = 0
    
#     # Loop through data to manage state (Entry vs Exit)
#     # Note: Vectorized approach is faster, but loop is easier to understand for state management (Entry -> Wait -> Exit)
#     for i in range(1, len(df)):
#         # Previous position carry forward
#         prev_pos = current_pos
        
#         # Current Row Data
#         z_score = df['Z_Score'].iloc[i]
#         signal = df['Signal'].iloc[i]
        
#         # --- EXIT CONDITIONS (Check first) ---
#         # Agar hum Long hain aur Z-Score 0 ke upar aa gaya -> Exit
#         if current_pos == 1 and z_score >= 0:
#             current_pos = 0
            
#         # Agar hum Short hain aur Z-Score 0 ke niche aa gaya -> Exit
#         elif current_pos == -1 and z_score <= 0:
#             current_pos = 0
            
#         # --- ENTRY CONDITIONS ---
#         # Agar koi position nahi hai, tabhi enter karenge
#         elif current_pos == 0:
#             if signal == 1:
#                 current_pos = 1
#             elif signal == -1:
#                 current_pos = -1
        
#         df.at[df.index[i], col_name] = current_pos

#     # 2. Calculate P&L
#     # Strategy Return = Position (Yesterday) * Market Return (Today)
#     # Market Return is change in the Ratio
#     df['Ratio_Ret'] = df['Ratio'].pct_change()
#     df['Strategy_Ret'] = df['Position'].shift(1) * df['Ratio_Ret']
    
#     # Cumulative Returns (Equity Curve)
#     df['Cumulative_Returns'] = (1 + df['Strategy_Ret']).cumprod()
    
#     return df

# def calculate_metrics(df):
#     """
#     Calculates Win Rate, Total Return, etc.
#     """
#     # Filter days where we had a trade
#     trade_days = df[df['Position'] != 0]
    
#     if trade_days.empty:
#         return {"Total Return": "0%", "Win Rate": "0%"}

#     total_return = (df['Cumulative_Returns'].iloc[-1] - 1) * 100
    
#     # Win Rate Approximation (Positive Daily Returns / Total Active Days)
#     wins = len(trade_days[trade_days['Strategy_Ret'] > 0])
#     total_active = len(trade_days)
#     win_rate = (wins / total_active) * 100 if total_active > 0 else 0
    
#     return {
#         "Total Return": f"{total_return:.2f}%",
#         "Win Rate": f"{win_rate:.2f}%",
#         "Days in Market": total_active
#     }



# def backtest_with_risk_management(df, stop_loss_z=3.5, take_profit_z=0.0, max_days=10):
#     """
#     Simulates trading with strict Exit Rules:
#     1. Profit: Z-Score returns to 'take_profit_z' (Mean Reversion).
#     2. Stop Loss: Z-Score exceeds 'stop_loss_z' (Regime Break).
#     3. Time Stop: Position held for > 'max_days'.
#     """
#     df = df.copy()
    
#     # New Columns
#     df['Position'] = 0
#     df['Exit_Reason'] = None # To track WHY we exited
#     df['Days_Held'] = 0
    
#     current_pos = 0 # 0: Flat, 1: Long, -1: Short
#     days_in_trade = 0
#     entry_price = 0
    
#     # Loop through Data
#     for i in range(1, len(df)):
#         # Data points
#         z = df['Z_Score'].iloc[i]
#         signal = df['Signal'].iloc[i]
#         close_ratio = df['Ratio'].iloc[i]
        
#         # --- 1. CHECK EXIT RULES (If Position is Active) ---
#         if current_pos != 0:
#             days_in_trade += 1
#             exit_trade = False
#             reason = None
            
#             # A. Statistical Stop Loss (Extreme Move against us)
#             # Long Logic: Entered at -2, if Z drops to -3.5 -> STOP LOSS
#             if current_pos == 1 and z <= -stop_loss_z:
#                 exit_trade = True
#                 reason = "SL: Regime Break"
#             # Short Logic: Entered at +2, if Z jumps to +3.5 -> STOP LOSS
#             elif current_pos == -1 and z >= stop_loss_z:
#                 exit_trade = True
#                 reason = "SL: Regime Break"
                
#             # B. Time Stop (Held too long)
#             elif days_in_trade >= max_days:
#                 exit_trade = True
#                 reason = "Time Stop"
                
#             # C. Mean Reversion (Take Profit)
#             # Long Logic: Z returned to 0 (or higher)
#             elif current_pos == 1 and z >= take_profit_z:
#                 exit_trade = True
#                 reason = "TP: Mean Reversion"
#             # Short Logic: Z returned to 0 (or lower)
#             elif current_pos == -1 and z <= -take_profit_z: # Symmetric target
#                 exit_trade = True
#                 reason = "TP: Mean Reversion"
            
#             # EXECUTE EXIT
#             if exit_trade:
#                 current_pos = 0
#                 days_in_trade = 0
#                 df.at[df.index[i], 'Exit_Reason'] = reason
        
#         # --- 2. CHECK ENTRY RULES (If Flat) ---
#         # Sirf tab enter karo agar abhi koi position nahi hai
#         if current_pos == 0:
#             if signal == 1:
#                 current_pos = 1
#                 entry_price = close_ratio
#             elif signal == -1:
#                 current_pos = -1
#                 entry_price = close_ratio
        
#         # Update State in DataFrame
#         df.at[df.index[i], 'Position'] = current_pos
#         df.at[df.index[i], 'Days_Held'] = days_in_trade

#     # --- 3. CALCULATE PnL ---
#     df['Ratio_Ret'] = df['Ratio'].pct_change()
#     # Strategy Return = Position (Yesterday) * Return (Today)
#     df['Strategy_Ret'] = df['Position'].shift(1) * df['Ratio_Ret']
#     df['Cumulative_Returns'] = (1 + df['Strategy_Ret']).cumprod()
    
#     return df






import pandas as pd
import numpy as np

# ==========================================
# PAIR METRICS
# ==========================================
def calculate_pair_metrics(df, window=20, std_dev_multiplier=2.0):

    if not {'CLOSE_PRICE_A', 'CLOSE_PRICE_B'}.issubset(df.columns):
        raise ValueError("Required columns missing: CLOSE_PRICE_A / CLOSE_PRICE_B")

    df = df.copy()

    # --- Ratio ---
    df['Ratio'] = df['CLOSE_PRICE_A'] / df['CLOSE_PRICE_B']

    # --- Bollinger Stats ---
    df['Mean'] = df['Ratio'].rolling(window).mean()
    df['StdDev'] = df['Ratio'].rolling(window).std()

    df['Upper_Band'] = df['Mean'] + std_dev_multiplier * df['StdDev']
    df['Lower_Band'] = df['Mean'] - std_dev_multiplier * df['StdDev']

    # --- Z-Score ---
    df['Z_Score'] = (df['Ratio'] - df['Mean']) / df['StdDev']

    # --- RSI (Wilder EMA) ---
    delta = df['Ratio'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()

    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# ==========================================
# NORMALIZED PERFORMANCE
# ==========================================
def calculate_normalized_performance(df, start_date):

    start_date = pd.to_datetime(start_date)
    df = df[df.index >= start_date].copy()

    if df.empty:
        return pd.DataFrame()

    base_a = df['CLOSE_PRICE_A'].iloc[0]
    base_b = df['CLOSE_PRICE_B'].iloc[0]

    df['Norm_A'] = (df['CLOSE_PRICE_A'] / base_a) * 100
    df['Norm_B'] = (df['CLOSE_PRICE_B'] / base_b) * 100

    return df

# ==========================================
# SIGNAL GENERATION
# ==========================================
def generate_trade_signals(df, z_threshold=2.0, rsi_upper=70, rsi_lower=30):

    df = df.copy()
    df['Signal'] = 0
    df['Signal_Label'] = "HOLD"

    valid = df[['Z_Score', 'RSI']].notna().all(axis=1)

    long_cond = valid & (df['Z_Score'] <= -z_threshold) & (df['RSI'] <= rsi_lower)
    short_cond = valid & (df['Z_Score'] >= z_threshold) & (df['RSI'] >= rsi_upper)


    df.loc[long_cond, ['Signal', 'Signal_Label']] = [1, "LONG ENTRY"]
    df.loc[short_cond, ['Signal', 'Signal_Label']] = [-1, "SHORT ENTRY"]

    return df

# ==========================================
# DOMINANCE METRICS
# ==========================================
def calculate_dominance_stats(norm_df):

    if norm_df.empty:
        return None

    hist_a = (norm_df['Norm_A'] > norm_df['Norm_B']).mean() * 100
    hist_b = 100 - hist_a

    last_date = norm_df.index.max()
    recent = norm_df[norm_df.index >= last_date - pd.DateOffset(months=3)]

    rec_a = (recent['Norm_A'] > recent['Norm_B']).mean() * 100 if not recent.empty else hist_a
    rec_b = 100 - rec_a

    return {
        "hist_a": hist_a,
        "hist_b": hist_b,
        "rec_a": rec_a,
        "rec_b": rec_b
    }

# ==========================================
# BASIC BACKTEST
# ==========================================
def backtest_strategy(df):

    df = df.copy()
    df['Position'] = 0

    for i in range(1, len(df)):
        prev_pos = df['Position'].iloc[i-1]
        z = df['Z_Score'].iloc[i-1]
        signal = df['Signal'].iloc[i-1]

        if prev_pos == 1 and z >= 0:
            df.iloc[i, df.columns.get_loc('Position')] = 0
        elif prev_pos == -1 and z <= 0:
            df.iloc[i, df.columns.get_loc('Position')] = 0
        elif prev_pos == 0:
            df.iloc[i, df.columns.get_loc('Position')] = signal
        else:
            df.iloc[i, df.columns.get_loc('Position')] = prev_pos

    df['Ratio_Ret'] = df['Ratio'].pct_change()
    df['Strategy_Ret'] = df['Position'].shift(1) * df['Ratio_Ret']
    df['Cumulative_Returns'] = (1 + df['Strategy_Ret']).cumprod()

    return df

# ==========================================
# RISK-MANAGED BACKTEST
# ==========================================
def backtest_with_risk_management(df, stop_loss_z=3.5, take_profit_z=0.0, max_days=10):

    df = df.copy()
    df['Position'] = 0
    df['Days_Held'] = 0
    df['Exit_Reason'] = None

    pos = 0
    days = 0

    for i in range(1, len(df)):
        z_prev = df['Z_Score'].iloc[i-1]
        signal_prev = df['Signal'].iloc[i-1]

        # EXIT
        if pos != 0:
            days += 1

            if (pos == 1 and z_prev <= -stop_loss_z) or (pos == -1 and z_prev >= stop_loss_z):
                pos, days = 0, 0
                df.at[df.index[i], 'Exit_Reason'] = "SL"
            elif days >= max_days:
                pos, days = 0, 0
                df.at[df.index[i], 'Exit_Reason'] = "TIME"
            elif (pos == 1 and z_prev >= take_profit_z) or (pos == -1 and z_prev <= -take_profit_z):
                pos, days = 0, 0
                df.at[df.index[i], 'Exit_Reason'] = "TP"

        # ENTRY
        if pos == 0:
            if signal_prev == 1:
                pos, days = 1, 1
            elif signal_prev == -1:
                pos, days = -1, 1

        df.at[df.index[i], 'Position'] = pos
        df.at[df.index[i], 'Days_Held'] = days

    df['Ratio_Ret'] = df['Ratio'].pct_change()
    df['Strategy_Ret'] = df['Position'].shift(1) * df['Ratio_Ret']
    df['Cumulative_Returns'] = (1 + df['Strategy_Ret']).cumprod()

    return df
