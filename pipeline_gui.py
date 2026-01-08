import streamlit as st
import os
import sys
import importlib.util
from datetime import datetime

def run(PIPELINE_FILE_PATH):
    st.header("⚙️ Data Pipeline Center")
    st.info("Fetches Bhavcopies, Cleans Corporate Actions, Adjusts Futures, and Harmonizes Data.")

    # 1. Import Logic
    if not os.path.exists(PIPELINE_FILE_PATH):
        st.error(f"❌ CRITICAL: 'main.py' not found at: {PIPELINE_FILE_PATH}")
        return

    try:
        spec = importlib.util.spec_from_file_location("data_pipeline", PIPELINE_FILE_PATH)
        data_pipeline = importlib.util.module_from_spec(spec)
        sys.modules["data_pipeline"] = data_pipeline
        spec.loader.exec_module(data_pipeline)
    except Exception as e:
        st.error(f"⚠️ Error loading pipeline module: {e}")
        return

    # 2. UI Layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Controls")
        if st.button("🚀 Run Data Update", type="primary", use_container_width=True):
            st.session_state['run_pipeline'] = True
    
    with col2:
        st.subheader("Live Execution Logs")
        log_area = st.empty()
        
        if st.session_state.get('run_pipeline', False):
            logs = []
            
            # Callback to capture prints from main.py
            def streamlit_logger(message, is_success=False):
                ts = datetime.now().strftime("%H:%M:%S")
                icon = "✅" if is_success else "🔹"
                logs.append(f"{icon} [{ts}] {message}")
                log_area.text_area("Console Output", "\n".join(logs), height=400)
            
            with st.spinner("Pipeline is running... This may take a few minutes."):
                status_msg, success = data_pipeline.main(status_callback=streamlit_logger)
            
            if success:
                st.success(status_msg)
                st.balloons()
            else:
                if "up to date" in status_msg: st.info(status_msg)
                else: st.error(status_msg)
            
            st.session_state['run_pipeline'] = False