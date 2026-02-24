import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
import streamlit as st

# Suppress Pandas downcasting warnings
pd.set_option('future.no_silent_downcasting', True)

def calculate_acwr(daily_workload: pd.Series, acute_window: int = 7, chronic_window: int = 28) -> pd.Series:
    """
    Calculates the Acute:Chronic Workload Ratio.
    ACWR = (Rolling Sum of Acute Window) / (Rolling Average of Chronic Window * Acute Window)
    Target: 0.8 - 1.3
    """
    acute_load = daily_workload.rolling(window=acute_window, min_periods=1).sum()
    chronic_load = daily_workload.rolling(window=chronic_window, min_periods=1).mean()
    
    # ACWR is acute sum / (chronic avg * acute_window)
    # This simplifies to: (acute_avg * acute_window) / (chronic_avg * acute_window) = acute_avg / chronic_avg
    # But usually it's defined as acute_sum / (chronic_avg * 7)
    acwr = acute_load / (chronic_load * acute_window)
    return acwr

def calculate_tsb(daily_load: pd.Series, atl_days: int = 7, ctl_days: int = 42) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates Training Stress Balance (TSB), Fatigue (ATL), and Fitness (CTL).
    Using Exponential Moving Averages (EMA).
    TSB = CTL - ATL
    """
    # ATL (Acute Training Load) - Fatigue
    atl = daily_load.ewm(span=atl_days, adjust=False).mean()
    
    # CTL (Chronic Training Load) - Fitness
    ctl = daily_load.ewm(span=ctl_days, adjust=False).mean()
    
    tsb = ctl.shift(1) - atl.shift(1)  # TSB is usually calculated based on previous day's fitness/fatigue
    return tsb, atl, ctl

def calculate_efficiency_factor(avg_power: pd.Series, avg_hr: pd.Series) -> pd.Series:
    """
    Calculates Efficiency Factor (EF).
    EF = Average Power / Average Heart Rate
    """
    # Handle division by zero or NaN
    ef = avg_power / avg_hr
    return ef.replace([np.inf, -np.inf], np.nan)

@st.cache_data
def aggregate_daily_metrics(records_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates raw records into daily metrics for health markers.
    """
    if records_df.empty:
        return pd.DataFrame()
    
    # Extract date
    df = records_df.copy()
    df['date'] = df['startDate'].dt.date
    
    # Separate Sleep from other records
    sleep_mask = df['type'] == 'HKCategoryTypeIdentifierSleepAnalysis'
    sleep_df = df[sleep_mask].copy()
    health_df = df[~sleep_mask].copy()
    
    # Pivot health metrics (mean for HRV, RHR, VO2Max, etc.)
    daily = health_df.pivot_table(
        index='date', 
        columns='type', 
        values='value', 
        aggfunc='mean'
    )
    
    # For some metrics, we want sum
    sum_metrics = [
        'HKQuantityTypeIdentifierActiveEnergyBurned',
        'HKQuantityTypeIdentifierAppleExerciseTime',
        'HKQuantityTypeIdentifierAppleStandTime',
        'HKQuantityTypeIdentifierDistanceWalkingRunning',
        'HKQuantityTypeIdentifierStepCount',
        'HKQuantityTypeIdentifierBasalEnergyBurned'
    ]
    daily_sums = health_df[health_df['type'].isin(sum_metrics)].pivot_table(
        index='date',
        columns='type',
        values='value',
        aggfunc='sum'
    )
    
    # Merge health metrics
    for col in daily_sums.columns:
        daily[col] = daily_sums[col]

    # Process Sleep
    if not sleep_df.empty:
        # Duration in hours
        sleep_df['duration_hrs'] = (sleep_df['endDate'] - sleep_df['startDate']).dt.total_seconds() / 3600.0
        
        # Aggregate sleep stages by date (mapping values to stages)
        # 0: In Bed, 1: Asleep, 2: Awake, 3: Core, 4: Deep, 5: REM
        sleep_daily = sleep_df.pivot_table(
            index='date',
            columns='value',
            values='duration_hrs',
            aggfunc='sum'
        )
        
        # Rename columns robustly
        # Handle various possible types for columns (int, float, string representation of numbers)
        rename_map = {
            0: 'sleep_in_bed', 0.0: 'sleep_in_bed', '0': 'sleep_in_bed', '0.0': 'sleep_in_bed',
            1: 'sleep_asleep', 1.0: 'sleep_asleep', '1': 'sleep_asleep', '1.0': 'sleep_asleep',
            2: 'sleep_awake', 2.0: 'sleep_awake', '2': 'sleep_awake', '2.0': 'sleep_awake',
            3: 'sleep_core', 3.0: 'sleep_core', '3': 'sleep_core', '3.0': 'sleep_core',
            4: 'sleep_deep', 4.0: 'sleep_deep', '4': 'sleep_deep', '4.0': 'sleep_deep',
            5: 'sleep_rem', 5.0: 'sleep_rem', '5': 'sleep_rem', '5.0': 'sleep_rem'
        }
        sleep_daily = sleep_daily.rename(columns=rename_map)
        
        # Ensure all expected sleep columns exist (even if empty) to avoid calculation errors
        sleep_stage_cols = ['sleep_in_bed', 'sleep_asleep', 'sleep_awake', 'sleep_core', 'sleep_deep', 'sleep_rem']
        for col in sleep_stage_cols:
            if col not in sleep_daily.columns:
                sleep_daily[col] = 0.0
        
        # Calculate total sleep (sum of core, deep, rem, asleep)
        # We explicitly sum these specific columns
        actual_sleep_stages = ['sleep_asleep', 'sleep_core', 'sleep_deep', 'sleep_rem']
        sleep_daily['total_sleep'] = sleep_daily[actual_sleep_stages].sum(axis=1)
            
        daily = daily.join(sleep_daily, how='outer')
    
    return daily

@st.cache_data
def process_running_workouts(workouts_df: pd.DataFrame, records_df: pd.DataFrame = None, gpx_routes: Dict[pd.Timestamp, pd.DataFrame] = None) -> pd.DataFrame:
    """
    Filters and processes running workouts, cross-referencing records and GPX for accurate metrics.
    """
    if workouts_df.empty:
        return pd.DataFrame()
    
    # Filter for running
    running = workouts_df[workouts_df['workoutActivityType'] == 'HKWorkoutActivityTypeRunning'].copy()
    
    if running.empty:
        return running
        
    # --- De-duplication Logic ---
    # Group workouts by start time (within 10 minutes) and duration (within 10 minutes)
    # This is more robust than comparing only adjacent rows.
    if not running.empty:
        running = running.sort_values(by=['startDate', 'totalDistance'], ascending=[True, False])
        
        # We'll use a simplified grouping: if multiple workouts start within 10m of each other
        # and have durations within 10m, we keep the one with the most distance (likely the most complete).
        deduped_rows = []
        if len(running) > 0:
            # Sort is already done
            current_group = [running.iloc[0]]
            
            for i in range(1, len(running)):
                row = running.iloc[i]
                prev_row = current_group[-1]
                
                start_diff = abs((row['startDate'] - prev_row['startDate']).total_seconds())
                dur_diff = abs(row['duration'] - prev_row['duration'])
                
                if start_diff < 600 and dur_diff < 600:
                    current_group.append(row)
                else:
                    # Keep the one with most distance in the group
                    best_workout = max(current_group, key=lambda x: x['totalDistance'] if pd.notna(x['totalDistance']) else 0)
                    deduped_rows.append(best_workout)
                    current_group = [row]
            
            # Don't forget the last group
            best_workout = max(current_group, key=lambda x: x['totalDistance'] if pd.notna(x['totalDistance']) else 0)
            deduped_rows.append(best_workout)
            
            running = pd.DataFrame(deduped_rows)
    # ----------------------------

    if records_df is not None and not records_df.empty:
        # Cross-reference HR, Power and Distance records
        hr_records = records_df[records_df['type'] == 'HKQuantityTypeIdentifierHeartRate']
        power_records = records_df[records_df['type'] == 'HKQuantityTypeIdentifierRunningPower']
        dist_records = records_df[records_df['type'] == 'HKQuantityTypeIdentifierDistanceWalkingRunning']
        
        avg_hrs = []
        avg_powers = []
        total_dists = []
        gpx_match_flags = []
        
        for idx, workout in running.iterrows():
            w_start = workout['startDate']
            w_end = workout['endDate']
            w_source = workout.get('sourceName')
            
            # --- HR & Power ---
            # Filter records by same source as workout to avoid double counting from multiple devices
            w_hr = hr_records[(hr_records['startDate'] < w_end) & (hr_records['endDate'] > w_start)]
            if w_source and not w_hr.empty:
                w_hr_source = w_hr[w_hr['sourceName'] == w_source]
                if not w_hr_source.empty:
                    w_hr = w_hr_source
            avg_hrs.append(w_hr['value'].mean() if not w_hr.empty else np.nan)
            
            w_power = power_records[(power_records['startDate'] < w_end) & (power_records['endDate'] > w_start)]
            if w_source and not w_power.empty:
                w_power_source = w_power[w_power['sourceName'] == w_source]
                if not w_power_source.empty:
                    w_power = w_power_source
            avg_powers.append(w_power['value'].mean() if not w_power.empty else np.nan)

            # --- Distance & Pace (GPX vs XML) ---
            found_gpx = False
            gpx_dist = 0.0
            
            # 1. Try to find a matching GPX route
            if gpx_routes:
                # Find GPX that starts within 2 minutes of the workout start
                for gpx_start, gpx_df in gpx_routes.items():
                    if abs((gpx_start - w_start).total_seconds()) < 120:
                        gpx_dist = _calculate_haversine_distance(gpx_df)
                        found_gpx = True
                        break
            
            gpx_match_flags.append(found_gpx)
            
            if found_gpx:
                # If GPX found, it is the most reliable source of distance
                total_dists.append(gpx_dist)
            else:
                # 2. Fallback to Workout attribute
                w_dist_attr = workout.get('totalDistance')
                if pd.isna(w_dist_attr) or w_dist_attr == 0:
                    # 3. Fallback to summing Records
                    w_dist_rec = dist_records[(dist_records['startDate'] >= w_start) & (dist_records['endDate'] <= w_end)]
                    
                    if not w_dist_rec.empty:
                        # CRITICAL: Pick a single source to avoid double counting (Watch + iPhone)
                        # Prioritize 'Watch' or 'Apple'
                        sources = w_dist_rec['sourceName'].unique()
                        best_source = None
                        for s in sources:
                            if 'Watch' in str(s) or 'Apple' in str(s):
                                best_source = s
                                break
                        
                        # If no 'Watch' source, just pick the one with most records
                        if not best_source:
                            best_source = w_dist_rec['sourceName'].value_counts().idxmax()
                        
                        w_dist_rec_filtered = w_dist_rec[w_dist_rec['sourceName'] == best_source]
                        total_dists.append(w_dist_rec_filtered['value'].sum())
                    else:
                        # 4. Loose fallback (overlapping window)
                        w_dist_rec_loose = dist_records[(dist_records['startDate'] < w_end) & (dist_records['endDate'] > w_start)]
                        if not w_dist_rec_loose.empty:
                            sources = w_dist_rec_loose['sourceName'].unique()
                            best_source = None
                            for s in sources:
                                if 'Watch' in str(s) or 'Apple' in str(s):
                                    best_source = s
                                    break
                            if not best_source:
                                best_source = w_dist_rec_loose['sourceName'].value_counts().idxmax()
                            
                            w_dist_rec_loose_filtered = w_dist_rec_loose[w_dist_rec_loose['sourceName'] == best_source]
                            total_dists.append(w_dist_rec_loose_filtered['value'].sum())
                        else:
                            total_dists.append(np.nan)
                else:
                    total_dists.append(w_dist_attr)
            
        running['avg_hr'] = avg_hrs
        running['avg_power'] = avg_powers
        running['totalDistance'] = total_dists
        running['has_gpx'] = gpx_match_flags
        
        # Recalculate pace and EF
        running['pace_min_km'] = np.where(
            running['totalDistance'] > 0, 
            running['duration'] / running['totalDistance'], 
            np.nan
        )
        running['efficiency_factor'] = running['avg_power'] / running['avg_hr']
        
    return running

def _calculate_haversine_distance(df: pd.DataFrame) -> float:
    """
    Calculates total distance in km from a dataframe of lat/lon points.
    """
    return np.sum(_calculate_point_distances(df))

def _calculate_point_distances(df: pd.DataFrame) -> np.ndarray:
    """
    Calculates distance between consecutive points in km using the Haversine formula.
    """
    if df.empty or len(df) < 2:
        return np.array([0.0] * len(df))
    
    # Haversine formula
    lat = np.radians(df['lat'].values)
    lon = np.radians(df['lon'].values)
    
    dlat = np.diff(lat)
    dlon = np.diff(lon)
    
    a = np.sin(dlat/2)**2 + np.cos(lat[:-1]) * np.cos(lat[1:]) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    r = 6371 # Earth radius in km
    
    distances = r * c
    return np.concatenate(([0.0], distances))

def process_gpx_timeseries(gpx_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates time-series pace and elevation from GPX data.
    
    Args:
        gpx_df: DataFrame with 'lat', 'lon', 'ele', 'time' columns.
        
    Returns:
        DataFrame with added 'pace_min_km', 'cum_dist_km', etc.
    """
    if gpx_df.empty:
        return pd.DataFrame()
        
    df = gpx_df.copy().sort_values('time')
    
    # Distance deltas
    df['dist_delta_km'] = _calculate_point_distances(df)
    
    # Time deltas in seconds
    df['time_delta_sec'] = df['time'].diff().dt.total_seconds().fillna(0)
    
    # Cumulative distance
    df['cum_dist_km'] = df['dist_delta_km'].cumsum()
    
    # Pace (min/km)
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        df['pace_min_km'] = (df['time_delta_sec'] / 60.0) / df['dist_delta_km']
        
    # Clean up infinite values and outliers (e.g. pace > 20 min/km or < 2 min/km usually errors)
    df['pace_min_km'] = df['pace_min_km'].replace([np.inf, -np.inf], np.nan)
    df.loc[df['pace_min_km'] > 20, 'pace_min_km'] = np.nan
    
    # Apply rolling average to smooth pace (10-point window for high-res GPX)
    df['pace_smoothed'] = df['pace_min_km'].rolling(window=10, min_periods=1, center=True).mean()
    
    return df

def get_workout_dynamics_timeseries(workout_start: pd.Timestamp, workout_end: pd.Timestamp, records_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts time-series data for HR, Power, VO, GCT, SL from XML records for a workout.
    
    Args:
        workout_start: Start timestamp.
        workout_end: End timestamp.
        records_df: Raw records DataFrame.
        
    Returns:
        DataFrame indexed by time with columns for each metric.
    """
    types = {
        'HKQuantityTypeIdentifierHeartRate': 'heart_rate',
        'HKQuantityTypeIdentifierRunningPower': 'power',
        'HKQuantityTypeIdentifierRunningVerticalOscillation': 'vo',
        'HKQuantityTypeIdentifierRunningGroundContactTime': 'gct',
        'HKQuantityTypeIdentifierRunningStrideLength': 'stride_length'
    }
    
    # Filter records with a 2-minute buffer to capture overlapping samples (especially for older data)
    buffer = pd.Timedelta('2min')
    mask = (records_df['startDate'] >= (workout_start - buffer)) & (records_df['startDate'] <= (workout_end + buffer)) & (records_df['type'].isin(types.keys()))
    workout_records = records_df[mask].copy()
    
    if workout_records.empty:
        return pd.DataFrame()
    
    # Ensure value is numeric
    workout_records['value'] = pd.to_numeric(workout_records['value'], errors='coerce')
    
    # Pivot
    ts_df = workout_records.pivot_table(
        index='startDate',
        columns='type',
        values='value',
        aggfunc='mean'
    ).rename(columns=types)
    
    return ts_df.sort_index()

def align_workout_data(dynamics_df: pd.DataFrame, gpx_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Aligns XML dynamics data and GPX data onto a single consistent timeline.
    
    Args:
        dynamics_df: DataFrame indexed by timestamp with dynamics columns.
        gpx_df: DataFrame with 'time' column and GPX metrics.
        
    Returns:
        A single aligned DataFrame with a rounded 'rel_min' column for unified hover.
    """
    if dynamics_df is None or dynamics_df.empty:
        if gpx_df is None or gpx_df.empty:
            return pd.DataFrame()
        # If only GPX exists
        df = gpx_df.copy().set_index('time').sort_index()
        df.index = pd.to_datetime(df.index, utc=True)
    else:
        dynamics_df = dynamics_df.copy().sort_index()
        # Force index to UTC aware datetime64[ns, UTC]
        dynamics_df.index = pd.to_datetime(dynamics_df.index, utc=True)

        if gpx_df is not None and not gpx_df.empty:
            gpx_df = gpx_df.copy().set_index('time').sort_index()
            # Force GPX index to UTC aware datetime64[ns, UTC]
            gpx_df.index = pd.to_datetime(gpx_df.index, utc=True)

            # Merge GPX onto Dynamics (nearest neighbor alignment)
            # We use 5s tolerance to account for asynchronous recording
            df = pd.merge_asof(
                dynamics_df, gpx_df, 
                left_index=True, right_index=True, 
                direction='nearest', tolerance=pd.Timedelta('5s')
            )
            
            # Interpolate GPX metrics to fill NaNs for dynamics points that fell between GPX points
            gpx_cols = [c for c in gpx_df.columns if c in df.columns]
            if gpx_cols:
                df[gpx_cols] = df[gpx_cols].interpolate(method='time')
        else:
            df = dynamics_df

    if df.empty:
        return df

    # Create Rounded Relative Time (The "Secret Sauce" for Unified Hover)
    # Ensure start_time is UTC to avoid subtraction issues
    start_time = pd.to_datetime(df.index.min(), utc=True)
    df['rel_min'] = ((pd.to_datetime(df.index, utc=True) - start_time).total_seconds() / 60.0).round(2)
    
    return df

@st.cache_data
def get_running_dynamics_bubble_data(records_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts and aligns VO, GCT, and Stride Length records for bubble chart analysis.
    
    Args:
        records_df: Raw HealthKit records.
        
    Returns:
        Merged DataFrame with aligned dynamics metrics.
    """
    if records_df.empty:
        return pd.DataFrame()
        
    # Extract metrics
    vo_df = records_df[records_df['type'] == 'HKQuantityTypeIdentifierRunningVerticalOscillation'].copy()
    gct_df = records_df[records_df['type'] == 'HKQuantityTypeIdentifierRunningGroundContactTime'].copy()
    sl_df = records_df[records_df['type'] == 'HKQuantityTypeIdentifierRunningStrideLength'].copy()
    
    if vo_df.empty or gct_df.empty or sl_df.empty:
        return pd.DataFrame()
        
    # Rename columns for merging and ensure sorting
    vo_df = vo_df[['startDate', 'value']].rename(columns={'value': 'RunningVerticalOscillation'}).sort_values('startDate')
    gct_df = gct_df[['startDate', 'value']].rename(columns={'value': 'RunningGroundContactTime'}).sort_values('startDate')
    sl_df = sl_df[['startDate', 'value']].rename(columns={'value': 'RunningStrideLength'}).sort_values('startDate')
    
    # Ensure numeric values
    vo_df['RunningVerticalOscillation'] = pd.to_numeric(vo_df['RunningVerticalOscillation'], errors='coerce')
    gct_df['RunningGroundContactTime'] = pd.to_numeric(gct_df['RunningGroundContactTime'], errors='coerce')
    sl_df['RunningStrideLength'] = pd.to_numeric(sl_df['RunningStrideLength'], errors='coerce')
    
    # Merge dataframes using pd.merge_asof with 2s tolerance
    merged = pd.merge_asof(vo_df, gct_df, on='startDate', tolerance=pd.Timedelta('2s'), direction='nearest')
    merged = pd.merge_asof(merged, sl_df, on='startDate', tolerance=pd.Timedelta('2s'), direction='nearest')
    
    # Drop rows where any of the metrics are missing after merge
    merged = merged.dropna(subset=['RunningVerticalOscillation', 'RunningGroundContactTime', 'RunningStrideLength'])
    
    if not merged.empty:
        # Calculate Vertical Ratio: (VO_cm / SL_cm) * 100
        # Stride Length is in meters, VO is in cm.
        merged['VerticalRatio'] = (merged['RunningVerticalOscillation'] / (merged['RunningStrideLength'] * 100)) * 100
        
    return merged
