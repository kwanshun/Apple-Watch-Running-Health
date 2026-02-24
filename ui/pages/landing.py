import streamlit as st
import os
from parser.xml_parser import parse_export_zip
from analytics.metrics import aggregate_daily_metrics, process_running_workouts

def show_landing_page():
    # Auto-detect if running in Web Version (e.g., Hugging Face Spaces) or Local Desktop
    is_web_version = (
        os.getenv('HF_WEB_VERSION', 'false').lower() == 'true' or 
        os.getenv('SPACE_ID') is not None or 
        os.getenv('RUNNING_IN_SPACE') is not None
    )

    st.title("🏃‍♂️ Apple Watch Running & Health Analysis")
    
    if is_web_version:
        st.info("""
        **🚀 Web Version (Limited Data)**
        This version is optimized for web hosting and only processes **Running Form Analysis** (Ground Contact Time, Vertical Oscillation, Stride Length). 
        All other analysis pages are inactive to save memory.
        
        To access the **Desktop Version** (Heart Rate, VO2 Max, Sleep, etc.), please run the application locally on your computer.
        """)
    
    st.write("Please upload your `export.zip` file from the Apple Health app to get started.")
    
    uploaded_file = st.file_uploader("Upload export.zip", type=["zip"], key="landing_uploader")
    
    if uploaded_file is not None:
        if 'records_df' not in st.session_state or 'all_records_dict' not in st.session_state:
            with st.status("Processing export.zip... this may take a moment.") as status:
                try:
                    # Pass the web_version flag to the parser
                    records_df, workouts_df, all_records_dict, gpx_routes = parse_export_zip(
                        uploaded_file, 
                        capture_all=(not is_web_version), # Don't capture all in web version to save memory
                        web_version=is_web_version
                    )
                    st.session_state['records_df'] = records_df
                    st.session_state['workouts_df'] = workouts_df
                    st.session_state['all_records_dict'] = all_records_dict
                    st.session_state['gpx_routes'] = gpx_routes
                    
                    if not is_web_version:
                        status.update(label="Aggregating daily metrics...", state="running")
                        daily_df = aggregate_daily_metrics(records_df)
                        st.session_state['daily_df'] = daily_df
                        
                        status.update(label="Processing running workouts...", state="running")
                        all_running = process_running_workouts(workouts_df, records_df, gpx_routes)
                        st.session_state['all_running'] = all_running
                    else:
                        # Placeholder for web version to avoid errors in page functions
                        st.session_state['daily_df'] = None
                        st.session_state['all_running'] = None
                        st.session_state['workouts_df'] = workouts_df # Still keep workouts for basic info

                    status.update(label="Done!", state="complete")
                    st.toast(f"Successfully parsed {len(records_df)} records!", icon="✅")
                    st.rerun()
                except Exception as e:
                    status.update(label="Error processing file", state="error")
                    st.error(f"Error processing file: {e}")
                    import traceback
                    st.error(traceback.format_exc())

    st.markdown("""
    ### How to get your data:
    1. Open the **Health** app on your iPhone.
    2. Tap your profile icon in the top right.
    3. Scroll to the bottom and tap **Export All Health Data**.
    4. Once the export is ready, share it to your computer.
    
    ---
    
    ### Analysis Overview / 分析功能概覽
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌐 Web Version / 網頁版")
        if os.path.exists("public/web_version.png"):
            st.image("public/web_version.png", use_container_width=True)
        st.markdown("""
        **English:** Optimized for cloud hosting. Focuses on **Running Form Analysis** (Vertical Oscillation, GCT, Stride Length).
        
        **繁體中文：** 針對雲端託管進行優化。專注於**跑步風格分析**（垂直振幅、觸地時間、步幅）。
        """)

    with col2:
        st.subheader("💻 Desktop Version / 本地電腦版")
        if os.path.exists("public/desktop_version.png"):
            st.image("public/desktop_version.png", use_container_width=True)
        st.markdown("""
        **English:** Full features including **Heart Rate, VO2 Max Trends, Sleep Analysis, and Training Load (TSB/ACWR)**.
        
        **繁體中文：** 完整功能，包括**心率、VO2 Max 趨勢、睡眠分析及訓練負荷 (TSB/ACWR)**。
        """)

    st.markdown("""
    ---
    
    ### ⚠️ Data Limitation Notice / 數據限制說明
    
    **English:** For older workouts (typically from earlier iOS/watchOS versions), Apple may only export a single "Workout Summary" record instead of high-frequency time-series data. In such cases, a continuous curve for metrics like Heart Rate may not be visible in the "Metric Timelines" page.
    
    **繁體中文：** 對於較舊的運動記錄（通常來自較早的 iOS/watchOS 版本），Apple 可能僅導出單條「運動摘要」記錄，而非高頻率的序列數據。在這種情況下，「指標分析」頁面中的心率等指標可能無法顯示連續曲線。
    """)
