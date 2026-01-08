

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from scipy import stats
import numpy as np


def plot_pair_ratio(df, stock_a, stock_b, std_dev_val, start_date=None, end_date=None):
    """
    Returns: fig, plot_df
    """
    # --- DATE FILTERING ---
    plot_df = df.copy()
    if start_date:
        plot_df = plot_df[plot_df.index >= pd.to_datetime(start_date)]
    if end_date:
        plot_df = plot_df[plot_df.index <= pd.to_datetime(end_date)]

    if plot_df.empty:
        raise ValueError("No data available in selected date range.")

    fig = go.Figure()

    # --- Upper Band ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Upper_Band'],
        mode='lines',
        name=f'+{std_dev_val} σ',
        line=dict(color='#00FF00', width=1),
        opacity=0.5,
        # Minimal Tooltip
        hovertemplate='Upper: %{y:.2f}<extra></extra>' 
    ))

    # --- Lower Band ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Lower_Band'],
        mode='lines',
        name=f'-{std_dev_val} σ',
        line=dict(color='#FF3333', width=1),
        fill='tonexty', fillcolor='rgba(255,255,255,0.05)',
        opacity=0.5,
        # Minimal Tooltip
        hovertemplate='Lower: %{y:.2f}<extra></extra>'
    ))

    # --- Mean (SMA) ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Mean'],
        mode='lines', name='Mean',
        line=dict(color='#FFD700', width=2),
        # Minimal Tooltip
        hovertemplate='Mean: %{y:.2f}<extra></extra>'
    ))

    # --- Ratio (Main Line) ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Ratio'],
        mode='lines', name=f'Ratio',
        line=dict(color="#EEF3F3", width=3),
        # Minimal Tooltip (Bold Value)
        hovertemplate='<b>Ratio: %{y:.4f}</b><extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=f"Pair Trading Ratio: {stock_a} vs {stock_b}", font=dict(size=18, color="white")),
        xaxis_title="Date", yaxis_title="Price Ratio",
        template="plotly_dark", height=650, 
        
        # --- 1. USE 'x' MODE (Splits the big box into small labels) ---
        hovermode="x", 
        
        # --- 2. MAKE LABELS TRANSPARENT (See-through) ---
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0.4)",  # 40% Transparent Black
            bordercolor="rgba(255,255,255,0.3)",
            font_size=12, 
            font_family="monospace",
            font_color="white"
        ),
        
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1
        ),
        margin=dict(r=20)
    )

    # --- 3. KEEP CROSSHAIRS FOR AXIS READING ---
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)',
        showspikes=True, spikemode='across', spikesnap='cursor', 
        showline=False, spikedash='dash', spikecolor="grey", spikethickness=1
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)',
        showspikes=True, spikemode='across', spikesnap='cursor', 
        showline=False, spikedash='dash', spikecolor="grey", spikethickness=1
    )

    return fig, plot_df


def plot_one_month_ratio(df, stock_a, stock_b, std_dev_val):
    """
    Plots the Pair Ratio specifically for the last 1 Month of data.
    """
    # ... (Date Filtering) ...
    last_date = df.index.max()
    start_date = last_date - pd.DateOffset(months=1)
    plot_df = df[df.index >= start_date].copy()

    if plot_df.empty:
        plot_df = df.tail(22)

    # --- NEW: COUNT TRADING DAYS ---
    trading_days_count = len(plot_df)
    # -------------------------------

    fig = go.Figure()

    # --- Upper Band ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Upper_Band'],
        mode='lines',
        name=f'+{std_dev_val} Std Dev',
        line=dict(color='#00FF00', width=1),
        opacity=0.5, hoverinfo='skip'
    ))

    # --- Lower Band ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Lower_Band'],
        mode='lines',
        name=f'-{std_dev_val} Std Dev',
        line=dict(color='#FF3333', width=1),
        fill='tonexty', fillcolor='rgba(255,255,255,0.05)',
        opacity=0.5, hoverinfo='skip'
    ))

    # --- Mean ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Mean'],
        mode='lines', name='Mean (SMA)',
        line=dict(color='#FFD700', width=2),
        hovertemplate='%{y:.4f}'
    ))

    # --- Ratio ---
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Ratio'],
        mode='lines+markers',
        name=f'Ratio ({stock_a}/{stock_b})',
        line=dict(color="#EEF3F3", width=3),
        marker=dict(size=6),
        hovertemplate='%{y:.4f}'
    ))

    fig.update_layout(
        title=dict(
            # --- UPDATED TITLE WITH COUNT ---
            text=f"Last 30 Days Zoom: {stock_a} vs {stock_b} ({trading_days_count} Trading Days)", 
            font=dict(size=18, color="white")
        ),
        xaxis_title="Date", 
        yaxis_title="Price Ratio",
        template="plotly_dark", 
        height=550,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(0,0,0,0.8)", font_size=14, font_family="monospace"),
        
        # Legend at Top (Right aligned)
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1
        ),
        margin=dict(r=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')

    return fig, plot_df

def plot_normalized_comparison(norm_df, stock_a_name, stock_b_name, start_date_str):
    """
    Plots two lines starting at 100 to compare percentage growth.
    """
    fig = go.Figure()

    # Line for Stock A (e.g., Green/Blue)
    fig.add_trace(go.Scatter(
        x=norm_df.index, y=norm_df['Norm_A'],
        mode='lines', 
        name=f"{stock_a_name} (Base 100)",
        line=dict(color='#00FF80', width=2.5) # Neon Green
    ))

    # Line for Stock B (e.g., Red/Orange)
    fig.add_trace(go.Scatter(
        x=norm_df.index, y=norm_df['Norm_B'],
        mode='lines', 
        name=f"{stock_b_name} (Base 100)",
        line=dict(color='#FF4136', width=2.5) # Neon Red
    ))

    # Add a baseline at 100 for reference
    fig.add_hline(y=100, line_dash="dot", line_color="gray", opacity=0.7)

    fig.update_layout(
        title=dict(
            text=f"Performance Comparison (Base 100 since {start_date_str})",
            font=dict(size=18, color="white")
        ),
        yaxis_title="Normalized Value (Started at 100)",
        xaxis_title="Date",
        template="plotly_dark",
        height=550,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1
        ),
        margin=dict(r=20)
    )
    
    return fig, norm_df

def plot_secondary_indicators(df, std_dev_val):
    """
    Plots only RSI of Ratio (Momentum).
    (std_dev_val is kept in arguments for compatibility with app.py calls, but not used)
    
    Returns: fig, df
    """
    # We switched from make_subplots to go.Figure since it is now a single chart
    fig = go.Figure()

    # --- RSI Line ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'],
        mode='lines', name='RSI (14)',
        line=dict(color='#FFA500', width=1.5),
        hovertemplate='RSI: %{y:.1f}<extra></extra>'
    ))

    # --- Overbought/Oversold Levels ---
    fig.add_hline(y=70, line_dash="dot", line_color="gray", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dot", line_color="gray", annotation_text="Oversold")

    # --- Layout ---
    fig.update_layout(
        title="RSI Momentum",
        template="plotly_dark",
        height=350,  # Reduced height since it is now a single plot
        hovermode="x unified",
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False,
        yaxis=dict(range=[0, 100]) # Fix Y-axis range for RSI
    )
    
    # RETURN BOTH FIG AND DATA
    return fig, df

def plot_recent_trends(df, std_dev_mult):
    """
    Returns: fig, df (with new calculated columns included)
    """
    # Create a copy so we don't mess up the original dataframe outside this function
    calc_df = df.copy()

    # 20-Day Stats
    calc_df['SMA_20'] = calc_df['Ratio'].rolling(window=20).mean()
    calc_df['STD_20'] = calc_df['Ratio'].rolling(window=20).std()
    calc_df['Upper_20'] = calc_df['SMA_20'] + (std_dev_mult * calc_df['STD_20'])
    calc_df['Lower_20'] = calc_df['SMA_20'] - (std_dev_mult * calc_df['STD_20'])
    
    # 50-Day Stats
    calc_df['SMA_50'] = calc_df['Ratio'].rolling(window=50).mean()
    calc_df['STD_50'] = calc_df['Ratio'].rolling(window=50).std()
    calc_df['Upper_50'] = calc_df['SMA_50'] + (std_dev_mult * calc_df['STD_50'])
    calc_df['Lower_50'] = calc_df['SMA_50'] - (std_dev_mult * calc_df['STD_50'])
    
    df_20 = calc_df.tail(20)
    df_50 = calc_df.tail(50)

    fig = make_subplots(rows=2, cols=1, subplot_titles=("Last 20 Days", "Last 50 Days"), vertical_spacing=0.15)

    # GRAPH 1: LAST 20 DAYS
    fig.add_trace(go.Scatter(x=df_20.index, y=df_20['Upper_20'], mode='lines', line=dict(color='gray', width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_20.index, y=df_20['Lower_20'], mode='lines', line=dict(color='gray', width=0), fill='tonexty', fillcolor='rgba(0, 255, 255, 0.1)', showlegend=False, hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_20.index, y=df_20['SMA_20'], mode='lines', name='SMA (20)', line=dict(color='#FFA500', width=2, dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_20.index, y=df_20['Ratio'], mode='lines+markers', name='Ratio (20d)', line=dict(color='#FFFFFF', width=2), marker=dict(size=4)), row=1, col=1)

    # GRAPH 2: LAST 50 DAYS
    fig.add_trace(go.Scatter(x=df_50.index, y=df_50['Upper_50'], mode='lines', line=dict(color='gray', width=0), showlegend=False, hoverinfo='skip'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_50.index, y=df_50['Lower_50'], mode='lines', line=dict(color='gray', width=0), fill='tonexty', fillcolor='rgba(255, 0, 255, 0.1)', showlegend=False, hoverinfo='skip'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_50.index, y=df_50['SMA_50'], mode='lines', name='SMA (50)', line=dict(color='#FFFF00', width=2, dash='dash')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_50.index, y=df_50['Ratio'], mode='lines', name='Ratio (50d)', line=dict(color='#EEF3F3', width=2)), row=2, col=1)

    fig.update_layout(template="plotly_dark", height=700, hovermode="x unified", showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    # RETURN BOTH FIG AND THE CALCULATED DATA
    return fig, calc_df

def plot_zscore_with_signals(df, z_threshold=2.0):
    """
    Returns: fig, df
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Z_Score'], mode='lines', name='Z-Score', line=dict(color='#BD00FF', width=2), opacity=0.8))

    fig.add_hline(y=z_threshold, line_dash="dot", line_color="#FF3333", annotation_text="Sell Zone")
    fig.add_hline(y=-z_threshold, line_dash="dot", line_color="#00FF00", annotation_text="Buy Zone")
    fig.add_hline(y=0, line_color="gray", line_width=1)

    long_signals = df[df['Signal'] == 1]
    short_signals = df[df['Signal'] == -1]

    fig.add_trace(go.Scatter(x=long_signals.index, y=long_signals['Z_Score'], mode='markers', name='Entry Long', marker=dict(symbol='triangle-up', size=12, color='#00FF00', line=dict(width=1, color='black')), hovertemplate='<b>ENTRY LONG</b><br>Z: %{y:.2f}<br>RSI Oversold<extra></extra>'))
    fig.add_trace(go.Scatter(x=short_signals.index, y=short_signals['Z_Score'], mode='markers', name='Entry Short', marker=dict(symbol='triangle-down', size=12, color='#FF0000', line=dict(width=1, color='black')), hovertemplate='<b>ENTRY SHORT</b><br>Z: %{y:.2f}<br>RSI Overbought<extra></extra>'))

    fig.update_layout(title="Strategy Signals: Z-Score + RSI Confluence", xaxis_title="Date", yaxis_title="Sigma (Z-Score)", template="plotly_dark", height=500, hovermode="x unified")

    return fig, df

def plot_advanced_signals(df, z_threshold, stop_loss_z):
    """
    Returns: fig, df
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Z_Score'], mode='lines', name='Z-Score', line=dict(color='gray', width=1)))

    fig.add_hline(y=0, line_color="white", line_width=1)
    fig.add_hline(y=z_threshold, line_dash="dot", line_color="#00FF00", annotation_text="Sell Zone")
    fig.add_hline(y=-z_threshold, line_dash="dot", line_color="#00FF00", annotation_text="Buy Zone")
    fig.add_hline(y=stop_loss_z, line_color="red", line_width=2, annotation_text="STOP LOSS (+)")
    fig.add_hline(y=-stop_loss_z, line_color="red", line_width=2, annotation_text="STOP LOSS (-)")

    entries = df[ (df['Signal'] != 0) & (df['Position'].shift(1) == 0) ]
    fig.add_trace(go.Scatter(x=entries.index, y=entries['Z_Score'], mode='markers', name='Entry', marker=dict(symbol='triangle-up', size=12, color='yellow')))

    tp_exits = df[df['Exit_Reason'] == "TP: Mean Reversion"]
    fig.add_trace(go.Scatter(x=tp_exits.index, y=tp_exits['Z_Score'], mode='markers', name='Take Profit', marker=dict(symbol='circle', size=10, color='#00FF00', line=dict(width=2, color='black'))))

    sl_exits = df[df['Exit_Reason'] == "SL: Regime Break"]
    fig.add_trace(go.Scatter(x=sl_exits.index, y=sl_exits['Z_Score'], mode='markers', name='Stop Loss', marker=dict(symbol='x', size=10, color='red', line=dict(width=2, color='white'))))

    ts_exits = df[df['Exit_Reason'] == "Time Stop"]
    fig.add_trace(go.Scatter(x=ts_exits.index, y=ts_exits['Z_Score'], mode='markers', name='Time Stop', marker=dict(symbol='square', size=10, color='orange', line=dict(width=2, color='black'))))

    fig.update_layout(title="Risk-Managed Trades: Entries vs Exits", template="plotly_dark", height=500)
    
    return fig, df




def plot_zscore_distribution(df):
    """
    Plots the Histogram of Z-Scores with a Bell Curve overlay.
    Shows 'Where we are now' with a marker.
    """
    # Clean data (remove NaNs)
    z_data = df['Z_Score'].dropna()
    
    if z_data.empty:
        return go.Figure()

    current_z = z_data.iloc[-1]
    mean_val = z_data.mean()
    std_val = z_data.std()

    # 1. Create the Histogram (The Real Body)
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=z_data,
        histnorm='probability density',
        name='Historical Z-Scores',
        marker_color='#333333',
        opacity=0.6,
        nbinsx=50
    ))

    # 2. Create the Bell Curve (The Ideal Shape) 💃
    x_range = np.linspace(z_data.min(), z_data.max(), 100)
    pdf = stats.norm.pdf(x_range, mean_val, std_val)
    
    fig.add_trace(go.Scatter(
        x=x_range, y=pdf,
        mode='lines',
        name='Normal Distribution',
        line=dict(color='#BD00FF', width=3) # Purple line
    ))

    # 3. Mark the Current Position (Where we are tonight)
    # We find the height of the curve at the current Z to place the marker perfectly
    current_pdf = stats.norm.pdf(current_z, mean_val, std_val)
    
    fig.add_trace(go.Scatter(
        x=[current_z], y=[current_pdf],
        mode='markers+text',
        name='Current Z-Score',
        text=[f"Current: {current_z:.2f}"],
        textposition="top center",
        marker=dict(size=15, color='#00FF00', line=dict(width=2, color='white'))
    ))

    # 4. Add Threshold Lines (The Danger Zones)
    fig.add_vline(x=2.0, line_dash="dot", line_color="#FF3333", annotation_text="+2σ")
    fig.add_vline(x=-2.0, line_dash="dot", line_color="#00FF00", annotation_text="-2σ")

    fig.update_layout(
        title="Z-Score Distribution (Bell Curve Analysis)",
        xaxis_title="Sigma (Standard Deviations)",
        yaxis_title="Probability Density",
        template="plotly_dark",
        height=450,
        showlegend=True,
        bargap=0.1
    )

    return fig


# import pandas as pd
# import plotly.graph_objects as go

def plot_quarterly_step_chart(df):
    """
    Expects a DataFrame with a DateTime Index and a column named 'Ratio'.
    Visualizes 3-Month Step Statistics (Mean, High, Low) with Trading Day counts.
    """

    grouper = df.groupby(pd.Grouper(freq='QE'))
    
    df = df.copy() # Work on a copy to avoid SettingWithCopy warnings
    df['Q_Mean']  = grouper['Ratio'].transform('mean')
    df['Q_Max']   = grouper['Ratio'].transform('max')
    df['Q_Min']   = grouper['Ratio'].transform('min')
    df['Q_Count'] = grouper['Ratio'].transform('count')


    quarter_labels = df.groupby(pd.Grouper(freq='QE')).last().dropna(subset=['Ratio'])

    # 3. Build Plot
    fig = go.Figure()

    # --- A. Main Ratio Line (Dynamic) ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Ratio'],
        mode='lines', name='Price Ratio',
        line=dict(color='white', width=1),
        opacity=0.7
    ))

    # --- B. 3-Month High (Flat Green Step) ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Q_Max'],
        mode='lines', name='3M High',
        line=dict(color='#00ff00', width=1.5)
    ))

    # --- C. 3-Month Low (Flat Red Step) ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Q_Min'],
        mode='lines', name='3M Low',
        line=dict(color='#ff0000', width=1.5)
    ))

    # --- D. 3-Month Mean (Flat Yellow Step) ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Q_Mean'],
        mode='lines', name='3M Mean',
        line=dict(color='yellow', width=2.5)
    ))

    # --- E. Add Trading Days Annotations ---
    # We place the text in the middle of the quarter visually
    for date, row in quarter_labels.iterrows():
        # Approximate the visual center of the quarter for the text
        mid_date = date - pd.DateOffset(days=45) 
        
        fig.add_annotation(
            x=mid_date,
            y=row['Q_Max'], # Position text at the High line
            text=f"{int(row['Q_Count'])} Days",
            showarrow=False,
            yshift=10,
            font=dict(color='cyan', size=10)
        )

    # 4. Styling (Dark Theme)
    fig.update_layout(
        title='Pair Ratio: 3-Month Fixed Statistics (Step Chart)',
        template='plotly_dark',
        height=600,
        hovermode='x unified',
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig




# import pandas as pd
# import plotly.graph_objects as go

def plot_semiannual_weekly_line(df):
    """
    1. Resamples Daily 'Ratio' to Weekly Data.
    2. Groups Weeks into 6-Month Blocks (Semi-Annual).
    3. Visualizes Weekly Close Line vs 6-Month Fixed Statistics.
    """
    
    # --- Step 1: Resample Daily to Weekly ---
    # We use .ohlc() to grab the specific Friday Close ('close') for the line
    weekly_df = df['Ratio'].resample('W').ohlc()
    weekly_df.columns = ['W_Open', 'W_High', 'W_Low', 'W_Close']

    # --- Step 2: Calculate 6-Month Statistics ---
    # Group by 6 Months ('6ME' for modern pandas, or '6M' for older)
    grouper = weekly_df.groupby(pd.Grouper(freq='6ME'))
    
    # Statistics based on the Weekly Close
    weekly_df['Semi_Mean']  = grouper['W_Close'].transform('mean')
    weekly_df['Semi_Max']   = grouper['W_High'].transform('max') # Max of the weekly highs
    weekly_df['Semi_Min']   = grouper['W_Low'].transform('min')  # Min of the weekly lows
    weekly_df['Week_Count'] = grouper['W_Close'].transform('count')

    # Get labels for annotations
    semiannual_labels = weekly_df.groupby(pd.Grouper(freq='6ME')).last().dropna(subset=['W_Close'])

    # --- Step 3: Build Plot ---
    fig = go.Figure()

    # A. Main Line (Weekly Close) - Replacing Candles
    fig.add_trace(go.Scatter(
        x=weekly_df.index, 
        y=weekly_df['W_Close'],
        mode='lines', 
        name='Weekly Ratio (Fri)',
        line=dict(color='white', width=1),
        opacity=0.8
    ))

    # B. 6-Month High (Green Step)
    fig.add_trace(go.Scatter(
        x=weekly_df.index, y=weekly_df['Semi_Max'],
        mode='lines', name='6M High',
        line=dict(color='#00ff00', width=1.5)
    ))

    # C. 6-Month Low (Red Step)
    fig.add_trace(go.Scatter(
        x=weekly_df.index, y=weekly_df['Semi_Min'],
        mode='lines', name='6M Low',
        line=dict(color='#ff0000', width=1.5)
    ))

    # D. 6-Month Mean (Yellow Step)
    fig.add_trace(go.Scatter(
        x=weekly_df.index, y=weekly_df['Semi_Mean'],
        mode='lines', name='6M Mean',
        line=dict(color='yellow', width=2.5)
    ))

    # E. Annotations (Week Counts)
    for date, row in semiannual_labels.iterrows():
        # Center text visually in the 6-month block (approx 13 weeks back)
        mid_date = date - pd.DateOffset(weeks=13)
        
        fig.add_annotation(
            x=mid_date,
            y=row['Semi_Max'], 
            text=f"{int(row['Week_Count'])} Weeks",
            showarrow=False,
            yshift=15,
            font=dict(color='cyan', size=11, family="monospace")
        )

    # --- Step 4: Styling ---
    fig.update_layout(
        title='<b>Semi-Annual Breakdown:</b> Weekly Ratio Line vs 6-Month Stats',
        template='plotly_dark',
        height=600,
        hovermode='x unified',
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig