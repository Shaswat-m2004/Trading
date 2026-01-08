

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
    df = df.sort_index()

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

# ==========================================
# BOLLINGER MEAN REVERSION STATS (-2σ SIDE)
# ==========================================

def calculate_bollinger_reversion_stats(df):

    required_cols = ['Ratio', 'Mean', 'Lower_Band']
    if not set(required_cols).issubset(df.columns):
        raise ValueError("Required columns missing for Bollinger stats")

    df = df.copy()
    df = df.reset_index(drop=False)  # ensure Date column exists

    events = []

    for i in range(1, len(df)):

        # --- Detect fresh -2σ touch ---
        touch_cond = (
            df.loc[i, 'Ratio'] < df.loc[i, 'Lower_Band'] and
            df.loc[i-1, 'Ratio'] >= df.loc[i-1, 'Lower_Band']
        )

        if not touch_cond:
            continue

        touch_price = df.loc[i, 'Ratio']
        touch_date = df.loc[i, df.columns[0]]  # Date or index

        # --- Look forward ---
        for j in range(i + 1, len(df)):

            # SUCCESS: Mean touched
            if df.loc[j, 'Ratio'] >= df.loc[j, 'Mean']:
                events.append({
                    "type": "success",
                    "touch_date": touch_date,
                    "mean_date": df.loc[j, df.columns[0]],
                    "days_to_mean": (df.loc[j, df.columns[0]] - touch_date).days
                })
                break

            # FAILURE: Lower low before mean
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
