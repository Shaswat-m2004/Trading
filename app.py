# # # # import streamlit as st
# # # # import plotly.graph_objects as go
# # # # # Import custom modules
# # # # from modules.calculation import calculations
# # # # from modules.plotting import plotting
# # # # from modules import data_loader
# # # # import pandas as pd
# # # # # --- PAGE CONFIG ---
# # # # st.set_page_config(layout="wide", page_title="One-to-One Pair Trader")

# # # # # ==========================================
# # # # # HELPER FUNCTION: DOWNLOAD CSV
# # # # # ==========================================
# # # # def render_chart_with_csv(fig, df_to_download, filename_prefix="chart_data", height=None):
# # # #     """
# # # #     Displays a Plotly chart and provides a button to download its specific data.
# # # #     """
# # # #     # 1. Show the Chart
# # # #     st.plotly_chart(fig, use_container_width=True, key=f"chart_{filename_prefix}")
    
# # # #     # 2. Prepare Data for Download
# # # #     csv_data = df_to_download.to_csv().encode('utf-8')
    
# # # #     # 3. Create Download Button (Right aligned)
# # # #     col1, col2 = st.columns([6, 1]) 
# # # #     with col1:
# # # #         st.download_button(
# # # #             label="📥 Download Data",
# # # #             data=csv_data,
# # # #             file_name=f"{filename_prefix}.csv",
# # # #             mime="text/csv",
# # # #             key=f"btn_{filename_prefix}" # Unique key prevents Streamlit errors
# # # #         )

# # # # # ==========================================
# # # # # MAIN APP UI
# # # # # ==========================================

# # # # st.title("⚖️ One-to-One Pair Trading Analysis")
# # # # st.markdown("---")

# # # # # --- SIDEBAR: SELECTION ---
# # # # st.sidebar.header("1. Select Pair")

# # # # # A. Sector Selection
# # # # sectors = data_loader.get_sectors()
# # # # selected_sector = st.sidebar.selectbox("Select Sector", sectors)

# # # # if selected_sector:
# # # #     # B. Stock Selection
# # # #     stocks = data_loader.get_stocks(selected_sector)
    
# # # #     col1, col2 = st.sidebar.columns(2)
# # # #     with col1:
# # # #         stock_a = st.selectbox("Stock A (Long)", stocks, index=0 if len(stocks) > 0 else None)
# # # #     with col2:
# # # #         default_idx = 1 if len(stocks) > 1 else 0
# # # #         stock_b = st.selectbox("Stock B (Short)", stocks, index=default_idx)

# # # #     # --- SIDEBAR: PARAMETERS ---
# # # #     st.sidebar.divider()
# # # #     st.sidebar.header("2. Analysis Parameters")
    
# # # #     lookback = st.sidebar.number_input("Lookback Period (Days)", min_value=5, max_value=200, value=20)
# # # #     std_dev_mult = st.sidebar.slider("Std Deviation Multiplier", min_value=0.5, max_value=4.0, value=2.0, step=0.1)

# # # #     # --- MAIN EXECUTION ---
# # # #     if stock_a and stock_b:
# # # #         if stock_a == stock_b:
# # # #             st.warning("⚠️ Please select two different stocks to create a pair.")
# # # #         else:
# # # #             # 1. Load & Process Data (Common for all tabs)
# # # #             with st.spinner("Crunching Numbers..."):
# # # #                 raw_df = data_loader.load_pair_data(selected_sector, stock_a, stock_b)

                
# # # #                 # print(raw_df.head())

# # # #             if raw_df is not None and not raw_df.empty:
# # # #                 # Calculate Metrics once
# # # #                 processed_df = calculations.calculate_pair_metrics(raw_df, window=lookback, std_dev_multiplier=std_dev_mult)
                
# # # #                 if processed_df.empty:
# # # #                     st.error(f"Not enough data overlap. Need at least {lookback} common trading days.")
# # # #                     st.stop()

# # # #                 # Generate Signals
# # # #                 z_thresh = 2.0 
# # # #                 df_signals = calculations.generate_trade_signals(processed_df, z_threshold=z_thresh, rsi_upper=70, rsi_lower=30)

# # # #                 # --- DASHBOARD HEADER ---
# # # #                 # Show current status at the top
# # # #                 last_row = df_signals.iloc[-1]
# # # #                 st.markdown(f"### Current Status: **{stock_a} / {stock_b}**")
                
# # # #                 kpi1, kpi2, kpi3, kpi4 = st.columns(4)
# # # #                 kpi1.metric("Current Ratio", f"{last_row['Ratio']:.2f}")
# # # #                 kpi2.metric("Z-Score", f"{last_row['Z_Score']:.2f}", delta_color="inverse")
# # # #                 kpi3.metric("RSI (14)", f"{last_row['RSI']:.1f}")
# # # #                 # kpi4.metric("Active Signal", last_row['Signal_Label'], 
# # # #                             # delta="ACTION REQ" if last_row['Signal'] != 0 else None)
                
# # # #                 default_start = pd.to_datetime("2018-01-01") 
# # # #                 norm_start_date = st.sidebar.date_input("Start Date", value=default_start)
# # # #                 st.markdown("---")

# # # #                 # --- TABS LAYOUT ---
# # # #                 tab1, tab2, tab3 = st.tabs(["📈 Market Analysis", "⚡ Trade Signals", "🛡️ Backtest & Risk"])

# # # #                 # ==========================================
# # # #                 # TAB 1: MARKET ANALYSIS
# # # #                 # ==========================================
# # # #                 with tab1:
# # # #                     st.subheader(f"Price Ratio Analysis ({lookback} Day Mean)")
                    
# # # #                     # 1. MAIN RATIO CHART (Full Width)
# # # #                     fig_main, data_main = plotting.plot_pair_ratio(processed_df, stock_a, stock_b, std_dev_mult)
# # # #                     render_chart_with_csv(fig_main, data_main, filename_prefix="main_ratio_chart")

# # # #                     st.divider()

# # # #                     st.subheader(f"Cumulative Performance Comparison (Base 100)")
                    
# # # #                     # 1. Calculate Normalized Data
# # # #                     norm_df = calculations.calculate_normalized_performance(raw_df, norm_start_date)
                    
# # # #                     if not norm_df.empty:
# # # #                         # --- NEW: CALCULATE DOMINANCE ---
# # # #                         dom_stats = calculations.calculate_dominance_stats(norm_df)
                        
# # # #                         # Display Dominance Metrics
# # # #                         if dom_stats:
# # # #                             st.markdown("##### 🏆 Performance Dominance (Days Leading)")
# # # #                             d1, d2, d3, d4 = st.columns(4)
                            
# # # #                             # Helper to format color
# # # #                             def get_color(val): return "normal" if val < 50 else "inverse"

# # # #                             with d1:
# # # #                                 st.metric(f"All-Time: {stock_a}", f"{dom_stats['hist_a']:.1f}%", delta="Historical Lead")
# # # #                             with d2:
# # # #                                 st.metric(f"All-Time: {stock_b}", f"{dom_stats['hist_b']:.1f}%", delta="Historical Lead")
# # # #                             with d3:
# # # #                                 st.metric(f"Last 3M: {stock_a}", f"{dom_stats['rec_a']:.1f}%", delta="Recent Trend")
# # # #                             with d4:
# # # #                                 st.metric(f"Last 3M: {stock_b}", f"{dom_stats['rec_b']:.1f}%", delta="Recent Trend")
                        
# # # #                         st.caption(f"Shows the % of trading days where one stock outperformed the other since {norm_start_date}.")
# # # #                         # --------------------------------

# # # #                         # 2. Plot the chart
# # # #                         fig_norm, data_norm = plotting.plot_normalized_comparison(norm_df, stock_a, stock_b, str(norm_start_date))
# # # #                         render_chart_with_csv(fig_norm, data_norm, filename_prefix="normalized_comparison_base100")
# # # #                     else:
# # # #                          st.warning(f"No data available after the selected start date: {norm_start_date}")
                    
# # # #                     st.divider()

# # # #                     # Create Columns for smaller charts
# # # #                     col_t1, col_t2 = st.columns(2)
                    
# # # #                     # --- LEFT COLUMN: ZOOMED VIEW ---
# # # #                     with col_t1:
# # # #                         st.subheader("🔍 Zoom: Last 30 Days")
# # # #                         # Use the 1-month plotting function here
# # # #                         fig_month, data_month = plotting.plot_one_month_ratio(processed_df, stock_a, stock_b, std_dev_mult)
# # # #                         # Unique prefix for this chart
# # # #                         render_chart_with_csv(fig_month, data_month, filename_prefix="last_month_ratio")
                    
# # # #                     # --- RIGHT COLUMN: SECONDARY INDICATORS ---
# # # #                     with col_t2:
# # # #                         st.subheader("📉 Momentum (RSI)")
# # # #                         fig_secondary, data_secondary = plotting.plot_secondary_indicators(processed_df, std_dev_mult)
# # # #                         # Unique prefix for this chart
# # # #                         render_chart_with_csv(fig_secondary, data_secondary, filename_prefix="secondary_indicators_chart")

# # # #                         # ... rest of your code (Trends, Indicators etc.) ...
                    
                   

# # # #                 # ==========================================
# # # #                 # TAB 2: TRADE SIGNALS
# # # #                 # ==========================================
# # # #                 with tab2:
# # # #                     st.subheader("Algorithmic Trade Signals")
                    
# # # #                     with st.expander("ℹ️ How Signals are Generated? (Click to Expand)", expanded=False):
# # # #                         st.markdown("""
# # # #                         1. **Entry Long:** Z-Score < -2.0 **AND** RSI < 30 (Oversold).
# # # #                         2. **Entry Short:** Z-Score > +2.0 **AND** RSI > 70 (Overbought).
# # # #                         3. **Exit:** Based on Mean Reversion or Stop Loss (See Backtest Tab).
# # # #                         """)

# # # #                     # 4. SIGNALS CHART
# # # #                     fig_signals, data_signals = plotting.plot_zscore_with_signals(df_signals, z_threshold=z_thresh)
# # # #                     render_chart_with_csv(fig_signals, data_signals, filename_prefix="trade_signals_chart")

# # # #                     st.divider()
# # # #                     st.subheader("Recent Trade Calls Log")

# # # #                     # Filter last 10 signals
# # # #                     filter_signals = df_signals[df_signals['Signal'] != 0].tail(10)

# # # #                     # ✅ FORCE correct price columns
# # # #                     required_cols = ['CLOSE_PRICE_A', 'CLOSE_PRICE_B', 'Ratio', 'Z_Score', 'RSI', 'Signal_Label']

# # # #                     missing = [c for c in required_cols if c not in filter_signals.columns]
# # # #                     if missing:
# # # #                         st.error(f"Missing columns in trade log: {missing}")
# # # #                     else:
# # # #                         # Select only correct columns
# # # #                         recent_trades = filter_signals[required_cols].rename(columns={
# # # #                             'CLOSE_PRICE_A': f"{stock_a} (Long)",
# # # #                             'CLOSE_PRICE_B': f"{stock_b} (Short)"
# # # #                         })

# # # #                         # Display table
# # # #                         st.dataframe(
# # # #                             recent_trades.style.map(
# # # #                                 lambda x: 'color: #00FF00; font-weight: bold' if 'LONG' in str(x) else ('color: #FF4B4B; font-weight: bold' if 'SHORT' in str(x) else ''),
# # # #                                 subset=['Signal_Label']
# # # #                             ).format("{:.2f}", subset=[f"{stock_a} (Long)", f"{stock_b} (Short)", 'Ratio', 'Z_Score', 'RSI']),
# # # #                             use_container_width=True
# # # #                         )

# # # #                 # ==========================================
# # # #                 # TAB 3: BACKTEST & RISK
# # # #                 # ==========================================
# # # #                 with tab3:
# # # #                     st.header("🛡️ Risk-First Strategy Performance")
                    
# # # #                     # Risk Inputs
# # # #                     with st.container():
# # # #                         st.markdown("#### ⚙️ Backtest Settings")
# # # #                         c_r1, c_r2, c_r3 = st.columns(3)
# # # #                         with c_r1:
# # # #                             sl_input = st.number_input("Stop Loss (Z-Score)", 2.5, 5.0, 3.5, 0.1, key="sl")
# # # #                         with c_r2:
# # # #                             tp_input = st.number_input("Take Profit (Z-Score)", 0.0, 1.5, 0.0, 0.1, help="0.0 = Mean Reversion", key="tp")
# # # #                         with c_r3:
# # # #                             time_stop_input = st.number_input("Max Holding Days", 5, 60, 30, key="ts")

# # # #                     # Calculation
# # # #                     df_risk_managed = calculations.backtest_with_risk_management(
# # # #                         df_signals, 
# # # #                         stop_loss_z=sl_input, 
# # # #                         take_profit_z=tp_input, 
# # # #                         max_days=time_stop_input
# # # #                     )
# # # #                     metrics = calculations.calculate_metrics(df_risk_managed)

# # # #                     # Metrics Row
# # # #                     st.divider()
# # # #                     m1, m2, m3 = st.columns(3)
# # # #                     m1.metric("Total Return", metrics["Total Return"], delta="Hypothetical P&L")
# # # #                     m2.metric("Win Rate", metrics["Win Rate"])
# # # #                     m3.metric("Trades Executed", metrics["Days in Market"])

# # # #                     # Charts
# # # #                     st.subheader("Trade Execution & Exits")
                    
# # # #                     # 5. BACKTEST/RISK CHART
# # # #                     fig_adv, data_adv = plotting.plot_advanced_signals(df_risk_managed, z_threshold=2.0, stop_loss_z=sl_input)
# # # #                     render_chart_with_csv(fig_adv, data_adv, filename_prefix="backtest_results")

# # # #             else:
# # # #                 st.error("Could not load data. Please check CSV files.")
# # # # else:
# # # #     st.info("👈 Please select a sector from the sidebar to begin.")





# # # # import streamlit as st
# # # # import pandas as pd

# # # # # Import custom modules
# # # # from modules.calculation import calculations
# # # # from modules.plotting import plotting
# # # # from modules import data_loader

# # # # # ==========================================
# # # # # CONFIGURATION (TASK 1: CENTRALIZED PATH)
# # # # # ==========================================
# # # # # Yahan apna path update karein
# # # # BASE_DIR = r"C:\Users\91702\Documents\programming\app\data\sec_wise_futures_data"

# # # # st.set_page_config(layout="wide", page_title="Pro Quant Pair Studio")

# # # # # ==========================================
# # # # # HELPER: DOWNLOAD BUTTON
# # # # # ==========================================
# # # # def render_chart_with_csv(fig, df_to_download, filename_prefix="data"):
# # # #     """
# # # #     Displays Chart + Download Button
# # # #     """
# # # #     st.plotly_chart(fig, use_container_width=True)
    
# # # #     csv_data = df_to_download.to_csv().encode('utf-8')
# # # #     st.download_button(
# # # #         label=f"📥 Download {filename_prefix} CSV",
# # # #         data=csv_data,
# # # #         file_name=f"{filename_prefix}.csv",
# # # #         mime="text/csv",
# # # #         key=f"btn_{filename_prefix}"
# # # #     )

# # # # # ==========================================
# # # # # MAIN UI
# # # # # ==========================================

# # # # st.title("⚡ Pro Quant Pairs Studio")

# # # # # --- SIDEBAR ---
# # # # st.sidebar.header("1. Select Pair")

# # # # # Pass BASE_DIR to data_loader functions
# # # # sectors = data_loader.get_sectors(BASE_DIR)
# # # # selected_sector = st.sidebar.selectbox("Select Sector", sectors)

# # # # if selected_sector:
# # # #     stocks = data_loader.get_stocks(BASE_DIR, selected_sector)
    
# # # #     col1, col2 = st.sidebar.columns(2)
# # # #     with col1:
# # # #         stock_a = st.selectbox("Stock A (Long)", stocks, index=0 if len(stocks) > 0 else None)
# # # #     with col2:
# # # #         default_idx = 1 if len(stocks) > 1 else 0
# # # #         stock_b = st.selectbox("Stock B (Short)", stocks, index=default_idx)

# # # #     st.sidebar.divider()
# # # #     st.sidebar.header("2. Parameters")
# # # #     lookback = st.sidebar.number_input("Lookback (SMA)", min_value=5, max_value=200, value=20)
# # # #     std_dev_mult = st.sidebar.slider("Std Dev Multiplier", 0.5, 4.0, 2.0, 0.1)
    
# # # #     default_start = pd.to_datetime("2023-01-01")
# # # #     norm_start_date = st.sidebar.date_input("Performance Start Date", value=default_start)

# # # #     # --- EXECUTION ---
# # # #     if stock_a and stock_b and stock_a != stock_b:
# # # #         with st.spinner("Crunching Data..."):
# # # #             # Load Data (Passing BASE_DIR)
# # # #             raw_df = data_loader.load_pair_data(BASE_DIR, selected_sector, stock_a, stock_b)

# # # #         if raw_df is not None and not raw_df.empty:
# # # #             # Calculations
# # # #             processed_df = calculations.calculate_pair_metrics(raw_df, window=lookback, std_dev_multiplier=std_dev_mult)
            
# # # #             # --- CHART 1: BOLLINGER BAND (PRICE RATIO) (TASK 2) ---
# # # #             st.subheader(f"1. Price Ratio & Bollinger Bands ({lookback} SMA)")
# # # #             fig_ratio, data_ratio = plotting.plot_pair_ratio(processed_df, stock_a, stock_b, std_dev_mult)
# # # #             render_chart_with_csv(fig_ratio, data_ratio, filename_prefix="bollinger_ratio_data")
            
# # # #             st.divider()

# # # #             # --- CHART 2: NORMALIZED PERFORMANCE (TASK 3) ---
# # # #             st.subheader("2. Normalized Performance Comparison (Base 100)")
# # # #             norm_df = calculations.calculate_normalized_performance(raw_df, norm_start_date)
            
# # # #             if not norm_df.empty:
# # # #                 fig_norm, data_norm = plotting.plot_normalized_comparison(norm_df, stock_a, stock_b, str(norm_start_date))
# # # #                 render_chart_with_csv(fig_norm, data_norm, filename_prefix="normalized_performance_data")
# # # #             else:
# # # #                 st.warning("No data available for selected start date.")

# # # #             st.divider()

# # # #             # --- CHART 3: RSI MOMENTUM (TASK 3) ---
# # # #             st.subheader("3. RSI Momentum Indicator")
# # # #             fig_rsi, data_rsi = plotting.plot_secondary_indicators(processed_df, std_dev_mult)
# # # #             render_chart_with_csv(fig_rsi, data_rsi, filename_prefix="rsi_data")

# # # #             # ... (After RSI Chart code) ...

# # # #             st.divider()

# # # #             # --- CHART 4: BELL CURVE ANALYSIS ---
# # # #             st.subheader("4. Statistical Distribution (The Bell Curve)")
            
# # # #             # Create two columns: Chart on Left, Stats on Right
# # # #             col_bell, col_stats = st.columns([3, 1])
            
# # # #             with col_bell:
# # # #                 fig_dist = plotting.plot_zscore_distribution(processed_df)
# # # #                 st.plotly_chart(fig_dist, use_container_width=True)

# # # #             with col_stats:
# # # #                 st.markdown("### 📊 Stats")
# # # #                 cur_z = processed_df['Z_Score'].iloc[-1]
# # # #                 mean_z = processed_df['Z_Score'].mean()
# # # #                 skew = processed_df['Z_Score'].skew()
                
# # # #                 st.metric("Current Z-Score", f"{cur_z:.2f}")
# # # #                 st.metric("Mean Z-Score", f"{mean_z:.2f}")
                
# # # #                 # Interpret Skewness (Is the relationship broken?)
# # # #                 skew_label = "Normal"
# # # #                 if abs(skew) > 1: skew_label = "⚠️ Skewed (Unstable)"
# # # #                 st.metric("Distribution Skew", f"{skew:.2f}", skew_label)
                
# # # #                 st.info(
# # # #                     """
# # # #                     **How to read this:**
# # # #                     - **Center Peak:** Where the ratio spends most of its time.
# # # #                     - **Green Dot:** Where we are right now.
# # # #                     - **Tails:** If the dot is far right/left, we are likely to revert to center.
# # # #                     """
# # # #                 )
# # # #         else:
# # # #             st.error("Not enough overlapping data for this pair.")
# # # #     else:
# # # #         if stock_a == stock_b:
# # # #             st.warning("⚠️ Select two different stocks.")
# # # # else:
# # # #     st.info("👈 Please select a sector to begin.")







# # import streamlit as st
# # import pandas as pd

# # # Import custom modules
# # from modules.calculation import calculations
# # from modules.plotting import plotting
# # from modules import data_loader

# # # ==========================================
# # # CONFIGURATION
# # # ==========================================
# # BASE_DIR = r"C:\Users\91702\Documents\programming\app\data\sec_wise_futures_data"

# # st.set_page_config(layout="wide", page_title="Pro Quant Pair Studio")

# # # ==========================================
# # # HELPER: DOWNLOAD BUTTON
# # # ==========================================
# # def render_chart_with_csv(fig, df_to_download, filename_prefix="data"):
# #     """
# #     Displays Chart + Download Button
# #     """
# #     st.plotly_chart(fig, use_container_width=True)
    
# #     csv_data = df_to_download.to_csv().encode('utf-8')
# #     st.download_button(
# #         label=f"📥 Download {filename_prefix} CSV",
# #         data=csv_data,
# #         file_name=f"{filename_prefix}.csv",
# #         mime="text/csv",
# #         key=f"btn_{filename_prefix}"
# #     )

# # # ==========================================
# # # MAIN UI
# # # ==========================================

# # st.title("⚡ Pro Quant Pairs Studio")

# # # --- SIDEBAR ---
# # st.sidebar.header("1. Select Pair")

# # # Pass BASE_DIR to data_loader functions
# # sectors = data_loader.get_sectors(BASE_DIR)
# # selected_sector = st.sidebar.selectbox("Select Sector", sectors)

# # if selected_sector:
# #     stocks = data_loader.get_stocks(BASE_DIR, selected_sector)
    
# #     col1, col2 = st.sidebar.columns(2)
# #     with col1:
# #         stock_a = st.selectbox("Stock A (Long)", stocks, index=0 if len(stocks) > 0 else None)
# #     with col2:
# #         default_idx = 1 if len(stocks) > 1 else 0
# #         stock_b = st.selectbox("Stock B (Short)", stocks, index=default_idx)

# #     st.sidebar.divider()
# #     st.sidebar.header("2. Parameters")
# #     lookback = st.sidebar.number_input("Lookback (SMA)", min_value=5, max_value=200, value=20)
# #     std_dev_mult = st.sidebar.slider("Std Dev Multiplier", 0.5, 4.0, 2.0, 0.1)
    
# #     default_start = pd.to_datetime("2023-01-01")
# #     norm_start_date = st.sidebar.date_input("Performance Start Date", value=default_start)

# #     # --- EXECUTION ---
# #     if stock_a and stock_b and stock_a != stock_b:
# #         with st.spinner("Crunching Data..."):
# #             # Load Data (Passing BASE_DIR)
# #             raw_df = data_loader.load_pair_data(BASE_DIR, selected_sector, stock_a, stock_b)

# #         if raw_df is not None and not raw_df.empty:
# #             # Calculations
# #             processed_df = calculations.calculate_pair_metrics(raw_df, window=lookback, std_dev_multiplier=std_dev_mult)
            
# #             # --- CHART 1: BOLLINGER BAND (PRICE RATIO) ---
# #             st.subheader(f"1. Price Ratio & Bollinger Bands ({lookback} SMA)")
# #             fig_ratio, data_ratio = plotting.plot_pair_ratio(processed_df, stock_a, stock_b, std_dev_mult)
# #             render_chart_with_csv(fig_ratio, data_ratio, filename_prefix="bollinger_ratio_data")
            
# #             st.divider()

# #             # --- CHART 2: NORMALIZED PERFORMANCE ---
# #             st.subheader("2. Normalized Performance Comparison (Base 100)")
# #             norm_df = calculations.calculate_normalized_performance(raw_df, norm_start_date)
            
# #             if not norm_df.empty:
# #                 if not norm_df.empty:
# #                         # --- NEW: CALCULATE DOMINANCE ---
# #                         dom_stats = calculations.calculate_dominance_stats(norm_df)
                        
# #                         # Display Dominance Metrics
# #                         if dom_stats:
# #                             st.markdown("##### 🏆 Performance Dominance (Days Leading)")
# #                             d1, d2, d3, d4 = st.columns(4)
                            
# #                             # Helper to format color
# #                             def get_color(val): return "normal" if val < 50 else "inverse"

# #                             with d1:
# #                                 st.metric(f"All-Time: {stock_a}", f"{dom_stats['hist_a']:.1f}%", delta="Historical Lead")
# #                             with d2:
# #                                 st.metric(f"All-Time: {stock_b}", f"{dom_stats['hist_b']:.1f}%", delta="Historical Lead")
# #                             with d3:
# #                                 st.metric(f"Last 3M: {stock_a}", f"{dom_stats['rec_a']:.1f}%", delta="Recent Trend")
# #                             with d4:
# #                                 st.metric(f"Last 3M: {stock_b}", f"{dom_stats['rec_b']:.1f}%", delta="Recent Trend")
                        
# #                         st.caption(f"Shows the % of trading days where one stock outperformed the other since {norm_start_date}.")
# #                 fig_norm, data_norm = plotting.plot_normalized_comparison(norm_df, stock_a, stock_b, str(norm_start_date))
# #                 render_chart_with_csv(fig_norm, data_norm, filename_prefix="normalized_performance_data")
# #             else:
# #                 st.warning("No data available for selected start date.")

# #             st.divider()

# #             # --- CHART 3: RSI MOMENTUM ---
# #             st.subheader("3. RSI Momentum Indicator")
# #             fig_rsi, data_rsi = plotting.plot_secondary_indicators(processed_df, std_dev_mult)
# #             render_chart_with_csv(fig_rsi, data_rsi, filename_prefix="rsi_data")

# #             st.divider()

# #             # --- CHART 4: BELL CURVE ANALYSIS ---
# #             st.subheader("4. Statistical Distribution (The Bell Curve)")
            
# #             col_bell, col_stats = st.columns([3, 1])
            
# #             with col_bell:
# #                 fig_dist = plotting.plot_zscore_distribution(processed_df)
# #                 st.plotly_chart(fig_dist, use_container_width=True)

# #             with col_stats:
# #                 st.markdown("### 📊 Stats")
# #                 cur_z = processed_df['Z_Score'].iloc[-1]
# #                 mean_z = processed_df['Z_Score'].mean()
# #                 skew = processed_df['Z_Score'].skew()
                
# #                 st.metric("Current Z-Score", f"{cur_z:.2f}")
# #                 st.metric("Mean Z-Score", f"{mean_z:.2f}")
                
# #                 skew_label = "Normal"
# #                 if abs(skew) > 1: skew_label = "⚠️ Skewed (Unstable)"
# #                 st.metric("Distribution Skew", f"{skew:.2f}", skew_label)
                
# #                 st.info(
# #                     """
# #                     **How to read this:**
# #                     - **Center Peak:** Where the ratio spends most of its time.
# #                     - **Green Dot:** Where we are right now.
# #                     """
# #                 )

# #             st.divider()

# #             # --- CHART 5: QUARTERLY STATISTICAL BREAKDOWN (NEW) ---
# #             st.subheader("5. Quarterly Statistical Breakdown (Step Chart)")
            
# #             # Prepare data for Step Chart (Needs DateTime Index)
# #             step_chart_df = processed_df.copy()
# #             if 'Date' in step_chart_df.columns:
# #                 step_chart_df['Date'] = pd.to_datetime(step_chart_df['Date'])
# #                 step_chart_df.set_index('Date', inplace=True)
            
# #             # Call the new function from plotting.py
# #             try:
# #                 fig_step = plotting.plot_quarterly_step_chart(step_chart_df)
# #                 st.plotly_chart(fig_step, use_container_width=True)
# #             except AttributeError:
# #                 st.error("Function `plot_quarterly_step_chart` not found in `plotting.py`. Please check your module.")
# #             except Exception as e:
# #                 st.error(f"Error generating Step Chart: {e}")
            
# #         else:
# #             st.error("Not enough overlapping data for this pair.")
# #     else:
# #         if stock_a == stock_b:
# #             st.warning("⚠️ Select two different stocks.")
# # else:
# #     st.info("👈 Please select a sector to begin.")






# # # import streamlit as st
# # # import pandas as pd
# # # import sys
# # # import os



# # # def build_continuous_futures(df):
# # #     """
# # #     Builds front-month continuous futures series.
# # #     - Chooses nearest expiry contract per day
# # #     - Ensures clean daily time series
# # #     """

# # #     # Parse dates
# # #     df = df.copy()
# # #     df['Date'] = pd.to_datetime(df['Date'])
# # #     df['EXP_DATE'] = pd.to_datetime(df['EXP_DATE'], dayfirst=True)

# # #     # Remove expired contracts
# # #     df = df[df['EXP_DATE'] >= df['Date']]

# # #     # Sort so nearest expiry comes first
# # #     df.sort_values(['Date', 'EXP_DATE'], inplace=True)

# # #     # Pick front-month per day
# # #     df_front = df.groupby('Date', as_index=False).first()

# # #     # Normalize price columns
# # #     df_front.rename(columns={
# # #         'OPEN_PRICE': 'Open',
# # #         'HI_PRICE': 'High',
# # #         'LO_PRICE': 'Low',
# # #         'CLOSE_PRICE': 'Close',
# # #         'OPEN_INT*': 'OpenInterest'
# # #     }, inplace=True)

# # #     return df_front.set_index('Date')













# # # # --- 1. SYSTEM PATH SETUP (Fixes 'NameError' & Import Issues) ---
# # # # This ensures app.py can find modules in 'Automation' and 'modules' folders
# # # current_dir = os.path.dirname(os.path.abspath(__file__))
# # # sys.path.append(current_dir)

# # # # Try adding the Automation folder explicitly for main.py dependencies
# # # automation_dir = os.path.join(current_dir, "Automation")
# # # if os.path.exists(automation_dir):
# # #     sys.path.append(automation_dir)

# # # # --- IMPORTS ---
# # # try:
# # #     from modules.calculation import calculations
# # #     from modules.plotting import plotting
# # #     from modules import data_loader
# # # except ImportError as e:
# # #     st.error(f"❌ CRITICAL ERROR: Could not import modules. Check your folder structure.\nDetails: {e}")
# # #     st.stop()

# # # # Import Pipeline (Handle if it's inside Automation folder or root)
# # # try:
# # #     import Automation.main as data_pipeline
# # # except ImportError:
# # #     try:
# # #         import main as data_pipeline
# # #     except ImportError:
# # #         data_pipeline = None  # Pipeline not found, we will disable auto-update features

# # # # ==========================================
# # # # CONFIGURATION
# # # # ==========================================
# # # BASE_DIR = r"C:\Users\91702\Documents\programming\all_cash_stocks\sec_wise_futures_data"

# # # st.set_page_config(layout="wide", page_title="Pro Quant Pair Studio")

# # # # ==========================================
# # # # 0. AUTO-RUN PIPELINE ON LOAD
# # # # ==========================================
# # # if "startup_check_done" not in st.session_state:
# # #     with st.spinner("Checking Data Freshness..."):
# # #         if data_pipeline:
# # #             try:
# # #                 # Run the pipeline and get status
# # #                 status_msg, updated = data_pipeline.main()
# # #                 st.session_state["startup_status"] = status_msg
# # #             except Exception as e:
# # #                 st.session_state["startup_status"] = f"⚠️ Pipeline Error: {e}"
# # #         else:
# # #             st.session_state["startup_status"] = "ℹ️ Auto-update disabled (main.py not found)."
        
# # #     st.session_state["startup_check_done"] = True

# # # # Display Status Banner
# # # if "startup_status" in st.session_state:
# # #     msg = st.session_state["startup_status"]
# # #     if "Failed" in msg or "Error" in msg:
# # #         st.warning(msg)
# # #     else:
# # #         st.success(msg)

# # # # ==========================================
# # # # HELPER: SAFE DATA LOADER (Fixes 'TIMESTAMP' Issue)
# # # # ==========================================
# # # def load_data_safe(base_dir, sector, stock_a, stock_b):
# # #     """
# # #     Robust loader that:
# # #     1. Handles 'TIMESTAMP' vs 'Date'.
# # #     2. Merges two stocks correctly.
# # #     3. Returns a clean dataframe for calculations.
# # #     """
# # #     path_a = os.path.join(base_dir, sector, f"{stock_a}.csv")
# # #     path_b = os.path.join(base_dir, sector, f"{stock_b}.csv")

# # #     if not os.path.exists(path_a) or not os.path.exists(path_b):
# # #         return None

# # #     try:
# # #         # return merged_df
# # #         # Read CSVs
# # #         df_a = pd.read_csv(path_a)
# # #         df_b = pd.read_csv(path_b)

# # #         # Rename TIMESTAMP
# # #         for df in [df_a, df_b]:
# # #             df.rename(columns={'TIMESTAMP': 'Date'}, inplace=True)

# # #         # 🚀 BUILD CONTINUOUS FUTURES
# # #         df_a = build_continuous_futures(df_a)
# # #         df_b = build_continuous_futures(df_b)

# # #         merged_df = pd.merge(
# # #         df_a[['Close']],
# # #         df_b[['Close']],
# # #         left_index=True,
# # #         right_index=True,
# # #         how='inner',
# # #         suffixes=(f'_{stock_a}', f'_{stock_b}')
# # #         )

# # #         merged_df.sort_index(inplace=True)



# # #     except Exception as e:
# # #         st.error(f"Error loading data: {e}")
# # #         return None

# # # # ==========================================
# # # # HELPER: FALLBACK CALCULATIONS (Fixes 'KeyError: Upper_Band')
# # # # ==========================================
# # # def ensure_metrics(df, stock_a, stock_b, window, std_dev):
# # #     """
# # #     Ensures 'Ratio', 'SMA', 'Upper_Band', 'Lower_Band', 'Z_Score' exist.
# # #     Calculates them if the external module missed them.
# # #     """
# # #     # 1. Calculate Ratio if missing
# # #     if 'Ratio' not in df.columns:
# # #         # Find close columns
# # #         col_a = f"Close_{stock_a}"
# # #         col_b = f"Close_{stock_b}"
        
# # #         # Fallback for column names if generic 'Close_x'/'Close_y' used
# # #         if col_a not in df.columns: col_a = [c for c in df.columns if f"_{stock_a}" in c and "Close" in c][0]
# # #         if col_b not in df.columns: col_b = [c for c in df.columns if f"_{stock_b}" in c and "Close" in c][0]
        
# # #         df['Ratio'] = df[col_a] / df[col_b]

# # #     # 2. Calculate Bollinger Bands if missing
# # #     if 'Upper_Band' not in df.columns:
# # #         df['SMA'] = df['Ratio'].rolling(window=window).mean()
# # #         std = df['Ratio'].rolling(window=window).std()
# # #         df['Upper_Band'] = df['SMA'] + (std * std_dev)
# # #         df['Lower_Band'] = df['SMA'] - (std * std_dev)
# # #         df['Z_Score'] = (df['Ratio'] - df['SMA']) / std
    
# # #     return df

# # # # ==========================================
# # # # HELPER: DOWNLOAD BUTTON
# # # # ==========================================
# # # def render_chart_with_csv(fig, df_to_download, filename_prefix="data"):
# # #     st.plotly_chart(fig, use_container_width=True)
# # #     csv_data = df_to_download.to_csv().encode('utf-8')
# # #     st.download_button(
# # #         label=f"📥 Download CSV",
# # #         data=csv_data,
# # #         file_name=f"{filename_prefix}.csv",
# # #         mime="text/csv",
# # #         key=f"btn_{filename_prefix}"
# # #     )

# # # # ==========================================
# # # # MAIN UI
# # # # ==========================================

# # # st.title("⚡ Pro Quant Pairs Studio")

# # # # --- SIDEBAR ---
# # # st.sidebar.header("1. Select Pair")

# # # sectors = data_loader.get_sectors(BASE_DIR)
# # # selected_sector = st.sidebar.selectbox("Select Sector", sectors)

# # # if selected_sector:
# # #     stocks = data_loader.get_stocks(BASE_DIR, selected_sector)
# # #     col1, col2 = st.sidebar.columns(2)
# # #     with col1:
# # #         stock_a = st.selectbox("Stock A (Long)", stocks, index=0 if len(stocks) > 0 else None)
# # #     with col2:
# # #         default_idx = 1 if len(stocks) > 1 else 0
# # #         stock_b = st.selectbox("Stock B (Short)", stocks, index=default_idx)

# # #     st.sidebar.divider()
# # #     st.sidebar.header("2. Parameters")
# # #     lookback = st.sidebar.number_input("Lookback (SMA)", min_value=5, max_value=200, value=20)
# # #     std_dev_mult = st.sidebar.slider("Std Dev Multiplier", 0.5, 4.0, 2.0, 0.1)
    
# # #     default_start = pd.to_datetime("2023-01-01")
# # #     norm_start_date = st.sidebar.date_input("Performance Start Date", value=default_start)

# # #     # Manual Update Button
# # #     st.sidebar.divider()
# # #     if st.sidebar.button("Force Update Pipeline"):
# # #         if data_pipeline:
# # #             with st.status("Running Manual Update...", expanded=True) as status:
# # #                 def streamlit_logger(message, is_success=False):
# # #                     if is_success: st.write(f"✅ {message}")
# # #                     else: st.write(f"⚙️ {message}")
                
# # #                 msg, _ = data_pipeline.main(status_callback=streamlit_logger)
# # #                 status.update(label=msg, state="complete", expanded=False)
# # #                 st.rerun()
# # #         else:
# # #             st.error("Pipeline module not loaded. Check file structure.")

# # #     # --- EXECUTION ---
# # #     if stock_a and stock_b and stock_a != stock_b:
# # #         with st.spinner("Crunching Data..."):
# # #             # 1. LOAD DATA (Using new Safe Loader)
# # #             raw_df = load_data_safe(BASE_DIR, selected_sector, stock_a, stock_b)

# # #         if raw_df is not None and not raw_df.empty:
# # #             # 2. CALCULATE (With Fallback Protection)
# # #             try:
# # #                 # Try using your existing module first
# # #                 processed_df = calculations.calculate_pair_metrics(raw_df, window=lookback, std_dev_multiplier=std_dev_mult)
# # #             except Exception:
# # #                 # If module fails, use raw_df directly and let ensure_metrics fix it
# # #                 processed_df = raw_df.copy()
            
# # #             # CRITICAL FIX: Ensure 'Upper_Band' etc. exist before plotting
# # #             processed_df = ensure_metrics(processed_df, stock_a, stock_b, lookback, std_dev_mult)

# # #             # --- CHART 1: BOLLINGER BAND (PRICE RATIO) ---
# # #             st.subheader(f"1. Price Ratio & Bollinger Bands ({lookback} SMA)")
# # #             try:
# # #                 fig_ratio, data_ratio = plotting.plot_pair_ratio(processed_df, stock_a, stock_b, std_dev_mult)
# # #                 render_chart_with_csv(fig_ratio, data_ratio, filename_prefix="bollinger_ratio_data")
# # #             except KeyError as e:
# # #                 st.error(f"Plotting Error: Missing column {e}. Columns available: {processed_df.columns.tolist()}")

# # #             st.divider()

# # #             # --- CHART 2: NORMALIZED PERFORMANCE ---
# # #             st.subheader("2. Normalized Performance Comparison (Base 100)")
# # #             norm_df = calculations.calculate_normalized_performance(raw_df, norm_start_date)
            
# # #             if not norm_df.empty:
# # #                 dom_stats = calculations.calculate_dominance_stats(norm_df)
# # #                 if dom_stats:
# # #                     st.markdown("##### 🏆 Performance Dominance")
# # #                     d1, d2, d3, d4 = st.columns(4)
# # #                     with d1: st.metric(f"{stock_a} (All-Time)", f"{dom_stats['hist_a']:.1f}%")
# # #                     with d2: st.metric(f"{stock_b} (All-Time)", f"{dom_stats['hist_b']:.1f}%")
# # #                     with d3: st.metric(f"{stock_a} (3M)", f"{dom_stats['rec_a']:.1f}%")
# # #                     with d4: st.metric(f"{stock_b} (3M)", f"{dom_stats['rec_b']:.1f}%")
                
# # #                 fig_norm, data_norm = plotting.plot_normalized_comparison(norm_df, stock_a, stock_b, str(norm_start_date))
# # #                 render_chart_with_csv(fig_norm, data_norm, filename_prefix="normalized_performance_data")
# # #             else:
# # #                 st.warning("No data for selected start date.")

# # #             st.divider()

# # #             # --- CHART 3: RSI MOMENTUM ---
# # #             st.subheader("3. RSI Momentum Indicator")
# # #             fig_rsi, data_rsi = plotting.plot_secondary_indicators(processed_df, std_dev_mult)
# # #             render_chart_with_csv(fig_rsi, data_rsi, filename_prefix="rsi_data")

# # #             st.divider()

# # #             # --- CHART 4: BELL CURVE ANALYSIS ---
# # #             st.subheader("4. Statistical Distribution")
# # #             fig_dist = plotting.plot_zscore_distribution(processed_df)
# # #             st.plotly_chart(fig_dist, use_container_width=True)

# # #         else:
# # #             # --- DEBUGGING ---
# # #             st.error("⚠️ Not enough overlapping data for this pair.")
# # #             with st.expander("🔍 Debug Info"):
# # #                 path_a = os.path.join(BASE_DIR, selected_sector, f"{stock_a}.csv")
# # #                 if os.path.exists(path_a):
# # #                      df_debug = pd.read_csv(path_a)
# # #                      st.write(f"Stock A ({stock_a}) Columns:", df_debug.columns.tolist())
# # #                      st.write("First 3 Rows:", df_debug.head(3))
# # #                 else:
# # #                      st.error(f"File for {stock_a} not found.")

# # #     else:
# # #         if stock_a == stock_b:
# # #             st.warning("⚠️ Select two different stocks.")
# # # else:
# # #     st.info("👈 Please select a sector to begin.")







# import streamlit as st
# import pandas as pd
# import numpy as np

# from modules.calculation import calculations
# from modules.plotting import plotting
# from modules import data_loader

# from openpyxl import Workbook
# from openpyxl.styles import Font, Alignment,Border, Side
# from openpyxl.utils import get_column_letter
# from io import BytesIO

# BASE_DIR = r"C:\Users\91702\Documents\programming\app\data\sec_wise_futures_data"

# st.set_page_config(layout="wide", page_title="Pro Quant Pair Studio")

# def dataframe_to_formatted_excel(df):
    
#     df_processed = df.copy() 

#     stock_a = str((df_processed['SYMBOL_A']).unique()[0])
#     stock_b = str((df_processed['SYMBOL_B']).unique()[0])

#     df_processed.drop(['INSTRUMENT_A','SYMBOL_A','OPEN_INT*_A','TRD_VAL_A','TRD_QTY_A','NO_OF_CONT_A','NO_OF_TRADE_A',
#                         'TIMESTAMP_B','INSTRUMENT_B','SYMBOL_B','OPEN_INT*_B','TRD_VAL_B','TRD_QTY_B','NO_OF_CONT_B','NO_OF_TRADE_B',
#                         'NEXT_EXP_DATE_A','NEXT_EXP_DATE_B'], axis=1, inplace=True)
    
#     df_processed.rename(columns={'TIMESTAMP_A': 'Date'}, inplace=True)

#     buffer = BytesIO()

#     with pd.ExcelWriter(buffer, engine='openpyxl') as writer:

#         df_processed.to_excel(writer, sheet_name="Pair Data", index=False, startrow=1) # Start at row 2 in Excel (row 1 for pandas)
        
#         wb = writer.book
#         ws = writer.sheets["Pair Data"]

#         ws.insert_cols(14) # Gap 3
#         ws.insert_cols(9)  # Gap 2
#         ws.insert_cols(2)  # Gap 1
        
#         ws.merge_cells("C1:H1") 
#         ws["C1"] = stock_a
#         ws["C1"].font = Font(bold=True)
#         ws["C1"].alignment = Alignment(horizontal="center")

#         ws.merge_cells("J1:O1")
#         ws["J1"] = stock_b
#         ws["J1"].font = Font(bold=True)
#         ws["J1"].alignment = Alignment(horizontal="center")

#         ws.merge_cells("Q1:W1")
#         ws["Q1"] = "INDICATORS"
#         ws["Q1"].font = Font(bold=True)
#         ws["Q1"].alignment = Alignment(horizontal="center")

#         for cell in ws[2]: 
#             if cell.value: # Only style cells that have content (ignore the new blank cells)
#                 cell.font = Font(bold=True)
#                 cell.alignment = Alignment(horizontal="center")

#         for col in ws.columns:
#             max_length = 0
#             column = col[1].column_letter # Get the column name
#             for cell in col:
#                 try: # Necessary to avoid error on empty cells
#                     if len(str(cell.value)) > max_length:
#                         max_length = len(str(cell.value))
#                 except:
#                     pass
#             adjusted_width = (max_length + 2) * 1.2
#             ws.column_dimensions[column].width = max(12, adjusted_width)

#     buffer.seek(0)
#     return buffer




# def preprocess_futures(df):

#     df = df.copy()

#     df.drop(
#         ['OPEN_INT_A', 'OPEN_INT_B'], axis=1, inplace=True, errors='ignore')

#     for leg in ['A', 'B']:

#         date_col = f'TIMESTAMP_{leg}'
#         expiry_col = f'EXP_DATE_{leg}'
#         symbol_col = f'SYMBOL_{leg}'
#         gap_col = f'expiry_gap_{leg}'

#         # ---- Convert to datetime ----
#         df[date_col] = pd.to_datetime(df[date_col])
#         df[expiry_col] = pd.to_datetime(df[expiry_col])

#         # ---- Sort correctly ----
#         df = df.sort_values([symbol_col, expiry_col, date_col])

#         # ---- Next expiry per symbol ----
#         next_exp_col = f'NEXT_EXP_DATE_{leg}'
#         df[next_exp_col] = (
#             df.groupby(symbol_col)[expiry_col]
#               .shift(-1)
#         )

#         # ---- Correct expiry gap logic ----
#         df[gap_col] = np.where(
#             df[date_col] < df[expiry_col],
#             (df[expiry_col] - df[date_col]).dt.days,
#             (df[next_exp_col] - df[date_col]).dt.days
#         )

#         # ---- Safety for last contract ----
#         df.loc[df[next_exp_col].isna(), gap_col] = np.nan

#     return df


# def render_chart_with_csv(fig, df_to_download, filename_prefix="data"):
#     st.plotly_chart(fig, use_container_width=True)

#     # ---- CSV ----
#     st.download_button(
#         "📥 Download CSV",
#         df_to_download.to_csv(index=False).encode("utf-8"),
#         file_name=f"{filename_prefix}.csv",
#         mime="text/csv"
#     )

#     # ---- EXCEL (FORMATTED) ----
#     excel_file = dataframe_to_formatted_excel(df_to_download)

#     st.download_button(
#         "📊 Download Excel (Formatted)",
#         data=excel_file,
#         file_name=f"{filename_prefix}.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )


# st.title("⚡ Pro Quant Pairs Studio")

# # --- SIDEBAR ---
# st.sidebar.header("1. Select Pair")

# sectors = data_loader.get_sectors(BASE_DIR)
# selected_sector = st.sidebar.selectbox("Select Sector", sectors)

# if selected_sector:
#     stocks = data_loader.get_stocks(BASE_DIR, selected_sector)

#     col1, col2 = st.sidebar.columns(2)
#     with col1:
#         stock_a = st.selectbox("Stock A (Long)", stocks, index=0)
#     with col2:
#         stock_b = st.selectbox(
#             "Stock B (Short)",
#             stocks,
#             index=1 if len(stocks) > 1 else 0
#         )

#     st.sidebar.divider()
#     st.sidebar.header("2. Parameters")

#     lookback = st.sidebar.number_input("Lookback (SMA)", 5, 200, 20)
#     std_dev_mult = st.sidebar.slider("Std Dev Multiplier", 0.5, 4.0, 2.0, 0.1)
#     norm_start_date = st.sidebar.date_input(
#         "Performance Start Date",
#         pd.to_datetime("2023-01-01")
#     )

#     if stock_a != stock_b:
#         with st.spinner("Crunching Data..."):
#             raw_df = data_loader.load_pair_data(
#                 BASE_DIR, selected_sector, stock_a, stock_b
#             )

#         if raw_df is not None and not raw_df.empty:

#             raw_df = preprocess_futures(raw_df)

#             processed_df = calculations.calculate_pair_metrics(
#                 raw_df,
#                 window=lookback,
#                 std_dev_multiplier=std_dev_mult
#             )

#             st.subheader("1. Price Ratio & Bollinger Bands")
#             fig_ratio, data_ratio = plotting.plot_pair_ratio(
#                 processed_df, stock_a, stock_b, std_dev_mult
#             )
#             render_chart_with_csv(fig_ratio, data_ratio, "bollinger_ratio_data")

#             st.divider()

#             st.subheader("2. Normalized Performance Comparison")
#             norm_df = calculations.calculate_normalized_performance(
#                 raw_df, norm_start_date
#             )

#             if not norm_df.empty:
#                 dom_stats = calculations.calculate_dominance_stats(norm_df)

#                 if dom_stats:
#                     st.markdown("##### 🏆 Performance Dominance")
#                     c1, c2, c3, c4 = st.columns(4)
#                     c1.metric(stock_a, f"{dom_stats['hist_a']:.1f}%")
#                     c2.metric(stock_b, f"{dom_stats['hist_b']:.1f}%")
#                     c3.metric(f"{stock_a} (3M)", f"{dom_stats['rec_a']:.1f}%")
#                     c4.metric(f"{stock_b} (3M)", f"{dom_stats['rec_b']:.1f}%")

#                 fig_norm, data_norm = plotting.plot_normalized_comparison(
#                     norm_df, stock_a, stock_b, str(norm_start_date)
#                 )
#                 render_chart_with_csv(
#                     fig_norm, data_norm, "normalized_performance_data"
#                 )
#             else:
#                 st.warning("No data available after selected date.")

#             st.divider()


#             st.subheader("3. RSI Momentum Indicator")
#             fig_rsi, data_rsi = plotting.plot_secondary_indicators(
#                 processed_df, std_dev_mult
#             )
#             render_chart_with_csv(fig_rsi, data_rsi, "rsi_data")

#             st.divider()


#             st.subheader("4. Statistical Distribution")
#             fig_dist = plotting.plot_zscore_distribution(processed_df)
#             st.plotly_chart(fig_dist, use_container_width=True)

#             st.divider()


#             st.subheader("5. Quarterly Statistical Breakdown")
#             fig_step = plotting.plot_quarterly_step_chart(processed_df)
#             st.plotly_chart(fig_step, use_container_width=True)

#         else:
#             st.error("Not enough overlapping data.")
#     else:
#         st.warning("Select two different stocks.")
# else:
#     st.info("👈 Select a sector to begin.")




import streamlit as st
import pandas as pd
import numpy as np

from modules.calculation import calculations
from modules.plotting import plotting
from modules import data_loader

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

from pathlib import Path
import os

# Define the base directory relative to the current script file
# Path(__file__).resolve().parent gets the directory containing the script being run
BASE_DIR = Path(__file__).resolve().parent / "sec_wise_futures_data"

st.set_page_config(layout="wide", page_title="Pro Quant Pair Studio")

# 1. MODIFIED: Added lookback and std_mult arguments to signature
def dataframe_to_formatted_excel(df, lookback, std_mult):
    
    df_processed = df.copy() 

    stock_a = str((df_processed['SYMBOL_A']).unique()[0])
    stock_b = str((df_processed['SYMBOL_B']).unique()[0])

    # Try/Except block added to handle dataframes that might not have all columns (like normalized data)
    try:
        df_processed.drop(['INSTRUMENT_A','SYMBOL_A','OPEN_INT*_A','TRD_VAL_A','TRD_QTY_A','NO_OF_CONT_A','NO_OF_TRADE_A',
                            'TIMESTAMP_B','INSTRUMENT_B','SYMBOL_B','OPEN_INT*_B','TRD_VAL_B','TRD_QTY_B','NO_OF_CONT_B','NO_OF_TRADE_B',
                            'NEXT_EXP_DATE_A','NEXT_EXP_DATE_B'], axis=1, inplace=True)
    except KeyError:
        pass # Ignore if columns don't exist
    
    if 'TIMESTAMP_A' in df_processed.columns:
        df_processed.rename(columns={'TIMESTAMP_A': 'Date'}, inplace=True)

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:

        df_processed.to_excel(writer, sheet_name="Pair Data", index=False, startrow=1) 
        
        wb = writer.book
        ws = writer.sheets["Pair Data"]

        ws.insert_cols(14) # Gap 3
        ws.insert_cols(9)  # Gap 2
        ws.insert_cols(2)  # Gap 1
        
        # --- Stock A Header ---
        ws.merge_cells("C1:H1") 
        ws["C1"] = stock_a
        ws["C1"].font = Font(bold=True)
        ws["C1"].alignment = Alignment(horizontal="center")

        # --- Stock B Header ---
        ws.merge_cells("J1:O1")
        ws["J1"] = stock_b
        ws["J1"].font = Font(bold=True)
        ws["J1"].alignment = Alignment(horizontal="center")

        # --- MODIFIED: Indicators Header with Parameters ---
        ws.merge_cells("Q1:W1")
        # Creating the detailed string requested
        header_text = f"INDICATORS (RSI/Z-Score: {lookback}D | Bands: ±{std_mult} SD)"
        ws["Q1"] = header_text
        ws["Q1"].font = Font(bold=True)
        ws["Q1"].alignment = Alignment(horizontal="center")

        for cell in ws[2]: 
            if cell.value: 
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")

        for col in ws.columns:
            max_length = 0
            column = col[1].column_letter 
            for cell in col:
                try: 
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length) * 1.2
            print(column + str(adjusted_width))
            ws.column_dimensions[column].width = max(12,adjusted_width)

    buffer.seek(0)
    return buffer


def preprocess_futures(df):
    df = df.copy()
    df.drop(['OPEN_INT_A', 'OPEN_INT_B'], axis=1, inplace=True, errors='ignore')

    for leg in ['A', 'B']:
        date_col = f'TIMESTAMP_{leg}'
        expiry_col = f'EXP_DATE_{leg}'
        symbol_col = f'SYMBOL_{leg}'
        gap_col = f'expiry_gap_{leg}'

        df[date_col] = pd.to_datetime(df[date_col])
        df[expiry_col] = pd.to_datetime(df[expiry_col])

        df = df.sort_values([symbol_col, expiry_col, date_col])

        next_exp_col = f'NEXT_EXP_DATE_{leg}'
        df[next_exp_col] = (df.groupby(symbol_col)[expiry_col].shift(-1))

        df[gap_col] = np.where(
            df[date_col] < df[expiry_col],
            (df[expiry_col] - df[date_col]).dt.days,
            (df[next_exp_col] - df[date_col]).dt.days
        )
        df.loc[df[next_exp_col].isna(), gap_col] = np.nan

    return df


# 2. MODIFIED: Added lookback and std_mult arguments to signature
def render_chart_with_csv(fig, df_to_download, lookback, std_mult, filename_prefix="data"):
    st.plotly_chart(fig, use_container_width=True)

    # ---- CSV ----
    # st.download_button(
    #     "📥 Download CSV",
    #     df_to_download.to_csv(index=False).encode("utf-8"),
    #     file_name=f"{filename_prefix}.csv",
    #     mime="text/csv"
    # )

    # ---- EXCEL (FORMATTED) ----
    # Passing the parameters to the excel function
    excel_file = dataframe_to_formatted_excel(df_to_download, lookback, std_mult)

    st.download_button(
        "📊 Download Excel (Formatted)",
        data=excel_file,
        file_name=f"{filename_prefix}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


st.title("⚡ Pro Quant Pairs Studio")

# --- SIDEBAR ---
st.sidebar.header("1. Select Pair")

sectors = data_loader.get_sectors(BASE_DIR)
selected_sector = st.sidebar.selectbox("Select Sector", sectors)

if selected_sector:
    stocks = data_loader.get_stocks(BASE_DIR, selected_sector)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        stock_a = st.selectbox("Stock A (Long)", stocks, index=0)
    with col2:
        stock_b = st.selectbox(
            "Stock B (Short)",
            stocks,
            index=1 if len(stocks) > 1 else 0
        )

    st.sidebar.divider()
    st.sidebar.header("2. Parameters")

    lookback = st.sidebar.number_input("Lookback (SMA)", 5, 200, 20)
    std_dev_mult = st.sidebar.slider("Std Dev Multiplier", 0.5, 4.0, 2.0, 0.1)
    norm_start_date = st.sidebar.date_input(
        "Performance Start Date",
        pd.to_datetime("2023-01-01")
    )

    if stock_a != stock_b:
        with st.spinner("Crunching Data..."):
            raw_df = data_loader.load_pair_data(
                BASE_DIR, selected_sector, stock_a, stock_b
            )

        if raw_df is not None and not raw_df.empty:

            raw_df = preprocess_futures(raw_df)

            processed_df = calculations.calculate_pair_metrics(
                raw_df,
                window=lookback,
                std_dev_multiplier=std_dev_mult
            )

            st.subheader("1. Price Ratio & Bollinger Bands")
            fig_ratio, data_ratio = plotting.plot_pair_ratio(
                processed_df, stock_a, stock_b, std_dev_mult
            )
            # 3. MODIFIED: Passing lookback and std_dev_mult
            render_chart_with_csv(fig_ratio, data_ratio, lookback, std_dev_mult, "bollinger_ratio_data")

            st.divider()

            st.subheader("2. Normalized Performance Comparison")
            norm_df = calculations.calculate_normalized_performance(
                raw_df, norm_start_date
            )

            if not norm_df.empty:
                dom_stats = calculations.calculate_dominance_stats(norm_df)

                if dom_stats:
                    st.markdown("##### 🏆 Performance Dominance")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric(stock_a, f"{dom_stats['hist_a']:.1f}%")
                    c2.metric(stock_b, f"{dom_stats['hist_b']:.1f}%")
                    c3.metric(f"{stock_a} (3M)", f"{dom_stats['rec_a']:.1f}%")
                    c4.metric(f"{stock_b} (3M)", f"{dom_stats['rec_b']:.1f}%")

                fig_norm, data_norm = plotting.plot_normalized_comparison(
                    norm_df, stock_a, stock_b, str(norm_start_date)
                )
                # 3. MODIFIED: Passing lookback and std_dev_mult
                render_chart_with_csv(
                    fig_norm, data_norm, lookback, std_dev_mult, "normalized_performance_data"
                )
            else:
                st.warning("No data available after selected date.")

            st.divider()


            st.subheader("3. RSI Momentum Indicator")
            fig_rsi, data_rsi = plotting.plot_secondary_indicators(
                processed_df, std_dev_mult
            )
            # 3. MODIFIED: Passing lookback and std_dev_mult
            render_chart_with_csv(fig_rsi, data_rsi, lookback, std_dev_mult, "rsi_data")

            st.divider()


            st.subheader("4. Statistical Distribution")
            fig_dist = plotting.plot_zscore_distribution(processed_df)
            st.plotly_chart(fig_dist, use_container_width=True)

            st.divider()


            st.subheader("5. Quarterly Statistical Breakdown")
            fig_step = plotting.plot_quarterly_step_chart(processed_df)
            st.plotly_chart(fig_step, use_container_width=True)

        else:
            st.error("Not enough overlapping data.")
    else:
        st.warning("Select two different stocks.")
else:
    st.info("👈 Select a sector to begin.")