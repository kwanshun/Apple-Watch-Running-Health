import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def generate_mock_parser_data():
    """
    Generates mock data for all required health and running metrics.
    """
    dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
    n = len(dates)
    
    mock_dict = {}
    
    # 1. Heart Health & Adv Analytics
    # VO2 Max: 35-45 range
    mock_dict['HKQuantityTypeIdentifierVO2Max'] = pd.DataFrame({
        'startDate': dates,
        'value': np.linspace(38, 42, n) + np.random.normal(0, 0.5, n),
        'unit': 'ml/kg/min'
    })
    
    # RHR: 50-70 range
    mock_dict['HKQuantityTypeIdentifierRestingHeartRate'] = pd.DataFrame({
        'startDate': dates,
        'value': np.linspace(62, 58, n) + np.random.normal(0, 2, n),
        'unit': 'count/min'
    })
    
    # Running Speed: 2.5 - 3.5 m/s
    mock_dict['HKQuantityTypeIdentifierRunningSpeed'] = pd.DataFrame({
        'startDate': dates,
        'value': np.linspace(2.8, 3.2, n) + np.random.normal(0, 0.2, n),
        'unit': 'm/s'
    })
    
    # HRV: 40-80 range
    mock_dict['HKQuantityTypeIdentifierHeartRateVariabilitySDNN'] = pd.DataFrame({
        'startDate': dates,
        'value': np.linspace(50, 65, n) + np.random.normal(0, 5, n),
        'unit': 'ms'
    })
    
    # Walking Heart Rate Average
    mock_dict['HKQuantityTypeIdentifierWalkingHeartRateAverage'] = pd.DataFrame({
        'startDate': dates,
        'value': np.linspace(95, 90, n) + np.random.normal(0, 3, n),
        'unit': 'count/min'
    })
    
    # Oxygen Saturation
    mock_dict['HKQuantityTypeIdentifierOxygenSaturation'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.uniform(0.96, 0.99, n),
        'unit': '%'
    })
    
    # HR Recovery (1 min)
    mock_dict['HKQuantityTypeIdentifierHeartRateRecoveryOneMinute'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.normal(30, 5, n),
        'unit': 'count/min'
    })

    # 2. Running Analysis 1
    # Distance
    mock_dict['HKQuantityTypeIdentifierDistanceWalkingRunning'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.choice([0, 5, 8, 12, 15], n, p=[0.4, 0.2, 0.2, 0.1, 0.1]),
        'unit': 'km'
    })
    
    # Heart Rate
    mock_dict['HKQuantityTypeIdentifierHeartRate'] = pd.DataFrame({
        'startDate': pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='h'),
        'value': np.random.normal(70, 10, 365*24),
        'unit': 'count/min'
    })
    
    # Power
    mock_dict['HKQuantityTypeIdentifierRunningPower'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.normal(250, 20, n),
        'unit': 'W'
    })
    
    # Stride Length
    mock_dict['HKQuantityTypeIdentifierRunningStrideLength'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.normal(1.05, 0.05, n),
        'unit': 'm'
    })
    
    # Vertical Oscillation
    mock_dict['HKQuantityTypeIdentifierRunningVerticalOscillation'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.normal(8.5, 0.5, n),
        'unit': 'cm'
    })
    
    # Ground Contact Time
    mock_dict['HKQuantityTypeIdentifierRunningGroundContactTime'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.normal(240, 10, n),
        'unit': 'ms'
    })

    # 3. Sleep Analysis
    sleep_map_inv = {
        0: 'InBed', 1: 'Asleep', 2: 'Awake', 3: 'Core', 4: 'Deep', 5: 'REM'
    }
    
    sleep_records = []
    for d in dates:
        # Generate a night of sleep
        start_night = d.replace(hour=22, minute=0) + timedelta(minutes=np.random.randint(0, 120))
        curr = start_night
        # Typical sequence: InBed -> Awake -> Core -> REM -> Core -> Deep -> ...
        stages = [0, 2, 3, 5, 3, 4, 3, 5, 2, 0]
        for stage in stages:
            duration = np.random.randint(20, 90)
            end = curr + timedelta(minutes=duration)
            sleep_records.append({
                'startDate': curr,
                'endDate': end,
                'value': stage,
                'type': 'HKCategoryTypeIdentifierSleepAnalysis'
            })
            curr = end
            
    mock_dict['HKCategoryTypeIdentifierSleepAnalysis'] = pd.DataFrame(sleep_records)
    
    # Wrist Temperature
    mock_dict['HKQuantityTypeIdentifierAppleSleepingWristTemperature'] = pd.DataFrame({
        'startDate': dates,
        'value': np.random.normal(36.5, 0.3, n),
        'unit': 'degC'
    })

    return mock_dict

def get_filtered_df(df, date_col, range_option):
    if df is None or df.empty:
        return None
    
    df = df.copy()
    
    # Ensure value is numeric for quantity types, but preserve for category types
    if 'value' in df.columns:
        is_category = False
        if 'type' in df.columns:
            is_category = df['type'].iloc[0].startswith('HKCategoryTypeIdentifier')
        
        if not is_category:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
    df[date_col] = pd.to_datetime(df[date_col])
    max_date = df[date_col].max()
    
    if range_option == "Last 7 Days":
        start_date = max_date - timedelta(days=7)
    elif range_option == "Last 14 Days":
        start_date = max_date - timedelta(days=14)
    elif range_option == "1 Month":
        start_date = max_date - timedelta(days=30)
    elif range_option == "3 Months":
        start_date = max_date - timedelta(days=90)
    elif range_option == "6 Months":
        start_date = max_date - timedelta(days=180)
    elif range_option == "1 Year":
        start_date = max_date - timedelta(days=365)
    else: # All Data
        return df
    
    return df[df[date_col] >= start_date]

def show_date_filter(key):
    return st.selectbox(
        "Select Date Range",
        ["Last 7 Days", "Last 14 Days", "1 Month", "3 Months", "6 Months", "1 Year", "All Data"],
        index=6,
        key=f"filter_{key}"
    )

def show_raw_data_viewer(all_data, range_opt, default_metrics=None, key_suffix=""):
    """
    Displays a raw data viewer with a selection of data sources.
    """
    st.markdown("---")
    st.subheader("📋 Raw Data Viewer")
    
    if not all_data:
        st.info("No raw data available for viewing.")
        return

    # Default metrics to show in the dropdown if provided
    if default_metrics is None:
        default_metrics = list(all_data.keys())
    
    # Filter out metrics that are not in all_data or are empty
    available_metrics = {m: all_data.get(m) for m in default_metrics if m in all_data and all_data.get(m) is not None and not all_data.get(m).empty}
    
    if not available_metrics:
        st.info("No raw data available for the selected metrics.")
        return
        
    selected_metric = st.selectbox(
        "Select data source to view:", 
        list(available_metrics.keys()),
        key=f"raw_viewer_select_{key_suffix}"
    )
    
    view_df = available_metrics[selected_metric]
    
    # Apply date filter if range_opt is provided
    if range_opt:
        date_col = 'startDate' if 'startDate' in view_df.columns else ('start_date' if 'start_date' in view_df.columns else None)
        if date_col:
            view_filtered = get_filtered_df(view_df, date_col, range_opt)
        else:
            view_filtered = view_df
    else:
        view_filtered = view_df
        
    if view_filtered is not None and not view_filtered.empty:
        st.write(f"Showing last 1000 rows of filtered data for **{selected_metric}**:")
        st.dataframe(view_filtered.tail(1000), width="stretch")
    else:
        st.info("No data for the selected range.")

def show_advanced_analytics(all_data):
    st.header("🧠 Advanced Physiological Analysis")
    st.info("VO2 Max, Resting Heart Rate, and Running Speed trends have been moved to the [生理機能分析](physio-analysis) page.")
    
    range_opt = show_date_filter("adv")
    
    # Raw Data Viewer
    metrics = {
        "VO2 Max": "HKQuantityTypeIdentifierVO2Max",
        "Resting Heart Rate": "HKQuantityTypeIdentifierRestingHeartRate",
        "Running Speed": "HKQuantityTypeIdentifierRunningSpeed"
    }
    show_raw_data_viewer(all_data, range_opt, list(metrics.values()), "adv")

def show_heart_health(all_data):
    st.header("❤️ Heart Health Analysis")
    range_opt = show_date_filter("heart")
    
    metrics = {
        "HKQuantityTypeIdentifierRestingHeartRate": {"name": "Resting Heart Rate", "unit": "bpm", "agg": "mean"},
        "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": {"name": "Heart Rate Variability", "unit": "ms", "agg": "mean"},
        "HKQuantityTypeIdentifierWalkingHeartRateAverage": {"name": "Walking Heart Rate Avg", "unit": "bpm", "agg": "mean"},
        "HKQuantityTypeIdentifierVO2Max": {"name": "VO2 Max", "unit": "ml/kg/min", "agg": "mean"},
        "HKQuantityTypeIdentifierOxygenSaturation": {"name": "Oxygen Saturation", "unit": "%", "agg": "mean"},
        "HKQuantityTypeIdentifierHeartRateRecoveryOneMinute": {"name": "HR Recovery (1 min)", "unit": "bpm", "agg": "mean"}
    }
    
    heart_dfs = {}
    for identifier, info in metrics.items():
        df = all_data.get(identifier)
        filtered = get_filtered_df(df, 'startDate', range_opt)
        if filtered is not None and not filtered.empty:
            filtered['date'] = filtered['startDate'].dt.date
            heart_dfs[identifier] = filtered.groupby('date')['value'].agg(info['agg']).reset_index()
            
    if not heart_dfs:
        st.warning("No heart health metrics found.")
    else:
        # Determine common X-axis range to ensure alignment
        all_dates = []
        for df in heart_dfs.values():
            all_dates.extend(df['date'].tolist())
        
        min_date = min(all_dates) if all_dates else None
        max_date = max(all_dates) if all_dates else None

        fig = make_subplots(rows=len(heart_dfs), cols=1, shared_xaxes=True,
                             vertical_spacing=0.05,
                             subplot_titles=[f"{metrics[f]['name']} ({metrics[f]['unit']})" for f in heart_dfs.keys()])
        
        for i, (identifier, df) in enumerate(heart_dfs.items(), 1):
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['value'], name=metrics[identifier]['name'], mode='lines+markers'),
                row=i, col=1
            )
        
        fig.update_layout(height=250 * len(heart_dfs), template="simple_white", showlegend=False)
        
        if min_date and max_date:
            fig.update_xaxes(range=[min_date, max_date])
            
        st.plotly_chart(fig, width="stretch")

    # Raw Data Viewer
    show_raw_data_viewer(all_data, range_opt, list(metrics.keys()), "heart")

def show_run_analysis_1(all_data):
    st.header("🏃 Consolidated Running Metrics")
    range_opt = show_date_filter("run1")
    
    metrics = {
        "HKQuantityTypeIdentifierDistanceWalkingRunning": {"name": "Distance", "unit": "km", "agg": "sum"},
        "HKQuantityTypeIdentifierRunningSpeed": {"name": "Speed", "unit": "km/hr", "agg": "mean"},
        "HKQuantityTypeIdentifierHeartRate": {"name": "Heart Rate", "unit": "bpm", "agg": "mean"},
        "HKQuantityTypeIdentifierRunningPower": {"name": "Power", "unit": "W", "agg": "mean"},
        "HKQuantityTypeIdentifierRunningStrideLength": {"name": "Stride Length", "unit": "m", "agg": "mean"},
        "HKQuantityTypeIdentifierRunningVerticalOscillation": {"name": "Vertical Oscillation", "unit": "cm", "agg": "mean"},
        "HKQuantityTypeIdentifierRunningGroundContactTime": {"name": "Ground Contact Time", "unit": "ms", "agg": "mean"}
    }
    
    running_dfs = {}
    for identifier, info in metrics.items():
        df = all_data.get(identifier)
        filtered = get_filtered_df(df, 'startDate', range_opt)
        if filtered is not None and not filtered.empty:
            # Special case for Speed if it's in m/s (Apple Health standard)
            if identifier == "HKQuantityTypeIdentifierRunningSpeed" and filtered['unit'].iloc[0] == 'm/s':
                filtered['value'] = filtered['value'] * 3.6
                
            filtered['date'] = filtered['startDate'].dt.date
            running_dfs[identifier] = filtered.groupby('date')['value'].agg(info['agg']).reset_index()
            
    if not running_dfs:
        st.warning("No running metrics found.")
    else:
        # Determine common X-axis range to ensure alignment
        all_dates = []
        for df in running_dfs.values():
            all_dates.extend(df['date'].tolist())
        
        min_date = min(all_dates) if all_dates else None
        max_date = max(all_dates) if all_dates else None

        fig = make_subplots(rows=len(running_dfs), cols=1, shared_xaxes=True,
                             vertical_spacing=0.05,
                             subplot_titles=[f"{metrics[f]['name']} ({metrics[f]['unit']})" for f in running_dfs.keys()])
        
        for i, (identifier, df) in enumerate(running_dfs.items(), 1):
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['value'], name=metrics[identifier]['name']),
                row=i, col=1
            )
        
        fig.update_layout(height=250 * len(running_dfs), template="simple_white", showlegend=False)
        
        if min_date and max_date:
            fig.update_xaxes(range=[min_date, max_date])
            
        st.plotly_chart(fig, width="stretch")

    # Raw Data Viewer
    show_raw_data_viewer(all_data, range_opt, list(metrics.keys()), "run1")

def show_run_analysis_2(all_data):
    st.header("🏃 Running Analysis 2: Efficiency & Form")
    range_opt = show_date_filter("run2")
    
    # 1. Core Metrics
    st.subheader("The Core Metrics")
    col1, col2, col3 = st.columns(3)
    
    # Weekly Volume (Using "All Data" for overall metrics)
    df_dist_overall = get_filtered_df(all_data.get("HKQuantityTypeIdentifierDistanceWalkingRunning"), 'startDate', "All Data")
    if df_dist_overall is not None and not df_dist_overall.empty:
        last_date = df_dist_overall['startDate'].max()
        week_ago = last_date - timedelta(days=7)
        two_weeks_ago = last_date - timedelta(days=14)
        
        vol_current = df_dist_overall[df_dist_overall['startDate'] > week_ago]['value'].sum()
        vol_prev = df_dist_overall[(df_dist_overall['startDate'] > two_weeks_ago) & (df_dist_overall['startDate'] <= week_ago)]['value'].sum()
        
        delta = f"{((vol_current - vol_prev) / vol_prev * 100):.1f}%" if vol_prev > 0 else None
        col1.metric("WEEKLY VOLUME", f"{vol_current:.1f} km", delta=delta)
    
    # RHR
    df_rhr_overall = get_filtered_df(all_data.get("HKQuantityTypeIdentifierRestingHeartRate"), 'startDate', "All Data")
    if df_rhr_overall is not None and not df_rhr_overall.empty:
        col2.metric("AVG RESTING HR", f"{int(df_rhr_overall['value'].mean())} bpm")
        
    # VO2 Max
    df_vo2_overall = get_filtered_df(all_data.get("HKQuantityTypeIdentifierVO2Max"), 'startDate', "All Data")
    if df_vo2_overall is not None and not df_vo2_overall.empty:
        col3.metric("EST. VO2 MAX", f"{df_vo2_overall['value'].iloc[-1]:.1f} ml/kg")

    st.markdown("---")
    
    # Prepare Speed and Stride for both sections
    df_speed_raw = all_data.get("HKQuantityTypeIdentifierRunningSpeed")
    df_stride_raw = all_data.get("HKQuantityTypeIdentifierRunningStrideLength")
    
    df_speed = get_filtered_df(df_speed_raw, 'startDate', range_opt)
    df_stride = get_filtered_df(df_stride_raw, 'startDate', range_opt)
    
    if df_speed is not None and not df_speed.empty:
        # Standardize units for pace and cadence calculation
        speed_unit = str(df_speed['unit'].iloc[0]).lower()
        if 'm/s' in speed_unit:
            # Already in m/s, convert to km/h for the efficiency trend and pace
            df_speed['speed_kmh'] = df_speed['value'] * 3.6
            df_speed['speed_ms'] = df_speed['value']
        else:
            # Assume km/h if not m/s (e.g., km/hr, km/h)
            df_speed['speed_kmh'] = df_speed['value']
            df_speed['speed_ms'] = df_speed['value'] / 3.6
            
        # Pace (min/km) = 60 / speed_kmh
        df_speed['pace'] = 60 / df_speed['speed_kmh']

    # 2. Efficiency Trend
    st.subheader("Efficiency Trend: Pace vs. Heart Rate")
    df_hr = get_filtered_df(all_data.get("HKQuantityTypeIdentifierHeartRate"), 'startDate', range_opt)
    
    if df_hr is not None and not df_hr.empty and df_speed is not None and not df_speed.empty:
        # Use a copy to avoid modifying df_speed for the next section
        df_speed_eff = df_speed.copy()
        df_hr_eff = df_hr.copy()
        
        df_hr_eff['week'] = df_hr_eff['startDate'].dt.tz_localize(None).dt.to_period('W').apply(lambda r: r.start_time)
        df_speed_eff['week'] = df_speed_eff['startDate'].dt.tz_localize(None).dt.to_period('W').apply(lambda r: r.start_time)
        
        weekly_hr = df_hr_eff.groupby('week')['value'].mean().reset_index()
        weekly_pace = df_speed_eff.groupby('week')['pace'].mean().reset_index()
        
        merged = pd.merge(weekly_hr, weekly_pace, on='week').sort_values('week')
        
        if not merged.empty:
            fig_eff = make_subplots(specs=[[{"secondary_y": True}]])
            fig_eff.add_trace(go.Scatter(x=merged['week'], y=merged['pace'], name="Pace (min/km)", line=dict(color="blue")), secondary_y=False)
            fig_eff.add_trace(go.Scatter(x=merged['week'], y=merged['value'], name="HR (bpm)", line=dict(color="orange", dash='dash')), secondary_y=True)
            
            fig_eff.update_yaxes(title_text="Pace (min/km)", secondary_y=False, autorange="reversed")
            fig_eff.update_yaxes(title_text="Heart Rate (bpm)", secondary_y=True)
            fig_eff.update_layout(title="Weekly Efficiency Trend", template="simple_white")
            st.plotly_chart(fig_eff, width="stretch")
    else:
        st.info("Insufficient data for Efficiency Trend (Heart Rate and Speed required).")

    # 3. Zones & Cadence
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Intensity Distribution")
        if df_hr is not None and not df_hr.empty:
            zones = pd.cut(df_hr['value'], bins=[0, 114, 133, 152, 171, 220], 
                          labels=['Zone 1: Recovery', 'Zone 2: Aerobic', 'Zone 3: Tempo', 'Zone 4: Threshold', 'Zone 5: VO2 Max'])
            counts = zones.value_counts().sort_index()
            fig_pie = px.pie(names=counts.index, values=counts.values, hole=0.4,
                             color_discrete_sequence=['lightgrey', 'blue', 'skyblue', 'orange', 'red'])
            fig_pie.update_layout(showlegend=True, legend=dict(orientation="v"))
            st.plotly_chart(fig_pie, width="stretch")
            
    with col_b:
        st.subheader("Cadence Analysis: Steps vs. Pace")
        if df_speed is not None and not df_speed.empty and df_stride is not None and not df_stride.empty:
            # Create working copies for merge
            df_sp_cad = df_speed.copy()
            df_st_cad = df_stride.copy()
            
            # Align by minute (strip timezones to ensure successful merge)
            df_sp_cad['t'] = df_sp_cad['startDate'].dt.tz_localize(None).dt.floor('min')
            df_st_cad['t'] = df_st_cad['startDate'].dt.tz_localize(None).dt.floor('min')
            
            # Handle stride units (ensure meters)
            stride_unit = str(df_st_cad['unit'].iloc[0]).lower()
            if stride_unit == 'km':
                df_st_cad['value'] = df_st_cad['value'] * 1000.0
            elif stride_unit == 'cm':
                df_st_cad['value'] = df_st_cad['value'] / 100.0
            
            merged_cad = pd.merge(df_sp_cad, df_st_cad, on='t', suffixes=('_sp', '_st'))
            
            if not merged_cad.empty:
                # Cadence Formula:
                # Apple Stride Length = distance for ONE step.
                # Speed (m/s) / Stride (m) = steps per second
                # steps per second * 60 = steps per minute (Cadence)
                
                sp_ms = merged_cad['speed_ms']
                st_m = merged_cad['value_st']
                
                merged_cad['cadence'] = (sp_ms / st_m) * 60
                
                # Filter for realistic running metrics to match original app visualization
                # Cadence [120-220] spm, Pace [3-10] min/km
                filtered_cad = merged_cad[
                    (merged_cad['cadence'] >= 120) & (merged_cad['cadence'] <= 220) &
                    (merged_cad['pace'] >= 3) & (merged_cad['pace'] <= 10)
                ]
                
                if not filtered_cad.empty:
                    fig_cad = px.scatter(filtered_cad, x='cadence', y='pace', opacity=0.5,
                                        title="Cadence (spm) vs. Pace (min/km)",
                                        labels={"cadence": "Cadence (spm)", "pace": "Pace (min/km)"},
                                        color_discrete_sequence=['orange'])
                    fig_cad.update_yaxes(autorange="reversed")
                    fig_cad.update_layout(template="simple_white")
                    st.plotly_chart(fig_cad, width="stretch")
                else:
                    st.info("No data points remained after filtering for realistic running metrics (Cadence 120-220, Pace 3-10).")
                    with st.expander("Debug: Data Ranges (Processed)"):
                        st.write(f"Cadence: {merged_cad['cadence'].min():.1f} - {merged_cad['cadence'].max():.1f}")
                        st.write(f"Pace: {merged_cad['pace'].min():.1f} - {merged_cad['pace'].max():.1f}")
                        st.write(f"Speed (km/h): {merged_cad['speed_kmh'].min():.1f} - {merged_cad['speed_kmh'].max():.1f}")
            else:
                st.info("Could not align speed and stride data for cadence analysis (timestamps don't match).")
        else:
            st.warning("Insufficient speed or stride data for cadence analysis.")

    # Raw Data Viewer
    show_raw_data_viewer(all_data, range_opt, [
        "HKQuantityTypeIdentifierRunningSpeed",
        "HKQuantityTypeIdentifierRunningStrideLength",
        "HKQuantityTypeIdentifierHeartRate",
        "HKQuantityTypeIdentifierDistanceWalkingRunning"
    ], "run2")

def show_sleep_analysis(all_data):
    st.header("😴 Sleep Analysis")
    range_opt = show_date_filter("sleep")
    
    # 1. Sleep Stages
    df_sleep = get_filtered_df(all_data.get("HKCategoryTypeIdentifierSleepAnalysis"), 'startDate', range_opt)
    if df_sleep is not None and not df_sleep.empty:
        st.subheader("Daily Sleep Stages")
        
        # Map integers to names if necessary
        sleep_labels = {0: 'InBed', 1: 'Asleep', 2: 'Awake', 3: 'Core', 4: 'Deep', 5: 'REM'}
        df_sleep['stage'] = df_sleep['value'].map(lambda x: sleep_labels.get(x, str(x)))
        
        # Simplify labels if they are strings
        df_sleep['stage'] = df_sleep['stage'].str.replace('HKCategoryValueSleepAnalysisAsleep', '').str.replace('HKCategoryValueSleepAnalysis', '')
        
        fig_sleep = px.timeline(df_sleep, x_start='startDate', x_end='endDate', y='stage', color='stage',
                                 category_orders={"stage": ["Awake", "InBed", "Asleep", "Core", "REM", "Deep"]},
                                 color_discrete_map={
                                     "Awake": "#FF4B4B", "InBed": "#778899", "Asleep": "#00CC96",
                                     "Core": "#636EFA", "REM": "#AB63FA", "Deep": "#19D3F3"
                                 })
        fig_sleep.update_layout(template="simple_white", showlegend=True)
        st.plotly_chart(fig_sleep, width="stretch")
        
    # 2. Wrist Temperature
    df_temp = get_filtered_df(all_data.get("HKQuantityTypeIdentifierAppleSleepingWristTemperature"), 'startDate', range_opt)
    if df_temp is not None and not df_temp.empty:
        st.subheader("Wrist Temperature Trend")
        df_temp['date'] = df_temp['startDate'].dt.date
        daily_temp = df_temp.groupby('date')['value'].mean().reset_index()
        fig_temp = px.line(daily_temp, x='date', y='value')
        fig_temp.update_layout(yaxis_title="Temp (°C)", template="simple_white")
        st.plotly_chart(fig_temp, width="stretch")

    # Raw Data Viewer
    show_raw_data_viewer(all_data, range_opt, [
        "HKCategoryTypeIdentifierSleepAnalysis",
        "HKQuantityTypeIdentifierAppleSleepingWristTemperature"
    ], "sleep")

def show_demo_parser_page():
    """
    Displays the Demo (Parser) page with 5 tabs of analytics.
    """
    st.title("📂 Demo (Parser) Analytics")
    
    # Check for session state data
    if 'all_records_dict' in st.session_state and st.session_state['all_records_dict']:
        all_data = st.session_state['all_records_dict']
        st.success("Using your uploaded health data.")
    else:
        all_data = generate_mock_parser_data()
        st.warning("⚠️ No detailed data found. Showing mock demonstration data. Please re-upload your export.zip on the Landing page to unlock full detailed analytics.")
        
    # Create Tabs
    tabs = st.tabs([
        "🧠 Advanced Analytics", 
        "❤️ Heart Health", 
        "🏃 Running Analysis 1", 
        "🏃 Running Analysis 2", 
        "😴 Sleep Analysis"
    ])
    
    with tabs[0]:
        show_advanced_analytics(all_data)
        
    with tabs[1]:
        show_heart_health(all_data)
        
    with tabs[2]:
        show_run_analysis_1(all_data)
        
    with tabs[3]:
        show_run_analysis_2(all_data)
        
    with tabs[4]:
        show_sleep_analysis(all_data)

if __name__ == "__main__":
    show_demo_parser_page()
