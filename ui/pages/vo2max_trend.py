import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def show_vo2max_trend_page():
    """
    Displays the VO2 Max Trend vs Workout Volume page.
    """
    st.title("VO2 Max Trend vs Workout Volume")
    
    all_data = st.session_state.get('all_records_dict')
    all_running = st.session_state.get('all_running')
    
    if not all_data or all_running is None:
        st.warning("No data available for analysis. Please upload your Health data on the Landing page.")
        return

    # 1. Date Range Selector
    st.subheader("Select Date Range")
    
    if 'vo2_trend_range' not in st.session_state or st.session_state['vo2_trend_range'] not in ["Last Month", "Last 3 Months", "Last 6 Months", "Last 12 Months", "All"]:
        st.session_state['vo2_trend_range'] = "Last 6 Months"
        
    range_options = {
        "Last Month": 30,
        "Last 3 Months": 90,
        "Last 6 Months": 180,
        "Last 12 Months": 365,
        "All": None
    }
    
    col_btns = st.columns(len(range_options))
    for i, (label, days) in enumerate(range_options.items()):
        if col_btns[i].button(label, key=f"btn_{label}", use_container_width=True, 
                             type="primary" if st.session_state['vo2_trend_range'] == label else "secondary"):
            st.session_state['vo2_trend_range'] = label
            st.rerun()

    range_opt = st.session_state['vo2_trend_range']
    days_to_subtract = range_options[range_opt]
    
    # 2. Aggregation & Metric Selectors
    col_freq, col_metric = st.columns(2)
    with col_freq:
        freq_opt = st.selectbox("Aggregation Frequency", ["Weekly", "Monthly"], index=0)
    with col_metric:
        workout_metric = st.selectbox("Workout Metric", ["Count", "Distance (km)", "Duration (min)"], index=1)
    
    freq_map = {"Weekly": "W", "Monthly": "MS"} # Use MS (Month Start) for cleaner labeling
    freq = freq_map[freq_opt]

    # 3. Process VO2 Max Data
    vo2_id = "HKQuantityTypeIdentifierVO2Max"
    vo2_raw = all_data.get(vo2_id)
    
    if vo2_raw is None or vo2_raw.empty:
        st.info("No VO2 Max data found in your records.")
        return

    vo2_raw = vo2_raw.copy()
    vo2_raw['startDate'] = pd.to_datetime(vo2_raw['startDate'], utc=True)
    vo2_raw['value'] = pd.to_numeric(vo2_raw['value'], errors='coerce')
    
    # Filter by date and exclude future dates
    max_date = vo2_raw['startDate'].max()
    now = pd.Timestamp.now(tz='UTC')
    effective_max = min(max_date, now)
    
    if days_to_subtract:
        # Calculate raw start date
        start_date = effective_max - timedelta(days=days_to_subtract)
        
        # Snap to the start of the period (Month or Week) to ensure the first bin isn't cut off
        if freq_opt == "Monthly":
            start_date = pd.Timestamp(start_date).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else: # Weekly
            # Snap to Monday of that week
            start_date = (pd.Timestamp(start_date) - pd.Timedelta(days=start_date.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            
        vo2_df = vo2_raw[(vo2_raw['startDate'] >= start_date) & (vo2_raw['startDate'] <= now)].copy()
        running_df = all_running[(all_running['startDate'] >= start_date) & (all_running['startDate'] <= now)].copy()
    else:
        vo2_df = vo2_raw[vo2_raw['startDate'] <= now].copy()
        running_df = all_running[all_running['startDate'] <= now].copy()

    if vo2_df.empty:
        st.info(f"No VO2 Max data available for the selected range: {range_opt}")
        return

    # Aggregate VO2 Max
    vo2_resampled = vo2_df.set_index('startDate')['value'].resample('D').mean()
    vo2_filled = vo2_resampled.interpolate(method='linear', limit=14)
    vo2_ma7 = vo2_filled.rolling(window=7, min_periods=1).mean()
    vo2_ma14 = vo2_filled.rolling(window=14, min_periods=1).mean()
    
    # Aggregate for the chosen frequency (Weekly/Monthly)
    vo2_periodic = vo2_filled.resample(freq).mean()
    vo2_ma7_periodic = vo2_ma7.resample(freq).mean()
    vo2_ma14_periodic = vo2_ma14.resample(freq).mean()
    
    # 4. Process Workout Data
    if running_df.empty:
        workout_periodic = pd.Series(0, index=vo2_periodic.index, name=workout_metric)
    else:
        running_df['startDate'] = pd.to_datetime(running_df['startDate'], utc=True)
        if workout_metric == "Count":
            workout_periodic = running_df.set_index('startDate').resample(freq).size()
        elif workout_metric == "Distance (km)":
            workout_periodic = running_df.set_index('startDate')['totalDistance'].resample(freq).sum()
        else: # Duration (min)
            workout_periodic = running_df.set_index('startDate')['duration'].resample(freq).sum()
            
        workout_periodic.name = workout_metric

    # Align VO2 and Workouts
    plot_df = pd.DataFrame({
        'VO2 Max': vo2_periodic,
        'VO2 Max 7d MA': vo2_ma7_periodic,
        'VO2 Max 14d MA': vo2_ma14_periodic,
        workout_metric: workout_periodic
    })
    
    # Fill workout metric with 0, but keep VO2 MAs as NaN for proper line gaps
    plot_df[workout_metric] = plot_df[workout_metric].fillna(0)
    
    # Filter out future bins (especially important for Monthly resampling)
    plot_df = plot_df[plot_df.index <= now]

    # 5. Plot Dual-Axis Chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add VO2 Max Trend (Line)
    fig.add_trace(
        go.Scatter(
            x=plot_df.index, 
            y=plot_df['VO2 Max'], 
            name="VO2 Max (Mean)",
            mode='lines+markers',
            line=dict(color='#E7103D', width=3),
            marker=dict(size=8),
            connectgaps=True
        ),
        secondary_y=False,
    )

    # Add 7d Moving Average
    fig.add_trace(
        go.Scatter(
            x=plot_df.index, 
            y=plot_df['VO2 Max 7d MA'], 
            name="VO2 Max (7d MA)",
            mode='lines',
            line=dict(color='#FFA500', width=2, dash='dash'),
            connectgaps=True
        ),
        secondary_y=False,
    )

    # Add 14d Moving Average
    fig.add_trace(
        go.Scatter(
            x=plot_df.index, 
            y=plot_df['VO2 Max 14d MA'], 
            name="VO2 Max (14d MA)",
            mode='lines',
            line=dict(color='#9467bd', width=2, dash='dot'),
            connectgaps=True
        ),
        secondary_y=False,
    )

    # Add Workout Metric (Bars)
    fig.add_trace(
        go.Bar(
            x=plot_df.index, 
            y=plot_df[workout_metric], 
            name=workout_metric,
            marker_color='rgba(3, 201, 214, 0.4)',
            offsetgroup=1
        ),
        secondary_y=True,
    )

    # Update layout
    fig.update_layout(
        title=f"VO2 Max vs Running {workout_metric} ({freq_opt})",
        template="simple_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=600,
        xaxis=dict(
            range=[plot_df.index.min() - pd.Timedelta(days=5), plot_df.index.max() + pd.Timedelta(days=5)]
        )
    )

    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="VO2 Max (ml/kg/min)", secondary_y=False, color='#E7103D')
    fig.update_yaxes(title_text=workout_metric, secondary_y=True, color='#03C9D6')

    st.plotly_chart(fig, use_container_width=True)

    # 6. Raw Data Tables
    st.divider()
    st.subheader("Data Inspection (Raw vs Processed)")
    
    tab1, tab2, tab3 = st.tabs(["VO2 Max (Raw)", "Workouts (XML Raw)", "Workouts (Processed)"])
    
    with tab1:
        st.write("**VO2 Max Records (Direct from XML)**")
        vo2_display = vo2_raw[['startDate', 'value', 'unit', 'sourceName']].sort_values('startDate', ascending=False)
        st.dataframe(vo2_display, use_container_width=True)
        
    with tab2:
        st.write("**Original Workout Records (Direct from XML)**")
        raw_workouts = st.session_state.get('workouts_df', pd.DataFrame())
        if not raw_workouts.empty:
            # Filter for running to keep it relevant
            raw_running = raw_workouts[raw_workouts['workoutActivityType'] == 'HKWorkoutActivityTypeRunning'].copy()
            cols = ['startDate', 'totalDistance', 'duration', 'sourceName']
            display_cols = [c for c in cols if c in raw_running.columns]
            st.dataframe(raw_running[display_cols].sort_values('startDate', ascending=False), use_container_width=True)
        else:
            st.info("No raw workout data found.")
            
    with tab3:
        st.write("**Processed Running Workouts (De-duplicated & Calibrated)**")
        workout_display = all_running[['startDate', 'totalDistance', 'duration', 'sourceName']].sort_values('startDate', ascending=False)
        st.dataframe(workout_display, use_container_width=True)
        st.caption("Note: Distance may be calibrated from Records or GPX if XML attribute was missing or zero. Duplicates from multiple sources (e.g. Watch + Strava) are removed.")

    st.info(f"The goal of this chart is to visualize if changes in running {workout_metric.lower()} correlate with changes in your VO2 Max over time.")
