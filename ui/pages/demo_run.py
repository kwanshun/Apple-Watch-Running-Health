import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

def generate_mock_data():
    """
    Generates mock Apple HealthKit data for demonstration purposes.
    """
    dates = pd.date_range(start=datetime.now() - timedelta(days=90), end=datetime.now(), freq='D')
    n = len(dates)
    
    # Base trends
    vo2_base = np.linspace(32, 36, n) + np.random.normal(0, 0.5, n)
    rhr_base = np.linspace(65, 58, n) + np.random.normal(0, 2, n)
    speed_base = np.linspace(10, 12, n) + np.random.normal(0, 0.8, n)
    
    # Dynamics
    vert_osc = np.random.normal(8.5, 0.5, n)
    gct = np.random.normal(240, 10, n)
    stride = np.random.normal(1.0, 0.1, n) + (speed_base - 10) * 0.1
    
    df = pd.DataFrame({
        'Date': dates,
        'VO2Max': vo2_base,
        'RestingHR': rhr_base,
        'RunningSpeed': speed_base,
        'VerticalOscillation': vert_osc,
        'GroundContactTime': gct,
        'StrideLength': stride
    })
    return df

def show_demo_run_page():
    """
    Displays the Demo (Run) page with visualizations for Apple HealthKit data.
    """
    st.header("🧪 Demo (Run) Dashboard")
    st.markdown("### Performance Trends & Running Efficiency")

    # 1. Data Loading & Preprocessing
    # Use real data if available, otherwise mock it
    if 'daily_df' in st.session_state and not st.session_state['daily_df'].empty:
        daily = st.session_state['daily_df']
        # Map existing columns to the required names if possible
        # HKQuantityTypeIdentifierVO2Max -> VO2Max
        # HKQuantityTypeIdentifierRestingHeartRate -> RestingHR
        # Deriving RunningSpeed from all_running if available, else mocking it for demo
        
        df = pd.DataFrame(index=daily.index)
        df['Date'] = pd.to_datetime(daily.index)
        df['VO2Max'] = daily.get('HKQuantityTypeIdentifierVO2Max', np.nan)
        df['RestingHR'] = daily.get('HKQuantityTypeIdentifierRestingHeartRate', np.nan)
        
        # Fill missing with mock for demo completeness if necessary
        if df['VO2Max'].isnull().all():
            df['VO2Max'] = np.linspace(32, 36, len(df)) + np.random.normal(0, 0.2, len(df))
        if df['RestingHR'].isnull().all():
            df['RestingHR'] = np.linspace(65, 58, len(df)) + np.random.normal(0, 1, len(df))
            
        df['RunningSpeed'] = daily.get('HKQuantityTypeIdentifierDistanceWalkingRunning', 0) / 2 # Dummy mapping
        df['VerticalOscillation'] = daily.get('HKQuantityTypeIdentifierRunningVerticalOscillation', np.random.normal(8.5, 0.5, len(df)))
        df['GroundContactTime'] = daily.get('HKQuantityTypeIdentifierRunningGroundContactTime', np.random.normal(240, 10, len(df)))
        df['StrideLength'] = daily.get('HKQuantityTypeIdentifierRunningStrideLength', np.random.normal(1.1, 0.1, len(df)))
        
        st.info("Using your uploaded health data (with some derived metrics for demo).")
    else:
        df = generate_mock_data()
        st.info("No data uploaded yet. Showing mock demonstration data.")

    # Convert Date column to datetime objects (already done if generated or mapped, but to be sure)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate 7-day Moving Average for VO2Max and RestingHR
    df['VO2Max_7d'] = df['VO2Max'].rolling(window=7).mean()
    df['RestingHR_7d'] = df['RestingHR'].rolling(window=7).mean()

    # 2. Sidebar Controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("Demo Controls")
    min_date = df['Date'].min().to_pydatetime()
    max_date = df['Date'].max().to_pydatetime()
    
    date_range = st.sidebar.slider(
        "Select Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="MMM DD, YYYY"
    )
    
    # Filter data based on selection
    mask = (df['Date'] >= pd.Timestamp(date_range[0])) & (df['Date'] <= pd.Timestamp(date_range[1]))
    filtered_df = df.loc[mask].copy()

    if filtered_df.empty:
        st.warning("No data found for the selected date range.")
        return

    # 3. Row 1: Key Performance Indicators (st.metric)
    st.subheader("Key Performance Indicators")
    col1, col2, col3 = st.columns(3)
    
    # Latest available data in range
    latest = filtered_df.iloc[-1]
    first = filtered_df.iloc[0]
    
    with col1:
        vo2_delta = latest['VO2Max'] - first['VO2Max']
        st.metric("Current VO2 Max", f"{latest['VO2Max']:.1f}", delta=f"{vo2_delta:+.1f}")
        
    with col2:
        avg_speed = filtered_df['RunningSpeed'].mean()
        st.metric("Avg Running Speed", f"{avg_speed:.2f} km/h")
        
    with col3:
        rhr_delta = latest['RestingHR'] - first['RestingHR']
        st.metric("Resting Heart Rate", f"{latest['RestingHR']:.0f} BPM", delta=f"{rhr_delta:+.0f}", delta_color="inverse")

    # 4. Row 2: Efficiency Trends (Dual-Axis Plotly Chart)
    st.subheader("Efficiency Trends")
    fig2 = go.Figure()
    
    # Primary Y-axis: Running Speed
    fig2.add_trace(go.Scatter(
        x=filtered_df['Date'], y=filtered_df['RunningSpeed'],
        name="Running Speed", line=dict(color="#00CC96", width=2)
    ))
    
    # Secondary Y-axis: VO2 Max
    fig2.add_trace(go.Scatter(
        x=filtered_df['Date'], y=filtered_df['VO2Max'],
        name="VO2 Max", line=dict(color="#636EFA", width=2),
        yaxis="y2"
    ))
    
    # High Performance Benchmark
    fig2.add_hline(y=34.0, line_dash="dash", line_color="white", annotation_text="High Perf Benchmark (34.0)")

    fig2.update_layout(
        title="Running Speed vs VO2 Max Correlation",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Running Speed (km/h)", side="left"),
        yaxis2=dict(title="VO2 Max", side="right", overlaying="y", anchor="x"),
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    st.plotly_chart(fig2, width="stretch")

    # 5. Row 3: Running Dynamics (Form Analysis)
    st.subheader("Running Dynamics & Form Analysis")
    col_a, col_b = st.columns(2)
    
    with col_a:
        fig_a = go.Figure()
        fig_a.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['VerticalOscillation'], name="Vert Osc (cm)"))
        fig_a.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['GroundContactTime'], name="GCT (ms)", yaxis="y2"))
        
        fig_a.update_layout(
            title="Vertical Oscillation & GCT",
            yaxis=dict(title="Vert Osc (cm)"),
            yaxis2=dict(title="GCT (ms)", overlaying="y", side="right"),
            template="plotly_dark",
            showlegend=True
        )
        st.plotly_chart(fig_a, width="stretch")
        st.info("Note: Lower values indicate better efficiency.")
        
    with col_b:
        fig_b = px.scatter(
            filtered_df, x="RunningSpeed", y="StrideLength",
            trendline="ols", title="Speed vs Stride Length",
            template="plotly_dark"
        )
        st.plotly_chart(fig_b, width="stretch")

    # 6. Logic & Insights
    latest_rhr = latest['RestingHR']
    rhr_7d_avg = latest['RestingHR_7d']
    
    if not np.isnan(rhr_7d_avg) and latest_rhr > (rhr_7d_avg * 1.05):
        st.warning("⚠️ Recovery Alert: Your resting heart rate is slightly elevated. Consider a deload day.")
    else:
        st.success("✅ Recovery Status: Resting heart rate is within normal range.")

    # 7. Styling
    st.markdown("""
    <style>
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: black !important;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid #f0f2f6;
    }
    .stMetric label {
        color: #31333F !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: black !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    show_demo_run_page()
