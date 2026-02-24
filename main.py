import streamlit as st
import os
from ui.pages.landing import show_landing_page
from ui.pages.analysis import show_analysis_page
from ui.pages.running_style import show_running_analysis_page
from ui.pages.metric_timelines import show_metric_timelines_page
from ui.pages.trend import show_trend_page
from ui.pages.vo2max_trend import show_vo2max_trend_page
from ui.pages.raw_data import show_raw_data_page

def show_inactive_page(page_name: str):
    """Displays a message for pages only available in the local/full version."""
    st.title(page_name)
    st.warning(f"### ⚠️ Local Only / 僅限本地運行")
    st.info(f"""
    **English:** The "{page_name}" page is only available in the **Desktop Version** of this application. 
    Due to memory and data constraints, the Web Version only supports Running Style Analysis.
    To use this feature, please clone the repository from [GitHub](https://github.com/andywong/Apple-Watch-Running-Health) and run it locally.

    **繁體中文：** 「{page_name}」頁面僅在本應用程式的 **Desktop Version (完整版)** 中提供。
    由於記憶體和數據限制，網頁版僅支持「跑步風格」分析。
    若要使用此功能，請從 [GitHub](https://github.com/andywong/Apple-Watch-Running-Health) 克隆儲存庫並在本地運行。
    """)

def show_data_missing_page():
    """Displays a message when data is required but not yet loaded."""
    st.title("Data Missing / 尚未上傳數據")
    st.info("""
    **English:** Please upload your Apple Health `export.zip` on the **Landing / Upload** page to view this analysis.
    
    **繁體中文：** 請先在 **Landing / Upload** 頁面核對並上傳您的 Apple Health `export.zip` 檔案以進行分析。
    """)

def main():
    st.set_page_config(page_title="Apple Watch Running & Health Analysis", layout="wide")
    
    # Auto-detect if running in Web Version (e.g., Hugging Face Spaces) or Local Desktop
    is_web_version = (
        os.getenv('HF_WEB_VERSION', 'false').lower() == 'true' or 
        os.getenv('SPACE_ID') is not None or 
        os.getenv('RUNNING_IN_SPACE') is not None
    )
    
    # Check if data is loaded
    data_loaded = 'records_df' in st.session_state
    
    # --- Define Page Wrappers to handle Web vs Desktop and Data Loaded states ---

    # 1. Landing Page (Always functional)
    landing_page = st.Page(show_landing_page, title="Landing / Upload", icon=":material/home:", default=True)

    # 2. Running Style (Functional in both, but needs data)
    def running_style_wrapper():
        if not data_loaded:
            show_data_missing_page()
        else:
            show_running_analysis_page(
                st.session_state.get('daily_df'), 
                st.session_state.get('workouts_df'), 
                st.session_state.get('all_running')
            )
    running_analysis_page = st.Page(running_style_wrapper, title="跑步風格", icon=":material/trending_up:", url_path="running-style")

    # 3. Desktop Analysis Pages (Inactive in Web, functional in Desktop if data loaded)
    def desktop_page_wrapper(page_name, func, args_type=None):
        def wrapper():
            if is_web_version:
                show_inactive_page(page_name)
            elif not data_loaded:
                show_data_missing_page()
            else:
                if args_type == 'standard':
                    func(st.session_state.get('daily_df'), st.session_state.get('workouts_df'), st.session_state.get('all_running'))
                elif args_type == 'raw_dict':
                    func(st.session_state.get('all_records_dict'))
                else:
                    func()
        return wrapper

    analysis_page = st.Page(
        desktop_page_wrapper("Core Analysis", show_analysis_page, 'standard'), 
        title="Core Analysis" + (" (Local Only)" if is_web_version else ""), 
        icon=":material/analytics:" if not is_web_version else ":material/lock:", 
        url_path="core-analysis"
    )
    
    metric_timelines_page = st.Page(
        desktop_page_wrapper("指標分析", show_metric_timelines_page, 'standard'), 
        title="指標分析" + (" (Local Only)" if is_web_version else ""), 
        icon=":material/timeline:" if not is_web_version else ":material/lock:", 
        url_path="metric-timelines"
    )
    
    trend_page = st.Page(
        desktop_page_wrapper("生理機能分析", show_trend_page), 
        title="生理機能分析" + (" (Local Only)" if is_web_version else ""), 
        icon=":material/trending_up:" if not is_web_version else ":material/lock:", 
        url_path="physio-analysis"
    )
    
    vo2max_trend_page = st.Page(
        desktop_page_wrapper("VO2 Max Trend", show_vo2max_trend_page), 
        title="VO2 Max Trend" + (" (Local Only)" if is_web_version else ""), 
        icon=":material/show_chart:" if not is_web_version else ":material/lock:", 
        url_path="vo2max-trend"
    )
    
    raw_data_page = st.Page(
        desktop_page_wrapper("View Raw Data", show_raw_data_page, 'raw_dict'), 
        title="View Raw Data" + (" (Local Only)" if is_web_version else ""), 
        icon=":material/description:" if not is_web_version else ":material/lock:", 
        url_path="raw-data"
    )

    # Structure navigation (Always show the full structure)
    pages_dict = {
        "Main": [landing_page],
        "Web Version": [running_analysis_page],
        "Desktop Version": [analysis_page, metric_timelines_page, trend_page, vo2max_trend_page, raw_data_page]
    }

    pg = st.navigation(pages_dict)
    
    # Sidebar: Clear Data button and info
    if data_loaded:
        with st.sidebar:
            st.divider()
            if st.button("🗑️ Clear Data", use_container_width=True):
                # Clear all relevant keys from session state
                keys_to_clear = ['records_df', 'workouts_df', 'all_records_dict', 'daily_df', 'all_running', 'gpx_routes']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            if is_web_version:
                st.caption("🚀 Running in Web Version")
    else:
        status_msg = "Web Version (Running Style Only)" if is_web_version else "Desktop Version (All Analysis)"
        st.sidebar.info(f"Mode: {status_msg}. Upload your Apple Health export.zip on the Landing page.")

    # Run the navigation
    pg.run()

if __name__ == "__main__":
    main()
