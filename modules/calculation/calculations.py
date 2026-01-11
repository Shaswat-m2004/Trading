
import pandas as pd
import numpy as np


def calculate_distribution_stats(df):
    """
    Calculates how often the Z-Score stays within specific Standard Deviation bands
    compared to a Theoretical Normal Distribution.
    """
    if 'Z_Score' not in df.columns:
        return None
        
    z = df['Z_Score'].dropna()
    total_points = len(z)
    
    if total_points == 0:
        return None

    # Define Bands
    stats_data = []
    
    # Ranges to check: within 1sd, within 2sd, within 3sd, and outlier (>3sd)
    # Theory (Normal Dist) Probabilities: 
    # 1σ: ~68.27%, 2σ: ~95.45%, 3σ: ~99.73%
    
    # 1. Inside 1 Sigma (-1 to 1)
    c1 = ((z > -1) & (z < 1)).sum()
    stats_data.append({
        "Range": "Inside ±1σ",
        "Count": c1,
        "Actual_%": (c1/total_points)*100,
        "Theoretical_%": 68.27
    })
    
    # 2. Inside 2 Sigma (-2 to 2)
    c2 = ((z > -2) & (z < 2)).sum()
    stats_data.append({
        "Range": "Inside ±2σ",
        "Count": c2,
        "Actual_%": (c2/total_points)*100,
        "Theoretical_%": 95.45
    })
    
    # 3. Inside 3 Sigma (-3 to 3)
    c3 = ((z > -3) & (z < 3)).sum()
    stats_data.append({
        "Range": "Inside ±3σ",
        "Count": c3,
        "Actual_%": (c3/total_points)*100,
        "Theoretical_%": 99.73
    })
    
    # 4. Outliers (> 3 Sigma or < -3 Sigma)
    outliers = total_points - c3
    stats_data.append({
        "Range": "Outliers (>±3σ)",
        "Count": outliers,
        "Actual_%": (outliers/total_points)*100,
        "Theoretical_%": 0.27
    })

    return pd.DataFrame(stats_data)

def get_spread_series(processed_df):
    """
    Spread for pair trading based on Ratio mean reversion
    Spread = Ratio - Mean
    """
    if "Ratio" not in processed_df.columns or "Mean" not in processed_df.columns:
        raise ValueError("Required columns (Ratio, Mean) not found in processed_df")

    spread = processed_df["Ratio"] - processed_df["Mean"]
    return spread.dropna()


# ==========================================
# PAIR METRICS
# ==========================================
def calculate_pair_metrics(df, window=20, std_dev_multiplier=2.0):
    
    if not {'CLOSE_PRICE_A', 'CLOSE_PRICE_B'}.issubset(df.columns):
        raise ValueError("Required columns missing: CLOSE_PRICE_A / CLOSE_PRICE_B")
    
    df = df.copy()
    df.sort_index(inplace=True)
      # ✅ FIX: Ensure data is sorted by Date (Oldest to Newest)

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
    
    df = df.copy()
    df.sort_index(inplace=True)  # ✅ FIX: Ensure sort before filtering
    
    df = df[df.index >= start_date]

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
    df.sort_index(inplace=True)  # ✅ FIX: Ensure sort

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
    
    # Ensure it's sorted just in case, though usually comes from calc_norm_perf
    norm_df = norm_df.sort_index() 

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
    df.sort_index(inplace=True)  # ✅ FIX: Crucial for .shift() and cumulative returns

    df['Position'] = 0

    # Iterating is slow, but keeps logic explicit. 
    # Since data is sorted now, iloc[i-1] correctly refers to the previous day.
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
# BACKTEST WITH RISK MANAGEMENT
# ==========================================
def backtest_with_risk_management(df, stop_loss_z=3.5, take_profit_z=0.0, max_days=10):

    df = df.copy()
    df.sort_index(inplace=True)  # ✅ FIX: Crucial for logic flow

    df['Position'] = 0
    df['Days_Held'] = 0
    df['Exit_Reason'] = None

    pos = 0
    days = 0

    for i in range(1, len(df)):
        z_prev = df['Z_Score'].iloc[i-1]
        signal_prev = df['Signal'].iloc[i-1]

        # EXIT LOGIC
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

        # ENTRY LOGIC
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

# ==========================================
# BOLLINGER MEAN REVERSION STATS (-2σ SIDE)
# ==========================================
def calculate_bollinger_reversion_stats(df):

    required_cols = ['Ratio', 'Mean', 'Lower_Band']
    if not set(required_cols).issubset(df.columns):
        raise ValueError("Required columns missing for Bollinger stats")

    df = df.copy()
    df.sort_index(inplace=True) # ✅ FIX: Sort before processing
    df = df.reset_index(drop=False) # Ensure Date is accessible as a column for the loop

    events = []

    # Identify Date Column (Assuming the first column after reset is the Date/Index)
    date_col = df.columns[0]

    for i in range(1, len(df)):

        # --- Detect fresh -2σ touch ---
        touch_cond = (
            df.loc[i, 'Ratio'] < df.loc[i, 'Lower_Band'] and
            df.loc[i-1, 'Ratio'] >= df.loc[i-1, 'Lower_Band']
        )

        if not touch_cond:
            continue

        touch_price = df.loc[i, 'Ratio']
        touch_date = df.loc[i, date_col]

        # --- Look forward ---
        for j in range(i + 1, len(df)):

            # SUCCESS: Mean touched
            if df.loc[j, 'Ratio'] >= df.loc[j, 'Mean']:
                events.append({
                    "type": "success",
                    "touch_date": touch_date,
                    "mean_date": df.loc[j, date_col],
                    "days_to_mean": (df.loc[j, date_col] - touch_date).days
                })
                break

            # FAILURE: Lower low before mean (Logic Check: Is this failure condition what you want?)
            # Usually failure is defined by Stop Loss or Time, but if Ratio makes a new significant low?
            # Keeping your existing logic:
            if df.loc[j, 'Ratio'] < touch_price:
                events.append({
                    "type": "failure",
                    "touch_date": touch_date
                })
                break

    # --- Aggregate Stats ---
    total = len(events)
    success = sum(e['type'] == 'success' for e in events)
    failure = sum(e['type'] == 'failure' for e in events)

    days = [e['days_to_mean'] for e in events if e['type'] == 'success']

    return {
        "touches": total,
        "mean_reversions": success,
        "failures": failure,
        "success_rate": (success / total * 100) if total > 0 else np.nan,
        "avg_days_to_mean": np.mean(days) if days else np.nan,
        "median_days_to_mean": np.median(days) if days else np.nan,
        "max_days_to_mean": np.max(days) if days else np.nan
    }




# modules/calculation.py
import pandas as pd

def calculate_quarterly_structure(df):
    """
    Calculates synthetic OHLC for the Ratio and aggregates it by Quarter (3 Months).
    Returns a dataframe with daily data merged with quarterly static levels.
    """

    df = df.copy()


    # --- 0. Ensure Datetime Index ---
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df['TIMESTAMP_A'])
        df = df.sort_index()

    # --- 1. Synthetic OHLC Ratio (UNCHANGED LOGIC) ---
    r_open  = df['OPEN_PRICE_A'] / df['OPEN_PRICE_B']
    r_high  = df['HI_PRICE_A']   / df['HI_PRICE_B']
    r_low   = df['LO_PRICE_A']   / df['LO_PRICE_B']
    r_close = df['CLOSE_PRICE_A'] / df['CLOSE_PRICE_B']

    temp_ohlc = pd.DataFrame({
        'RO': r_open,
        'RH': r_high,
        'RL': r_low,
        'RC': r_close
    }, index=df.index)

    df['Ratio_High']  = temp_ohlc.max(axis=1)
    df['Ratio_Low']   = temp_ohlc.min(axis=1)
    df['Ratio_Close'] = r_close

    # --- 2. Quarterly Grouping ---
    quarterly_groups = df.resample('QE')

    # --- 3. Quarterly Stats ---
    q_stats = pd.DataFrame(index=quarterly_groups.size().index)

    q_stats['Q_Highest_Close'] = quarterly_groups['Ratio_Close'].max()
    q_stats['Q_Lowest_Close']  = quarterly_groups['Ratio_Close'].min()
    q_stats['Q_High']          = quarterly_groups['Ratio_High'].max()
    q_stats['Q_Low']           = quarterly_groups['Ratio_Low'].min()
    q_stats['Q_Sessions']      = quarterly_groups['Ratio_Close'].count()

    # --- 4. Bands Logic (UNCHANGED) ---
    q_stats['Q_Hi_Band'] = (q_stats['Q_Highest_Close'] + q_stats['Q_High']) / 2
    q_stats['Q_Lo_Band'] = (q_stats['Q_Lowest_Close']  + q_stats['Q_Low']) / 2
    q_stats['Q_Mean']    = (q_stats['Q_Hi_Band'] + q_stats['Q_Lo_Band']) / 2

    # --- 5. Merge Back to Daily ---
    df['Quarter_End'] = df.index.to_period('Q').to_timestamp(how='end').normalize()
    q_stats.index = q_stats.index.normalize()

    df = pd.merge(
        df,
        q_stats,
        left_on='Quarter_End',
        right_index=True,
        how='left'
    )

    df.fillna(method='ffill', inplace=True)

    return df




def calculate_semiannual_weekly_structure(df):
    """
    Builds WEEKLY OHLC from daily synthetic ratio
    and calculates 6-Month structural bands.
    Logic identical to quarterly chart, only timeframe changed.
    """
    print("1")
    df = df.copy()
    print("Here is the one how is the one:")
    print(df.columns)

    # --- Ensure Datetime Index ---
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df['TIMESTAMP_A'])
        df = df.sort_index()

    # --- WEEKLY OHLC (Holiday Safe) ---
    print("2")
    weekly = df.resample('W-FRI').agg({
        'Ratio_Close': ['first', 'last'],   # Open, Close
        'Ratio_High': 'max',               # High
        'Ratio_Low': 'min'                 # Low
    })
    print("3")

    weekly.columns = ['W_Open', 'W_Close', 'W_High', 'W_Low']
    # weekly.dropna(inplace=True)

    # --- 6 Month Grouping (2 Quarters) ---
    semi_groups = weekly.resample('2Q')

    s_stats = pd.DataFrame(index=semi_groups.size().index)

    s_stats['S_Highest_Close'] = semi_groups['W_Close'].max()
    s_stats['S_Lowest_Close']  = semi_groups['W_Close'].min()
    s_stats['S_High']          = semi_groups['W_High'].max()
    s_stats['S_Low']           = semi_groups['W_Low'].min()
    s_stats['S_Weeks']         = semi_groups['W_Close'].count()
    print("4")

    # --- SAME BAND LOGIC ---
    s_stats['S_Hi_Band'] = (s_stats['S_Highest_Close'] + s_stats['S_High']) / 2
    s_stats['S_Lo_Band'] = (s_stats['S_Lowest_Close']  + s_stats['S_Low']) / 2
    s_stats['S_Mean']    = (s_stats['S_Hi_Band'] + s_stats['S_Lo_Band']) / 2

    # --- Merge Back to Weekly ---
    weekly['Semi_End'] = weekly.index.to_period('2Q').to_timestamp(how='end').normalize()
    s_stats.index = s_stats.index.normalize()

    weekly = pd.merge(
        weekly,
        s_stats,
        left_on='Semi_End',
        right_index=True,
        how='left'
    )

    weekly.fillna(method='ffill', inplace=True)

    print("weekly:",weekly.columns)

    return weekly


from statsmodels.tsa.stattools import adfuller
import numpy as np

def calculate_cointegration_metrics(spread, window=250):
    spread = spread.dropna().tail(window)

    adf_stat, p_value, _, _, critical_values, _ = adfuller(spread, autolag="AIC")
    crit_5 = critical_values["5%"]

    strength = abs(adf_stat - crit_5)

    return {
        "adf_stat": adf_stat,
        "p_value": p_value,
        "crit_5": crit_5,
        "strength": strength,
        "cointegrated": adf_stat < crit_5
    }


def calculate_hurst_exponent(ts):
    ts = ts.dropna().values
    lags = range(2, 20)
    tau = [np.sqrt(np.std(ts[lag:] - ts[:-lag])) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    hurst = poly[0] * 2.0
    return hurst


def calculate_relationship_metrics(df):
    """
    Calculates correlation, covariance and spread variance
    """
    price_a = df["CLOSE_PRICE_A"]
    price_b = df["CLOSE_PRICE_B"]

    correlation = price_a.corr(price_b)
    covariance = price_a.cov(price_b)

    # Spread / Ratio variance
    if "Ratio_Close" in df.columns:
        spread_variance = df["Ratio_Close"].var()
    else:
        spread_variance = np.nan

    return {
        "correlation": correlation,
        "covariance": covariance,
        "spread_variance": spread_variance
    }
