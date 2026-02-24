import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Suppress Pandas downcasting warnings
pd.set_option('future.no_silent_downcasting', True)

def render_metric_card(label, value, delta=None, help=None, key=None):
    st.metric(label=label, value=value, delta=delta, help=help)

def plot_acwr_gauge(current_acwr, key=None):
    """
    Plots the ACWR gauge with a needle pointer and clear color zones.
    """
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_acwr,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "ACWR (Acute:Chronic Workload Ratio)", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 2], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "rgba(0,0,0,0.8)", 'thickness': 0.1}, # Thin needle-like bar
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps' : [
                {'range': [0, 0.8], 'color': "#E5E7E9"},      # Underload (Light Gray)
                {'range': [0.8, 1.3], 'color': "#2ECC71"},    # Sweet Spot (Vibrant Green)
                {'range': [1.3, 1.5], 'color': "#F1C40F"},    # Risk Zone (Bright Yellow)
                {'range': [1.5, 2], 'color': "#E74C3C"}       # Danger Zone (Bright Red)
            ],
            'threshold' : {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': current_acwr
            }
        }
    ))
    
    # Add annotations to label the zones directly on the chart
    fig.add_annotation(x=0.2, y=0.15, text="Underload", showarrow=False, font=dict(color="gray"))
    fig.add_annotation(x=0.5, y=0.5, text="Sweet Spot", showarrow=False, font=dict(color="green", size=14, family="Arial Black"))
    fig.add_annotation(x=0.85, y=0.15, text="Danger", showarrow=False, font=dict(color="red"))

    fig.update_layout(
        height=350,
        margin=dict(l=30, r=30, t=50, b=30),
    )
    
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_tsb_chart(df, key=None):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=df.index, y=df['ctl'], name='Fitness (CTL)', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['atl'], name='Fatigue (ATL)', line=dict(color='red')))
    fig.add_trace(go.Bar(x=df.index, y=df['tsb'], name='Form (TSB)', marker_color='orange', opacity=0.5))
    
    fig.update_layout(title="Training Stress Balance (TSB)", xaxis_title="Date", yaxis_title="Load / Form", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_health_trend(df, metric_col, title, key=None):
    fig = px.line(df, x=df.index, y=metric_col, title=title)
    # Add 7-day rolling average
    df_roll = df[metric_col].rolling(window=7).mean()
    fig.add_trace(go.Scatter(x=df.index, y=df_roll, name="7-day Trend", line=dict(color='black', width=2)))
    
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_sleep_composition(df, key=None):
    sleep_cols = ['sleep_deep', 'sleep_rem', 'sleep_core', 'sleep_awake']
    available = [c for c in sleep_cols if c in df.columns]
    
    if not available:
        st.warning("No sleep stage data available.")
        return
        
    fig = px.bar(df, x=df.index, y=available, title="Sleep Composition (Hours)")
    fig.update_layout(barmode='stack', hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_decoupling_chart(running_df, key=None):
    """
    Plots Efficiency Factor and HR vs Power/Pace trends.
    """
    if 'efficiency_factor' not in running_df.columns or running_df['efficiency_factor'].dropna().empty:
        st.info("Efficiency Factor data (Power + HR) not available for these workouts.")
        return
    
    fig = go.Figure()
    
    # EF trend
    fig.add_trace(go.Scatter(
        x=running_df['startDate'], 
        y=running_df['efficiency_factor'],
        name="Efficiency Factor (Power/HR)",
        mode='lines+markers',
        line=dict(color='green')
    ))
    
    # 7-workout rolling average
    if len(running_df) >= 3:
        ef_roll = running_df['efficiency_factor'].rolling(window=7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=running_df['startDate'], 
            y=ef_roll,
            name="EF Trend (7-workout)",
            line=dict(color='darkgreen', width=3)
        ))

    fig.update_layout(title="Efficiency Factor Trend", xaxis_title="Date", yaxis_title="EF (Watts/BPM)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_dual_axis_decoupling(running_df, key=None):
    """
    Plots a dual-axis line graph plotting Pace and Heart Rate.
    If HR rises while Pace stays constant (or slows), it indicates aerobic decoupling.
    """
    if 'pace_min_km' not in running_df.columns or 'avg_hr' not in running_df.columns:
        st.info("Pace or HR data not available for decoupling analysis.")
        return

    valid_df = running_df.dropna(subset=['pace_min_km', 'avg_hr'])
    if valid_df.empty:
        st.info("No valid workouts with both Pace and HR data found.")
        return

    from plotly.subplots import make_subplots
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Heart Rate (Primary Y)
    fig.add_trace(
        go.Scatter(x=running_df['startDate'], y=running_df['avg_hr'], name="Avg Heart Rate", line=dict(color="red")),
        secondary_y=False,
    )

    # Pace (Secondary Y - inverted because lower is faster)
    fig.add_trace(
        go.Scatter(x=running_df['startDate'], y=running_df['pace_min_km'], name="Avg Pace (min/km)", line=dict(color="blue")),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="Aerobic Decoupling: Pace vs Heart Rate",
        hovermode="x unified"
    )

    fig.update_yaxes(title_text="Heart Rate (BPM)", secondary_y=False)
    fig.update_yaxes(title_text="Pace (min/km)", secondary_y=True, autorange="reversed")

    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_readiness_heatmap(df, key=None):
    """
    A calendar view where days are colored based on the deviation of HRV/RHR 
    from their 30-day baselines.
    """
    hrv_col = 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN'
    rhr_col = 'HKQuantityTypeIdentifierRestingHeartRate'
    
    if hrv_col not in df.columns and rhr_col not in df.columns:
        st.info("HRV or RHR data not available for Readiness Heatmap.")
        return

    # Select primary metric for readiness (HRV preferred)
    metric_col = hrv_col if hrv_col in df.columns else rhr_col
    metric_name = "HRV" if metric_col == hrv_col else "RHR"
    
    # Calculate 30-day baseline deviation
    df_ready = df[[metric_col]].copy()
    df_ready['baseline'] = df_ready[metric_col].rolling(window=30, min_periods=7).mean()
    
    # Deviation % (Higher HRV is better, lower RHR is better)
    if metric_col == hrv_col:
        df_ready['deviation'] = (df_ready[metric_col] - df_ready['baseline']) / df_ready['baseline'] * 100
    else:
        # For RHR, negative deviation is "good" (ready)
        df_ready['deviation'] = (df_ready['baseline'] - df_ready[metric_col]) / df_ready['baseline'] * 100
    
    # Fill NaNs for display if any remain
    df_ready['deviation'] = df_ready['deviation'].fillna(0).infer_objects(copy=False)
    
    # Plot as heatmap
    df_ready['month'] = pd.to_datetime(df_ready.index).month
    df_ready['day'] = pd.to_datetime(df_ready.index).day
    
    pivot = df_ready.pivot_table(index='month', columns='day', values='deviation', aggfunc='mean')
    
    all_months = range(1, 13)
    all_days = range(1, 32)
    pivot = pivot.reindex(index=all_months, columns=all_days)
    
    fig = px.imshow(
        pivot,
        labels=dict(x="Day of the month", y="Month", color="Deviation (%)"),
        x=list(all_days),
        y=[['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][m-1] for m in all_months],
        color_continuous_scale="RdYlGn", # Red-Yellow-Green (Higher deviation = Green for HRV)
        title=f"Readiness Heatmap: {metric_name} Deviation from 30-day Baseline",
        template="simple_white",
        text_auto=".0f"
    )
    
    fig.update_layout(xaxis_title="Day of Month", yaxis_title="Month")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_long_term_progress(running_df, key=None):
    """
    A scatter plot of all runs, with a smoothed trend line (rolling average) 
    showing the trajectory of Efficiency Factor.
    """
    if 'efficiency_factor' not in running_df.columns:
        st.info("Efficiency Factor data not available for Progress chart.")
        return
        
    valid_df = running_df.dropna(subset=['efficiency_factor']).sort_values('startDate').copy()
    if valid_df.empty:
        st.info("No Efficiency Factor data to plot.")
        return

    # Fix: Ensure size property (totalDistance) has no NaNs to avoid Plotly ValueError
    if 'totalDistance' in valid_df.columns:
        valid_df['totalDistance_plot'] = valid_df['totalDistance'].fillna(0)
    else:
        valid_df['totalDistance_plot'] = 1 # Fallback constant size

    fig = px.scatter(
        valid_df, 
        x='startDate', 
        y='efficiency_factor',
        size='totalDistance_plot',
        color='pace_min_km' if 'pace_min_km' in valid_df.columns else None,
        title="Long-term Progress: Efficiency Factor Trend",
        labels={'efficiency_factor': 'Efficiency Factor (Watts/BPM)', 'startDate': 'Date', 'totalDistance_plot': 'Distance (km)'},
        template="simple_white",
        hover_data=['totalDistance', 'pace_min_km'] if 'totalDistance' in valid_df.columns else ['pace_min_km']
    )
    
    # Add smoothed trend line (30-day rolling if possible, or 10-workout)
    valid_df['ef_smooth'] = valid_df['efficiency_factor'].rolling(window=10, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=valid_df['startDate'], 
        y=valid_df['ef_smooth'], 
        name="Smoothed Trend (10-run)",
        line=dict(color='black', width=3)
    ))

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_activity_overview(df, key=None):
    """
    Plots the activity overview: Active Energy, Exercise Time, and Stand Time.
    Mimics apple-health-parser overview style.
    """
    from plotly.subplots import make_subplots
    
    # Check for available columns
    energy_col = 'HKQuantityTypeIdentifierActiveEnergyBurned'
    exercise_col = 'HKQuantityTypeIdentifierAppleExerciseTime'
    stand_col = 'HKQuantityTypeIdentifierAppleStandTime'
    
    available = []
    if energy_col in df.columns: available.append((energy_col, "Active Energy (kcal)", "#E7103D"))
    if exercise_col in df.columns: available.append((exercise_col, "Exercise Time (min)", "#80EB03"))
    if stand_col in df.columns: available.append((stand_col, "Stand Time (min)", "#03C9D6"))
    
    if not available:
        st.info("Activity data (Energy, Exercise, Stand) not available for overview.")
        return

    fig = make_subplots(rows=len(available), cols=1, shared_xaxes=True, vertical_spacing=0.05)
    
    for i, (col, name, color) in enumerate(available):
        fig.add_trace(
            go.Bar(x=df.index, y=df[col], name=name, marker_color=color),
            row=i+1, col=1
        )
        fig.update_yaxes(title_text=name, row=i+1, col=1)
        
    fig.update_layout(height=200*len(available), title_text="Activity Overview", showlegend=False, template="simple_white")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_heatmap(df, col, title, colormap="viridis", key=None):
    """
    Plots a heatmap for a given metric (e.g., Distance) by Month and Day.
    Mimics apple-health-parser heatmap style.
    """
    if col not in df.columns:
        st.info(f"Data for {title} not available for heatmap.")
        return
        
    # Prepare data for heatmap: Month (rows) x Day (columns)
    df_heat = df[[col]].copy()
    df_heat['month'] = pd.to_datetime(df_heat.index).month
    df_heat['day'] = pd.to_datetime(df_heat.index).day
    
    pivot = df_heat.pivot_table(index='month', columns='day', values=col, aggfunc='sum')
    
    # Ensure all months and days are present for a clean grid
    all_months = range(1, 13)
    all_days = range(1, 32)
    pivot = pivot.reindex(index=all_months, columns=all_days)
    
    fig = px.imshow(
        pivot,
        labels=dict(x="Day of the month", y="Month", color=col),
        x=list(all_days),
        y=[['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][m-1] for m in all_months],
        color_continuous_scale=colormap,
        title=title,
        template="simple_white",
        text_auto=".1f" if pivot.max().max() < 100 else False
    )
    
    fig.update_layout(xaxis_title="Day of Month", yaxis_title="Month")
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_sleep_timeline(records_df, key=None):
    """
    Plots a timeline of sleep stages for a single night/period.
    Mimics apple-health-parser sleep plot style.
    """
    sleep_df = records_df[records_df['type'] == 'HKCategoryTypeIdentifierSleepAnalysis'].copy()
    if sleep_df.empty:
        st.info("No sleep stage data available for timeline.")
        return
        
    # Map values to names
    # 0: In Bed, 1: Asleep, 2: Awake, 3: Core, 4: Deep, 5: REM
    stage_map = {
        0: 'In Bed', 1: 'Asleep', 2: 'Awake', 3: 'Core', 4: 'Deep', 5: 'REM'
    }
    colors = {
        'In Bed': "#00c7bd", 'Awake': "#ff816a", 'Core': "#32abe4", 'Deep': "#007aff", 'REM': "#3634a3", 'Asleep': "#505050"
    }
    
    sleep_df['stage'] = sleep_df['value'].map(stage_map)
    
    fig = go.Figure()
    
    # Sort by start date to make the timeline logical
    sleep_df = sleep_df.sort_values('startDate')
    
    for _, row in sleep_df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row['startDate'], row['endDate']],
                y=[row['stage'], row['stage']],
                mode='lines',
                line=dict(color=colors.get(row['stage'], "black"), width=15),
                name=row['stage'],
                showlegend=False,
                hovertext=f"{row['startDate'].strftime('%H:%M')} - {row['endDate'].strftime('%H:%M')}<br>{row['stage']}",
                hoverinfo="text"
            )
        )
        
    fig.update_layout(
        title="Sleep Stage Timeline",
        xaxis_title="Time",
        yaxis_title="Stage",
        template="simple_white",
        height=400,
        yaxis=dict(categoryorder='array', categoryarray=['In Bed', 'Awake', 'REM', 'Core', 'Deep', 'Asleep'])
    )
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_running_form_bubble(df, key=None, filter_noise=False, height=700):
    """
    Plots a Running Form Classification bubble chart.
    X: Ground Contact Time, Y: Vertical Oscillation, Size: Stride Length, Color: Vertical Ratio.

    Args:
        df: Merged DataFrame containing running dynamics metrics.
        key: Unique key for the Streamlit component.
        filter_noise: Whether to filter out the first and last 2 minutes.
        height: Height of the chart in pixels.
    """
    if df.empty:
        st.info("No data available for Running Form Classification.")
        return

    # Ensure numeric types and standard pandas format for Plotly Express
    plot_df = df.copy()
    
    # Apply noise filtering if requested
    if filter_noise:
        # Calculate relative time in minutes from the start of this specific workout segment
        plot_df['startDate'] = pd.to_datetime(plot_df['startDate'])
        w_start = plot_df['startDate'].min()
        w_end = plot_df['startDate'].max()
        
        # Filter out first/last 2 mins
        mask = (plot_df['startDate'] > (w_start + pd.Timedelta(minutes=2))) & \
               (plot_df['startDate'] < (w_end - pd.Timedelta(minutes=2)))
        plot_df = plot_df[mask]
        
    for col in ['RunningGroundContactTime', 'RunningVerticalOscillation', 'RunningStrideLength', 'VerticalRatio']:
        if col in plot_df.columns:
            plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce')
    
    plot_df = plot_df.dropna(subset=['RunningGroundContactTime', 'RunningVerticalOscillation', 'RunningStrideLength', 'VerticalRatio'])

    if plot_df.empty:
        st.info("No valid numeric data points for bubble chart.")
        return

    # Create the bubble chart with enhanced styling
    fig = px.scatter(
        plot_df,
        x='RunningGroundContactTime',
        y='RunningVerticalOscillation',
        size='RunningStrideLength',
        color='VerticalRatio',
        hover_data={
            'startDate': '| %Y-%m-%d %H:%M',
            'RunningVerticalOscillation': ':.2f',
            'RunningGroundContactTime': ':.1f',
            'RunningStrideLength': ':.2f',
            'VerticalRatio': ':.2f'
        },
        title="<b>Running Form Classification: Vertical Oscillation vs GCT</b>",
        labels={
            'RunningGroundContactTime': 'Ground Contact Time (ms)',
            'RunningVerticalOscillation': 'Vertical Oscillation (cm)',
            'RunningStrideLength': 'Stride Length (m)',
            'VerticalRatio': 'Vertical Ratio (%)',
            'startDate': 'Time'
        },
        color_continuous_scale="Plasma",
        opacity=0.7
    )

    # Add vertical and horizontal dashed lines
    line_style = dict(line_dash="dash", line_color="gray", line_width=1.5)
    fig.add_vline(x=260, **line_style, 
                 annotation_text="GCT 260ms", annotation_position="bottom right")
    fig.add_hline(y=10, **line_style, 
                 annotation_text="VO 10cm", annotation_position="top left")

    # Add Quadrant Annotations
    quadrant_style = dict(showarrow=False, font=dict(size=14, color="gray"))
    fig.add_annotation(x=200, y=11, text="<b>Power / Bouncy</b>", **quadrant_style)
    fig.add_annotation(x=320, y=11, text="<b>Heavy / Inefficient</b>", **quadrant_style)
    fig.add_annotation(x=200, y=7, text="<b>Elite / Efficient</b>", **quadrant_style)
    fig.add_annotation(x=320, y=7, text="<b>Glider / Flat</b>", **quadrant_style)

    fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    
    fig.update_layout(
        xaxis=dict(zeroline=False),
        yaxis=dict(zeroline=False),
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        coloraxis_colorbar=dict(
            title="Vertical Ratio (%)",
            thicknessmode="pixels", thickness=15,
            lenmode="fraction", len=0.7,
            yanchor="middle", y=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_workout_timeseries(dynamics_df, gpx_df=None, workout_start=None, key=None, filter_noise=False):
    """
    Plots a multi-row time-series chart for a single workout with unified hover.
    Rows: Heart Rate, Pace, VO, GCT, SL, Power, Elevation.
    """
    from analytics.metrics import align_workout_data
    import streamlit as st
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Align data onto a consistent timeline
    df = align_workout_data(dynamics_df, gpx_df)
    
    if df.empty:
        st.warning("No time-series data available for this workout.")
        return

    # Determine x-axis column and label (Prefer Distance if GPX is available)
    x_col = 'cum_dist_km' if 'cum_dist_km' in df.columns else 'rel_min'
    x_label = "Distance (km)" if x_col == 'cum_dist_km' else "Minutes from Start"
    max_x = df[x_col].max()
    max_time = df['rel_min'].max()

    # Metrics configuration: (column, display name, color, invert_y)
    metrics_config = [
        ('heart_rate', "Heart Rate", "#E74C3C", False),
        ('pace_smoothed', "Pace", "#3498DB", True),
        ('vo', "Vertical Oscillation", "#F39C12", False),
        ('gct', "Ground Contact Time", "#9B59B6", False),
        ('stride_length', "Stride Length", "#2ECC71", False),
        ('power', "Power", "#F1C40F", False),
        ('ele', "Elevation", "#8E44AD", False)
    ]

    # 2. Apply filtering logic if toggle is ON
    plot_df = df.copy()
    averages = {}
    
    for col, name, _, _ in metrics_config:
        if col in plot_df.columns:
            if filter_noise:
                mask = (plot_df['rel_min'] > 2) & (plot_df['rel_min'] < (max_time - 2))
                averages[col] = plot_df.loc[mask, col].mean()
                # Nullify data outside the mask for plotting
                plot_df.loc[~mask, col] = None
            else:
                averages[col] = plot_df[col].mean()

    fig = make_subplots(
        rows=7, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=[m[1] for m in metrics_config]
    )

    for i, (col, name, color, invert) in enumerate(metrics_config):
        if col in plot_df.columns:
            # Show filtered average in legend/title if filter is on
            display_name = f"{name} (Avg: {averages[col]:.1f})" if col in averages and not pd.isna(averages[col]) else name
            
            fig.add_trace(
                go.Scatter(
                    x=plot_df[x_col], 
                    y=plot_df[col], 
                    name=display_name, 
                    mode='lines',
                    line=dict(color=color, width=2),
                    connectgaps=True, # MANDATORY: Dynamics data is sparse; False makes lines invisible
                    hovertemplate=f"<b>{name}</b>: %{{y:.2f}}<extra></extra>"
                ),
                row=i+1, col=1
            )
            if invert:
                fig.update_yaxes(autorange="reversed", row=i+1, col=1)

    fig.update_layout(
        height=1400, 
        showlegend=False, 
        title_text=f"<b>Workout Time-Series Analysis ({x_label})</b>",
        margin=dict(l=60, r=20, t=80, b=60),
        hovermode="x unified", # Single tooltip box for all subplots
        spikedistance=-1,
        hoverdistance=-1
    )
    
    # Update all x-axes to have consistent spike and title
    fig.update_xaxes(
        showgrid=True, 
        showspikes=True, 
        spikemode='across', # Vertical line across all subplots
        spikethickness=1,
        spikedash='dash',
        spikecolor="gray",
        spikesnap='cursor',
        range=[0, max_x] # 3. Ensure x-axis range is preserved
    )
    fig.update_xaxes(title_text=x_label, row=7, col=1)

    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_workout_map(gpx_df, key=None, filter_noise=False):
    """
    Plots the workout route on an interactive map using Plotly.

    Args:
        gpx_df: DataFrame containing 'lat' and 'lon' columns.
        key: Unique key for the Streamlit component.
        filter_noise: Whether to filter out the first and last 2 minutes.
    """
    import plotly.graph_objects as go
    if gpx_df is None or gpx_df.empty or 'lat' not in gpx_df.columns or 'lon' not in gpx_df.columns:
        st.info("No GPS data available to plot the route.")
        return

    plot_df = gpx_df.copy()
    
    if filter_noise:
        # Calculate time from start in minutes if not already there
        if 'rel_min' not in plot_df.columns:
            plot_df['time'] = pd.to_datetime(plot_df['time'])
            start_time = plot_df['time'].min()
            plot_df['rel_min'] = (plot_df['time'] - start_time).dt.total_seconds() / 60.0
        
        max_time = plot_df['rel_min'].max()
        mask = (plot_df['rel_min'] > 2) & (plot_df['rel_min'] < (max_time - 2))
        plot_df = plot_df[mask]

    if plot_df.empty:
        st.info("No GPS data points remaining after filtering.")
        return

    # Downsample for better performance (max 1000 points)
    if len(plot_df) > 1000:
        step = len(plot_df) // 1000
        plot_df = plot_df.iloc[::step]

    # Clean data: drop NaNs in lat/lon
    plot_df = plot_df.dropna(subset=['lat', 'lon'])
    
    if plot_df.empty:
        st.info("No valid GPS coordinates found.")
        return

    # Center of the map
    center_lat = plot_df['lat'].mean()
    center_lon = plot_df['lon'].mean()

    # Render with Plotly Scattermapbox
    # Note: If Cursor's internal browser shows a white background, try viewing in an external browser (Safari/Chrome).
    fig = go.Figure(go.Scattermapbox(
        lat=plot_df['lat'],
        lon=plot_df['lon'],
        mode='lines',
        line=dict(width=4, color='#1B4F72'), # Dark blue
        name="Route",
        hoverinfo='skip'
    ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=13,
        ),
        margin={"r":0,"t":40,"l":0,"b":0},
        height=600,
        title="<b>Workout Route</b>",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key=key)
