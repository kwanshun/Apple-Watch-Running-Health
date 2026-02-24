import streamlit as st
import pandas as pd
import datetime
from analytics.metrics import calculate_acwr, calculate_tsb
from ui.components import (
    plot_acwr_gauge, plot_tsb_chart, plot_health_trend, 
    plot_sleep_composition, plot_decoupling_chart,
    plot_activity_overview, plot_heatmap, plot_sleep_timeline,
    plot_dual_axis_decoupling, plot_readiness_heatmap, plot_long_term_progress
)

def show_analysis_page(daily_df, workouts_df, all_running):
    st.title("🏃‍♂️ Apple Watch Running & Health Analysis")
    st.header("Core App Analysis")
    
    if daily_df.empty:
        st.warning("No daily data available for analysis.")
        return

    # Date Filters
    min_date = daily_df.index.min()
    max_data_date = daily_df.index.max()
    today = datetime.date.today()
    max_picker_date = max(max_data_date, today)
    
    st.subheader("Analysis Filters")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        date_range = st.date_input(
            "Select Date Range",
            value=(max_data_date - datetime.timedelta(days=180), max_data_date),
            min_value=min_date,
            max_value=max_picker_date,
            key="analysis_date_range"
        )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (daily_df.index >= start_date) & (daily_df.index <= end_date)
        filtered_daily = daily_df.loc[mask]
        
        workouts_df['date'] = workouts_df['startDate'].dt.date
        filtered_workouts = workouts_df[(workouts_df['date'] >= start_date) & (workouts_df['date'] <= end_date)]
    else:
        filtered_daily = daily_df
        filtered_workouts = workouts_df
        start_date, end_date = None, None

    # Sub-tabs for analysis
    subtab_perf, subtab_health, subtab_dynamics, subtab_sleep, subtab_ref = st.tabs([
        "🚀 Performance", 
        "❤️ Health & Recovery", 
        "📊 Dynamics & Health (Section 2)",
        "😴 Sleep", 
        "📈 Reference Visuals"
    ])
    
    # Reusable Raw Data Viewer logic for analysis page
    def show_analysis_raw_viewer(all_running_df, daily_df, records_df, key_suffix=""):
        st.markdown("---")
        st.subheader("📋 Raw Data Viewer")
        
        sources = {}
        if not all_running_df.empty: sources["Running Workouts"] = all_running_df
        if not daily_df.empty: sources["Daily Aggregates"] = daily_df
        if records_df is not None and not records_df.empty: sources["Raw Health Records"] = records_df
        
        if not sources:
            st.info("No raw data available for viewing.")
            return
            
        selected_source = st.selectbox(
            "Select data source to view:", 
            list(sources.keys()),
            key=f"analysis_raw_viewer_{key_suffix}"
        )
        
        view_df = sources[selected_source]
        
        # Simple date filtering based on the page's date_range
        if len(date_range) == 2:
            s_date, e_date = date_range
            date_col = 'startDate' if 'startDate' in view_df.columns else ('start_date' if 'start_date' in view_df.columns else None)
            if date_col:
                view_df = view_df.copy()
                view_df[date_col] = pd.to_datetime(view_df[date_col])
                # Filter using index for daily_df if it's the index
                if selected_source == "Daily Aggregates":
                    mask = (view_df.index.date >= s_date) & (view_df.index.date <= e_date)
                    view_df = view_df[mask]
                else:
                    mask = (view_df[date_col].dt.date >= s_date) & (view_df[date_col].dt.date <= e_date)
                    view_df = view_df[mask]
        
        st.write(f"Showing last 1000 rows of data for **{selected_source}**:")
        st.dataframe(view_df.tail(1000), use_container_width=True)

    with subtab_perf:
        st.subheader("Running Performance")
        col1, col2 = st.columns([1, 2])
        
        dist_col = 'HKQuantityTypeIdentifierDistanceWalkingRunning'
        if dist_col in daily_df.columns:
            daily_df['acwr'] = calculate_acwr(daily_df[dist_col])
            current_acwr = daily_df['acwr'].iloc[-1]
            
            with col1:
                plot_acwr_gauge(current_acwr, key="perf_acwr")
            
            with col2:
                tsb, atl, ctl = calculate_tsb(daily_df[dist_col])
                tsb_df = pd.DataFrame({'tsb': tsb, 'atl': atl, 'ctl': ctl}, index=daily_df.index)
                if len(date_range) == 2:
                    tsb_df = tsb_df.loc[mask]
                plot_tsb_chart(tsb_df, key="perf_tsb")
        
        st.subheader("Workouts")
        if not all_running.empty:
            all_running['date'] = all_running['startDate'].dt.date
            if len(date_range) == 2:
                filtered_running = all_running[(all_running['date'] >= start_date) & (all_running['date'] <= end_date)]
            else:
                filtered_running = all_running
            
            if not filtered_running.empty:
                plot_decoupling_chart(filtered_running, key="perf_ef")
                
                cols_to_show = ['startDate', 'totalDistance', 'duration', 'pace_min_km']
                if 'avg_hr' in filtered_running.columns: cols_to_show.append('avg_hr')
                if 'avg_power' in filtered_running.columns: cols_to_show.append('avg_power')
                if 'efficiency_factor' in filtered_running.columns: cols_to_show.append('efficiency_factor')
                
                st.dataframe(filtered_running[cols_to_show].sort_values('startDate', ascending=False), use_container_width=True)
            else:
                st.info("No running workouts found in the selected range.")
        else:
            st.info("No running workouts found in your health data.")

        show_analysis_raw_viewer(all_running, daily_df, st.session_state.get('records_df'), "perf")

    with subtab_health:
        st.subheader("Health Markers")
        if filtered_daily.empty:
            st.info("No health data found in the selected range.")
        else:
            h_col1, h_col2 = st.columns(2)
            hrv_col = 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN'
            rhr_col = 'HKQuantityTypeIdentifierRestingHeartRate'
            
            with h_col1:
                if hrv_col in filtered_daily.columns:
                    plot_health_trend(filtered_daily, hrv_col, "Heart Rate Variability (SDNN)", key="health_hrv")
                else:
                    st.info("HRV data not available.")
            
            with h_col2:
                if rhr_col in filtered_daily.columns:
                    plot_health_trend(filtered_daily, rhr_col, "Resting Heart Rate", key="health_rhr")
                else:
                    st.info("RHR data not available.")
        
        show_analysis_raw_viewer(all_running, daily_df, st.session_state.get('records_df'), "health")

    with subtab_dynamics:
        st.subheader("Section 2 Metrics: Dynamics & Health")
        if filtered_daily.empty:
            st.info("No data found in the selected range.")
        else:
            metrics_groups = {
                "2.1 Running Dynamics": {
                    'HKQuantityTypeIdentifierRunningPower': "Running Power (Watts)",
                    'HKQuantityTypeIdentifierRunningVerticalOscillation': "Vertical Oscillation (cm)",
                    'HKQuantityTypeIdentifierRunningGroundContactTime': "Ground Contact Time (ms)",
                    'HKQuantityTypeIdentifierRunningStrideLength': "Stride Length (m)"
                },
                "2.2 Health & Recovery": {
                    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': "HRV (SDNN - ms)",
                    'HKQuantityTypeIdentifierRestingHeartRate': "Resting Heart Rate (BPM)",
                    'HKQuantityTypeIdentifierVO2Max': "VO2 Max (mL/min·kg)"
                }
            }
            
            for group_idx, (group_name, metrics) in enumerate(metrics_groups.items()):
                st.write(f"### {group_name}")
                cols = st.columns(2)
                for i, (m_id, m_name) in enumerate(metrics.items()):
                    with cols[i % 2]:
                        if m_id in filtered_daily.columns:
                            plot_health_trend(filtered_daily, m_id, m_name, key=f"dynamics_{group_idx}_{i}")
                        else:
                            st.info(f"{m_name} data not available.")

        show_analysis_raw_viewer(all_running, daily_df, st.session_state.get('records_df'), "dynamics")

    with subtab_sleep:
        st.subheader("Sleep Analysis")
        if filtered_daily.empty:
            st.info("No sleep data found in the selected range.")
        elif 'total_sleep' in filtered_daily.columns:
            plot_sleep_composition(filtered_daily, key="sleep_comp")
        else:
            st.info("Sleep data not available in the selected range.")
        
        show_analysis_raw_viewer(all_running, daily_df, st.session_state.get('records_df'), "sleep")

    with subtab_ref:
        st.subheader("Reference Library Visualizations")
        if filtered_daily.empty:
            st.info("No data available for the selected range.")
        else:
            st.write("### 1. The Decoupling Chart")
            if not all_running.empty:
                all_running['date'] = all_running['startDate'].dt.date
                if len(date_range) == 2:
                    filtered_running_ref = all_running[(all_running['date'] >= start_date) & (all_running['date'] <= end_date)]
                else:
                    filtered_running_ref = all_running
                plot_dual_axis_decoupling(filtered_running_ref, key="ref_decoupling")
            else:
                st.info("No running workouts available for Decoupling Chart.")

            st.write("### 2. The Load Gauge (ACWR)")
            dist_col = 'HKQuantityTypeIdentifierDistanceWalkingRunning'
            if dist_col in daily_df.columns:
                current_acwr = daily_df['acwr'].iloc[-1]
                plot_acwr_gauge(current_acwr, key="ref_acwr")
            else:
                st.info("Distance data not available for Load Gauge.")

            st.write("### 3. The Readiness Heatmap")
            plot_readiness_heatmap(filtered_daily, key="ref_readiness")
            
            st.write("### 4. Long-term Progress (EF Trend)")
            if not all_running.empty:
                plot_long_term_progress(filtered_running_ref, key="ref_progress")
            else:
                st.info("No running workouts available for Progress chart.")

            st.divider()
            st.subheader("Additional Reference Visuals")
            plot_activity_overview(filtered_daily, key="ref_activity")
            
            st.write("### Distance Heatmap")
            plot_heatmap(filtered_daily, dist_col, "Daily Distance Heatmap (km)", colormap="YlOrRd", key="ref_dist_heatmap")
            
            st.write("### Recent Sleep Timeline")
            if 'records_df' in st.session_state and not st.session_state['records_df'].empty:
                last_date = filtered_daily.index.max()
                if last_date:
                    day_start = pd.Timestamp(last_date)
                    night_start = day_start - pd.Timedelta(hours=6)
                    night_end = day_start + pd.Timedelta(hours=18)
                    
                    records = st.session_state['records_df']
                    if records['startDate'].dt.tz is not None:
                        night_start = night_start.tz_localize(records['startDate'].dt.tz)
                        night_end = night_end.tz_localize(records['startDate'].dt.tz)
    
                    night_records = records[
                        (records['startDate'] >= night_start) & 
                        (records['startDate'] <= night_end)
                    ]
                    plot_sleep_timeline(night_records, key="ref_sleep_timeline")
                else:
                    st.info("No recent sleep data found.")
            else:
                st.info("Raw records not available for sleep timeline.")

        show_analysis_raw_viewer(all_running, daily_df, st.session_state.get('records_df'), "ref")
