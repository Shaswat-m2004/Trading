


import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
import concurrent.futures # For Parallel Processing

# Custom Modules
from modules.calculation import calculations
from modules.plotting import plotting
from modules import data_loader

# --- HELPERS (Excel & Preprocess) ---
# (Keeping excel logic same)
def dataframe_to_formatted_excel(df, lookback, std_mult):
    df_processed = df.copy()
    stock_a = str((df_processed['SYMBOL_A']).unique()[0])
    stock_b = str((df_processed['SYMBOL_B']).unique()[0])
    
    try:
        df_processed.drop(['INSTRUMENT_A','SYMBOL_A','OPEN_INT*_A','TRD_VAL_A','TRD_QTY_A','NO_OF_CONT_A','NO_OF_TRADE_A',
                           'TIMESTAMP_B','INSTRUMENT_B','SYMBOL_B','OPEN_INT*_B','TRD_VAL_B','TRD_QTY_B','NO_OF_CONT_B','NO_OF_TRADE_B',
                           'NEXT_EXP_DATE_A','NEXT_EXP_DATE_B'], axis=1, inplace=True)
    except KeyError: pass
    
    if 'TIMESTAMP_A' in df_processed.columns: 
        df_processed.rename(columns={'TIMESTAMP_A': 'Date'}, inplace=True)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_processed.to_excel(writer, sheet_name="Pair Data", index=False, startrow=1)
        wb = writer.book
        ws = writer.sheets["Pair Data"]
        
        ws.insert_cols(14); ws.insert_cols(9); ws.insert_cols(2)
        
        # Headers
        ws.merge_cells("C1:H1"); ws["C1"] = stock_a
        ws["C1"].font = Font(bold=True); ws["C1"].alignment = Alignment(horizontal="center")
        
        ws.merge_cells("J1:O1"); ws["J1"] = stock_b
        ws["J1"].font = Font(bold=True); ws["J1"].alignment = Alignment(horizontal="center")
        
        ws.merge_cells("Q1:W1")
        ws["Q1"] = f"INDICATORS (RSI/Z-Score: {lookback}D | Bands: ±{std_mult} SD)"
        ws["Q1"].font = Font(bold=True); ws["Q1"].alignment = Alignment(horizontal="center")

        # Auto-width
        for col in ws.columns:
            max_length = 0
            column = col[1].column_letter 
            for cell in col:
                try: 
                    if len(str(cell.value)) > max_length: max_length = len(str(cell.value))
                except: pass
            ws.column_dimensions[column].width = max(12, (max_length * 1.2))

    buffer.seek(0)
    return buffer

def preprocess_futures(df):
    df = df.copy()
    df.drop(['OPEN_INT_A', 'OPEN_INT_B'], axis=1, inplace=True, errors='ignore')
    for leg in ['A', 'B']:
        date_col = f'TIMESTAMP_{leg}'; expiry_col = f'EXP_DATE_{leg}'; symbol_col = f'SYMBOL_{leg}'; gap_col = f'expiry_gap_{leg}'
        df[date_col] = pd.to_datetime(df[date_col]); df[expiry_col] = pd.to_datetime(df[expiry_col])
        df = df.sort_values([symbol_col, expiry_col, date_col])
        next_exp_col = f'NEXT_EXP_DATE_{leg}'
        df[next_exp_col] = (df.groupby(symbol_col)[expiry_col].shift(-1))
        df[gap_col] = np.where(df[date_col] < df[expiry_col], (df[expiry_col] - df[date_col]).dt.days, (df[next_exp_col] - df[date_col]).dt.days)
        df.loc[df[next_exp_col].isna(), gap_col] = np.nan
    return df

def render_chart_with_csv(fig, df_to_download, lookback, std_mult, filename_prefix="data"):
    st.plotly_chart(fig, use_container_width=True)
    excel_file = dataframe_to_formatted_excel(df_to_download, lookback, std_mult)
    st.download_button("📊 Download Excel", data=excel_file, file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=filename_prefix)

# --- OPTIMIZATION 1: Caching Data Loading & Calculation ---
# Ye function data load karega aur calculations karega.
# Jab tak parameters same hain, ye dobara run nahi hoga -> Instant Speed ⚡
@st.cache_data(show_spinner=False)
def get_cached_data_and_calc(base_dir, sector, stock_a, stock_b, lookback, std_dev_mult, norm_start_date):
    # 1. Load
    raw_df = data_loader.load_pair_data(base_dir, sector, stock_a, stock_b)
    if raw_df is None or raw_df.empty:
        return None, None, None, None

    # 2. Preprocess
    raw_df = preprocess_futures(raw_df)

    # 3. Calculate
    processed_df = calculations.calculate_pair_metrics(raw_df, window=lookback, std_dev_multiplier=std_dev_mult)
    stats = calculations.calculate_bollinger_reversion_stats(processed_df)
    
    # 4. Normalize Data
    norm_df = calculations.calculate_normalized_performance(raw_df, norm_start_date)
    
    return processed_df, stats, norm_df, raw_df

# --- OPTIMIZATION 2: Parallel Plot Generation ---
# Sare charts ek saath generate honge background threads me
def generate_all_plots_parallel(processed_df, norm_df, stock_a, stock_b, std_dev_mult, norm_start_date_str):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks
        future_ratio = executor.submit(plotting.plot_pair_ratio, processed_df, stock_a, stock_b, std_dev_mult)
        
        future_norm = None
        if not norm_df.empty:
            future_norm = executor.submit(plotting.plot_normalized_comparison, norm_df, stock_a, stock_b, norm_start_date_str)
            
        future_rsi = executor.submit(plotting.plot_secondary_indicators, processed_df, std_dev_mult)
        future_dist = executor.submit(plotting.plot_zscore_distribution, processed_df)
        future_step = executor.submit(plotting.plot_quarterly_step_chart, processed_df)
        future_semiannual = executor.submit(plotting.plot_semiannual_weekly_line, processed_df)

        # Collect results
        res_ratio = future_ratio.result()
        res_norm = future_norm.result() if future_norm else (None, None)
        res_rsi = future_rsi.result()
        res_dist = future_dist.result()
        res_step = future_step.result()
        res_semiannual = future_semiannual.result()
        
    return res_ratio, res_norm, res_rsi, res_dist, res_step, res_semiannual


# --- MAIN RUN FUNCTION ---
def run(BASE_DIR, selected_sector, stock_a, stock_b, lookback, std_dev_mult, norm_start_date):
    
    st.header("📈 Pro Quant Chart Studio")
    
    if not selected_sector:
        st.info("👈 Please select a sector from the sidebar to begin.")
        return

    st.markdown(f"**Analyzing:** {stock_a} vs {stock_b} | **Sector:** {selected_sector}")

    if stock_a != stock_b:
        # --- STEP 1: Fast Data & Calculation (Cached) ---
        with st.spinner("⚡ Crunching Numbers..."):
            processed_df, stats, norm_df, raw_df = get_cached_data_and_calc(
                BASE_DIR, selected_sector, stock_a, stock_b, lookback, std_dev_mult, norm_start_date
            )

        if processed_df is not None:
            
            # --- STEP 2: Metrics (Instant Display) ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("-2σ Touches", stats["touches"])
            m2.metric("Reversions", f"{stats['mean_reversions']} ({stats['success_rate']:.1f}%)")
            m3.metric("Failures", stats["failures"])
            m4.metric("Avg Days", f"{stats['avg_days_to_mean']:.1f}")

            # --- STEP 3: Parallel Plotting (Background Generation) ---
            # Chart objects generate honge parallel threads me
            (fig_ratio, data_ratio), (fig_norm, data_norm), (fig_rsi, data_rsi), fig_dist, fig_step, fig_semiannual = generate_all_plots_parallel(
                processed_df, norm_df, stock_a, stock_b, std_dev_mult, str(norm_start_date)
            )

            # --- STEP 4: Render ---
            # 1. Bollinger Chart
            st.subheader("1. Price Ratio & Bollinger Bands")
            render_chart_with_csv(fig_ratio, data_ratio, lookback, std_dev_mult, "bollinger_ratio_data")
            
            st.divider()

            # 2. Normalized Chart
            st.subheader("2. Normalized Performance")
            if fig_norm:
                render_chart_with_csv(fig_norm, data_norm, lookback, std_dev_mult, "normalized_data")
            else:
                st.warning("No data found for Normalized Chart after start date.")
            
            st.divider()

            # 3. RSI Chart
            st.subheader("3. RSI Momentum")
            render_chart_with_csv(fig_rsi, data_rsi, lookback, std_dev_mult, "rsi_data")
            
            st.divider()

            # 4 & 5 Stats
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("4. Z-Score Dist")
                st.plotly_chart(fig_dist, use_container_width=True)
            with c2:
                st.subheader("5. Quarterly Stats")
                st.plotly_chart(fig_step, use_container_width=True)
            
            st.subheader("6. Semiannual Weekly Chart")
            st.plotly_chart(fig_semiannual, use_container_width=True)

        else: 
            st.error("Not enough overlapping data found for this pair.")
    else: 
        st.warning("⚠️ Please select two **different** stocks in the sidebar.")