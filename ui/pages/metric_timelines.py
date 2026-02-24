import streamlit as st
import pandas as pd
from ui.components import plot_workout_timeseries, plot_workout_map, plot_running_form_bubble
from analytics.metrics import get_workout_dynamics_timeseries, process_gpx_timeseries, get_running_dynamics_bubble_data

def show_metric_timelines_page(daily_df, workouts_df, all_running):
    """
    Displays the "指標分析" (Metric Timelines) page.

    Args:
        daily_df (pd.DataFrame): Daily aggregated health data.
        workouts_df (pd.DataFrame): Individual workout data.
        all_running (pd.DataFrame): Filtered running workout data.
    """
    st.title("指標分析")
    
    if 'records_df' not in st.session_state or st.session_state['records_df'].empty:
        st.info("Please upload your Apple Health export.zip on the Landing page to view analysis.")
        return

    records = st.session_state['records_df']

    st.subheader("🎯 Single Workout Time-Series")
    
    if not all_running.empty:
        # Create a friendly label for the dropdown: Date | Distance | Pace
        workout_options = all_running.copy().sort_values('startDate', ascending=False)
        
        def format_pace(pace_min):
            if pd.isna(pace_min): return "N/A"
            mins = int(pace_min)
            secs = int((pace_min - mins) * 60)
            return f"{mins}:{secs:02d} /km"

        def format_distance(dist):
            if pd.isna(dist) or dist == 0: return "Unknown"
            return f"{dist:.2f} km"

        workout_options['label'] = workout_options.apply(
            lambda x: f"{x['startDate'].strftime('%Y-%m-%d %H:%M')} | {format_distance(x['totalDistance'])} | {format_pace(x['pace_min_km'])}{' (GPS)' if x.get('has_gpx') else ''}", 
            axis=1
        )
        
        selected_workout_label = st.selectbox(
            "Select a Running Workout to Analyze:",
            workout_options['label'].tolist(),
            index=0, # Default to the most recent run
            key="metric_timelines_workout_select"
        )
        
        # Get the selected workout's data
        selected_workout = workout_options[workout_options['label'] == selected_workout_label].iloc[0]
        w_start = selected_workout['startDate']
        w_end = selected_workout['endDate']
        
        col_w1, col_w2, col_w3 = st.columns(3)
        
        dist_label = "Distance (GPS)" if selected_workout.get('has_gpx') else "Distance (XML)"
        col_w1.metric(dist_label, format_distance(selected_workout['totalDistance']))
        
        pace_label = "Pace (GPS)" if selected_workout.get('has_gpx') else "Pace (XML)"
        col_w2.metric(pace_label, format_pace(selected_workout['pace_min_km']))

        avg_hr = selected_workout.get('avg_hr')
        col_w3.metric("Average Heart Rate", f"{avg_hr:.0f} bpm" if not pd.isna(avg_hr) else "N/A")
        
        # --- Time-Series Analysis Section ---
        st.markdown("### 📈 Time-Series Analysis")
        filter_noise_ts = st.toggle("Filter Start/End Noise (2 min)", value=False, key="metric_timelines_noise_toggle_ts")
        
        with st.spinner("Generating time-series graphs..."):
            # 1. Get XML dynamics timeseries (HR, Power, VO, GCT, SL)
            ts_dynamics = get_workout_dynamics_timeseries(w_start, w_end, records)

            # --- Data Availability Feedback ---
            if ts_dynamics.empty:
                st.warning("⚠️ No high-frequency dynamics data (HR, Power, etc.) found for this workout in the export.")
            elif 'heart_rate' in ts_dynamics.columns:
                hr_count = ts_dynamics['heart_rate'].count()
                if hr_count < 5:
                    st.info("ℹ️ **Sparse Heart Rate Data:** Only a few heart rate samples were found for this workout. Older workouts or specific export settings may only include a 'Summary Record' instead of a continuous curve.")
            
            # 2. Find and process matching GPX route for Pace and Elevation
            ts_gpx = None
            if 'gpx_routes' in st.session_state:
                gpx_routes = st.session_state['gpx_routes']
                for gpx_start, gpx_df in gpx_routes.items():
                    # Match GPX starting within 2 minutes of workout
                    if abs((gpx_start - w_start).total_seconds()) < 120:
                        ts_gpx = process_gpx_timeseries(gpx_df)
                        break
            
            # 3. Plot the 7-row subplot
            plot_workout_timeseries(ts_dynamics, ts_gpx, workout_start=w_start, key="metric_timelines_timeseries_plot", filter_noise=filter_noise_ts)

            # 4. Plot the map if GPX data is available
            if ts_gpx is not None and not ts_gpx.empty:
                st.markdown("### 🗺️ Workout Route")
                plot_workout_map(ts_gpx, key="metric_timelines_map", filter_noise=filter_noise_ts)

            # 5. Plot Running Form Bubble Chart (Moved from Running Style page)
            st.markdown("### 🏃‍♂️ Running Form Analysis")
            merged_dynamics = get_running_dynamics_bubble_data(records)
            if not merged_dynamics.empty:
                # Filter for the selected workout
                workout_merged = merged_dynamics[(merged_dynamics['startDate'] >= w_start) & (merged_dynamics['startDate'] <= w_end)]
                
                if not workout_merged.empty:
                    st.info(f"Analyzing {len(workout_merged)} dynamics points (VO, GCT, SL) for this workout.")
                    filter_noise_bubble = st.toggle("Filter Start/End Noise (2 min)", value=False, key="metric_timelines_noise_toggle_bubble")
                    plot_running_form_bubble(workout_merged, key="metric_timelines_form_bubble", filter_noise=filter_noise_bubble)
                else:
                    st.warning("No running dynamics data (VO, GCT, SL) found for this specific workout.")
            else:
                st.info("Required metrics (Vertical Oscillation, Ground Contact Time, Stride Length) not found in raw records.")
    else:
        st.info("No running workouts available for analysis.")
