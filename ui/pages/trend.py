import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def show_trend_page():
    """
    Displays the Physiological Analysis page (生理機能分析).
    """
    st.title("生理機能分析")
    
    all_data = st.session_state.get('all_records_dict')
    
    if not all_data:
        st.warning("No data available for analysis. Please upload your Health data on the Landing page.")
        return

    # 1. Custom Date Range Selector (Buttons)
    st.subheader("Select Date Range")
    
    # Use session state to track selected range
    if 'trend_range' not in st.session_state or st.session_state['trend_range'] not in ["Last Week", "Last Month", "Last 3 Months", "Last 6 Months", "Last 12 Months", "Last 24 Months", "All"]:
        st.session_state['trend_range'] = "Last 6 Months"
        
    range_options = {
        "Last Week": 7,
        "Last Month": 30,
        "Last 3 Months": 90,
        "Last 6 Months": 180,
        "Last 12 Months": 365,
        "Last 24 Months": 730,
        "All": None
    }
    
    col_btns = st.columns(len(range_options))
    for i, (label, days) in enumerate(range_options.items()):
        if col_btns[i].button(label, use_container_width=True, type="primary" if st.session_state['trend_range'] == label else "secondary"):
            st.session_state['trend_range'] = label
            st.rerun()

    range_opt = st.session_state['trend_range']
    days_to_subtract = range_options[range_opt]
    
    # 2. Process Metrics (VO2 Max, Resting HR, Running Speed, HRV)
    metrics_map = {
        "VO2 Max": "HKQuantityTypeIdentifierVO2Max",
        "Resting Heart Rate": "HKQuantityTypeIdentifierRestingHeartRate",
        "Running Speed": "HKQuantityTypeIdentifierRunningSpeed",
        "HRV (SDNN)": "HKQuantityTypeIdentifierHeartRateVariabilitySDNN"
    }
    
    processed_data = {}
    all_indices = []
    
    for label, identifier in metrics_map.items():
        df = all_data.get(identifier)
        if df is not None and not df.empty:
            df = df.copy()
            df['startDate'] = pd.to_datetime(df['startDate'])
            
            # Filter by date
            max_date = df['startDate'].max()
            if days_to_subtract:
                start_date = max_date - timedelta(days=days_to_subtract)
                df = df[df['startDate'] >= start_date]
            
            if not df.empty:
                # Unit conversion for Running Speed (m/s to km/h)
                if identifier == "HKQuantityTypeIdentifierRunningSpeed":
                    unit = df['unit'].iloc[0] if 'unit' in df.columns else 'm/s'
                    if unit == 'm/s':
                        df['value'] = pd.to_numeric(df['value'], errors='coerce') * 3.6
                else:
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                
                df = df.sort_values('startDate').set_index('startDate')
                # Resample daily and mean
                daily = df['value'].resample('D').mean()
                # Linear interpolation up to 14 days
                daily_filled = daily.interpolate(method='linear', limit=14)
                # 7-day and 14-day moving average
                moving_7 = daily_filled.rolling(window=7, min_periods=1).mean()
                moving_14 = daily_filled.rolling(window=14, min_periods=1).mean()
                
                processed_data[label] = pd.DataFrame({
                    'Daily': daily, 
                    'Moving_7D': moving_7,
                    'Moving_14D': moving_14
                })
                all_indices.extend(daily.index.tolist())

    if not processed_data:
        st.info(f"No trend data available for the selected range: {range_opt}")
        return

    # 3. Plot Combined Trends
    min_x = min(all_indices)
    max_x = max(all_indices)
    
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.07,
                         subplot_titles=("VO2 Max Trend", "Resting Heart Rate Trend", "Running Speed Trend", "HRV (SDNN) Trend"))
    
    colors = {
        "VO2 Max": "#E7103D", 
        "Resting Heart Rate": "#03C9D6", 
        "Running Speed": "#80EB03",
        "HRV (SDNN)": "#6A0DAD"
    }
    
    for i, label in enumerate(["VO2 Max", "Resting Heart Rate", "Running Speed", "HRV (SDNN)"], 1):
        if label in processed_data:
            d = processed_data[label]
            
            if label == "HRV (SDNN)":
                # Special layered chart for HRV:
                # 1. Daily Area Plot (light blue, 0.2 opacity)
                fig.add_trace(go.Scatter(
                    x=d.index, y=d['Daily'], 
                    mode='lines', 
                    name='Daily Average',
                    fill='tozeroy',
                    fillcolor='rgba(173, 216, 230, 0.2)', # lightblue with opacity
                    line=dict(color='rgba(173, 216, 230, 0.3)', width=1),
                    connectgaps=True
                ), row=i, col=1)
                
                # 2. 7-Day MA (Solid Purple)
                fig.add_trace(go.Scatter(
                    x=d.index, y=d['Moving_7D'], 
                    mode='lines', 
                    name='7-Day MA (Acute)', 
                    line=dict(width=3, color='#6A0DAD'), 
                    connectgaps=True
                ), row=i, col=1)
                
                # 3. 14-Day MA (Dashed Orange)
                fig.add_trace(go.Scatter(
                    x=d.index, y=d['Moving_14D'], 
                    mode='lines', 
                    name='14-Day MA (Chronic)', 
                    line=dict(width=2, color='#FFA500', dash='dash'), 
                    connectgaps=True
                ), row=i, col=1)
            else:
                # Default styling for other metrics
                fig.add_trace(go.Scatter(x=d.index, y=d['Daily'], mode='markers', name=f'{label} Daily', 
                                       marker=dict(opacity=0.3, color=colors[label])), row=i, col=1)
                fig.add_trace(go.Scatter(x=d.index, y=d['Moving_7D'], mode='lines', name=f'{label} 7D MA', 
                                       line=dict(width=3, color=colors[label]), connectgaps=True), row=i, col=1)
    
    # Update layout with clean white template and unified hover
    fig.update_layout(
        height=1100, 
        template="simple_white", 
        showlegend=False,
        hovermode="x unified"
    )
    
    # Set labels and axis ranges
    fig.update_yaxes(title_text="VO2 Max", row=1, col=1)
    fig.update_yaxes(title_text="BPM", row=2, col=1)
    fig.update_yaxes(title_text="km/h", row=3, col=1)
    
    # HRV Y-axis: Don't force 0, allow zoom (start from 20 or data min)
    hrv_min = 20
    if "HRV (SDNN)" in processed_data:
        actual_min = processed_data["HRV (SDNN)"]['Daily'].min()
        if not pd.isna(actual_min):
            hrv_min = max(0, min(20, actual_min - 10))
            
    fig.update_yaxes(title_text="SDNN (ms)", row=4, col=1, rangemode="normal")
    if "HRV (SDNN)" in processed_data:
        # We can explicitly set a range if we want to ensure it doesn't start at 0
        fig.update_yaxes(range=[hrv_min, None], row=4, col=1)

    fig.update_xaxes(title_text="Date", row=4, col=1)
    fig.update_xaxes(range=[min_x, max_x])
    
    st.plotly_chart(fig, use_container_width=True)
