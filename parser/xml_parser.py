import zipfile
import pandas as pd
import numpy as np

# Suppress Pandas downcasting warnings
pd.set_option('future.no_silent_downcasting', True)

from lxml import etree
import io
from typing import Tuple, Dict, List

RELEVANT_RECORD_TYPES = {
    'HKQuantityTypeIdentifierHeartRate',
    'HKQuantityTypeIdentifierRestingHeartRate',
    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN',
    'HKQuantityTypeIdentifierVO2Max',
    'HKQuantityTypeIdentifierActiveEnergyBurned',
    'HKQuantityTypeIdentifierAppleExerciseTime',
    'HKQuantityTypeIdentifierAppleStandTime',
    'HKQuantityTypeIdentifierDistanceWalkingRunning',
    'HKQuantityTypeIdentifierRunningPower',
    'HKQuantityTypeIdentifierRunningSpeed',
    'HKQuantityTypeIdentifierRunningVerticalOscillation',
    'HKQuantityTypeIdentifierRunningGroundContactTime',
    'HKQuantityTypeIdentifierRunningStrideLength',
    'HKQuantityTypeIdentifierStepCount',
    'HKQuantityTypeIdentifierBasalEnergyBurned',
    'HKCategoryTypeIdentifierSleepAnalysis'
}

# Web Version (MVP) subset to save memory
WEB_RELEVANT_RECORD_TYPES = {
    'HKQuantityTypeIdentifierRunningVerticalOscillation',
    'HKQuantityTypeIdentifierRunningGroundContactTime',
    'HKQuantityTypeIdentifierRunningStrideLength',
}

def parse_export_zip(zip_file: io.BytesIO, capture_all: bool = False, web_version: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """
    Parses the Apple Health export.zip file and extracts Records, Workouts, and GPX routes.
    
    Args:
        zip_file: BytesIO object of the uploaded export.zip
        capture_all: If True, captures all record types into a dictionary of DataFrames
        web_version: If True, only parses record types in WEB_RELEVANT_RECORD_TYPES
        
    Returns:
        A tuple of (records_df, workouts_df, all_records_dict, gpx_routes_dict)
        gpx_routes_dict is a mapping of workout start times to GPX point dataframes.
    """
    with zipfile.ZipFile(zip_file) as z:
        # Apple Health export structure is usually apple_health_export/export.xml
        xml_path = next((f for f in z.namelist() if f.endswith('.xml') and '/' in f and f.count('/') == 1), None)
        if not xml_path:
            xml_path = next((f for f in z.namelist() if f.endswith('.xml')), None)
            
        if not xml_path:
            raise FileNotFoundError("No XML file found in the zip archive.")
        
        # Parse XML
        with z.open(xml_path) as f:
            records_df, workouts_df, all_records_dfs = _parse_xml_stream(f, capture_all=capture_all, web_version=web_version)

        # Extract GPX files (skip in web version to save memory)
        gpx_routes = {}
        if not web_version:
            gpx_files = [f for f in z.namelist() if f.endswith('.gpx')]
            for gpx_path in gpx_files:
                try:
                    with z.open(gpx_path) as gpx_f:
                        gpx_df = _parse_gpx_stream(gpx_f)
                        if not gpx_df.empty:
                            # Use the first point's timestamp as the key for matching
                            # (GPX start time often matches or is very close to workout start time)
                            start_time = gpx_df['time'].iloc[0]
                            gpx_routes[start_time] = gpx_df
                except Exception as e:
                    print(f"Error parsing GPX {gpx_path}: {e}")
            
        return records_df, workouts_df, all_records_dfs, gpx_routes

def _parse_gpx_stream(stream) -> pd.DataFrame:
    """
    Parses a GPX file stream into a DataFrame.
    """
    points = []
    tree = etree.parse(stream)
    root = tree.getroot()
    
    # GPX namespaces can vary, so we search with and without namespace
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    # Try searching for track points
    trkpts = root.xpath('//gpx:trkpt', namespaces=ns)
    if not trkpts:
        trkpts = root.xpath('//trkpt')
        
    for trkpt in trkpts:
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        ele_elem = trkpt.find('gpx:ele', ns) if trkpt.find('gpx:ele', ns) is not None else trkpt.find('ele')
        time_elem = trkpt.find('gpx:time', ns) if trkpt.find('gpx:time', ns) is not None else trkpt.find('time')
        
        ele = float(ele_elem.text) if ele_elem is not None else 0.0
        time_str = time_elem.text if time_elem is not None else None
        
        if time_str:
            points.append({
                'lat': lat,
                'lon': lon,
                'ele': ele,
                'time': pd.to_datetime(time_str, utc=True)
            })
            
    return pd.DataFrame(points)

def _parse_xml_stream(stream, capture_all: bool = False, web_version: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Uses lxml.etree.iterparse to stream and parse the XML file efficiently.
    
    Args:
        stream: The XML file stream
        capture_all: If True, captures all record types into a dictionary of DataFrames
        web_version: If True, only parses record types in WEB_RELEVANT_RECORD_TYPES
        
    Returns:
        A tuple of (records_df, workouts_df, all_records_dict)
    """
    records = []
    workouts = []
    all_records_data = {} # type: Dict[str, List[Dict]]
    
    # Define which record types to capture
    target_types = WEB_RELEVANT_RECORD_TYPES if web_version else RELEVANT_RECORD_TYPES

    # We only care about end events for Record and Workout tags
    context = etree.iterparse(stream, events=('end',), tag=('Record', 'Workout'))
    
    for _, elem in context:
        if elem.tag == 'Record':
            record_type = elem.get('type')
            
            # Extract attributes
            record_data = {
                'type': record_type,
                'startDate': elem.get('startDate'),
                'endDate': elem.get('endDate'),
                'value': elem.get('value'),
                'unit': elem.get('unit'),
                'sourceName': elem.get('sourceName'),
                'creationDate': elem.get('creationDate'),
                'device': elem.get('device')
            }

            if record_type in target_types:
                records.append(record_data)
            
            if capture_all:
                if record_type not in all_records_data:
                    all_records_data[record_type] = []
                all_records_data[record_type].append(record_data)

        elif elem.tag == 'Workout':
            workout_data = dict(elem.attrib)
            
            # Extract metadata and statistics
            for child in elem:
                if child.tag == 'MetadataEntry':
                    key = child.get('key')
                    value = child.get('value')
                    if key:
                        workout_data[f"meta_{key}"] = value
                elif child.tag == 'WorkoutStatistics':
                    stat_type = child.get('type')
                    # Map common statistics to workout attributes if they are missing
                    if stat_type == 'HKQuantityTypeIdentifierDistanceWalkingRunning':
                        workout_data['totalDistance'] = child.get('sum')
                        workout_data['totalDistanceUnit'] = child.get('unit')
                    elif stat_type == 'HKQuantityTypeIdentifierActiveEnergyBurned':
                        workout_data['totalEnergyBurned'] = child.get('sum')
                        workout_data['totalEnergyBurnedUnit'] = child.get('unit')
            
            workouts.append(workout_data)
        
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    records_df = pd.DataFrame(records)
    workouts_df = pd.DataFrame(workouts)
    
    all_records_dfs = {}
    if capture_all:
        for r_type, data_list in all_records_data.items():
            df_temp = pd.DataFrame(data_list)
            # Apply same cleanup as records_df
            all_records_dfs[r_type] = _cleanup_records(df_temp)
    
    # Cleanup and conversion for the main dataframes
    records_df = _cleanup_records(records_df)
    workouts_df = _cleanup_workouts(workouts_df)
            
    return records_df, workouts_df, all_records_dfs

def _cleanup_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    
    df['startDate'] = pd.to_datetime(df['startDate'], utc=True)
    df['endDate'] = pd.to_datetime(df['endDate'], utc=True)
    
    # Handle Sleep Analysis separately to preserve category strings/codes
    sleep_mask = df['type'] == 'HKCategoryTypeIdentifierSleepAnalysis'
    
    # For non-sleep, convert to numeric
    if (~sleep_mask).any():
        df.loc[~sleep_mask, 'value'] = pd.to_numeric(df.loc[~sleep_mask, 'value'], errors='coerce')
    
    # For sleep, map strings to integers if they exist
    if sleep_mask.any():
        sleep_map = {
            'HKCategoryValueSleepAnalysisInBed': 0,
            'HKCategoryValueSleepAnalysisAsleep': 1,
            'HKCategoryValueSleepAnalysisAwake': 2,
            'HKCategoryValueSleepAnalysisAsleepCore': 3,
            'HKCategoryValueSleepAnalysisAsleepDeep': 4,
            'HKCategoryValueSleepAnalysisAsleepREM': 5,
            'HKCategoryValueSleepAnalysisAsleepUnspecified': 1,
            # Also handle short versions just in case
            'InBed': 0, 'Asleep': 1, 'Awake': 2, 'Core': 3, 'Deep': 4, 'REM': 5
        }
        
        # 1. Strip whitespace and ensure string type for mapping
        df.loc[sleep_mask, 'value'] = df.loc[sleep_mask, 'value'].astype(str).str.strip()
        
        # 2. Map strings to integers
        df.loc[sleep_mask, 'value'] = df.loc[sleep_mask, 'value'].replace(sleep_map).infer_objects(copy=False)
        
        # 3. Convert to numeric (handles cases where it was already a number string or mapped)
        df.loc[sleep_mask, 'value'] = pd.to_numeric(df.loc[sleep_mask, 'value'], errors='coerce')
    
    # Unit normalization
    # Distance: Convert to km (Only for distance metrics)
    distance_types = {
        'HKQuantityTypeIdentifierDistanceWalkingRunning',
        'HKQuantityTypeIdentifierDistanceCycling',
        'HKQuantityTypeIdentifierDistanceSwimming'
    }
    mask_dist = df['type'].isin(distance_types)
    mask_m = (df['unit'] == 'm') & mask_dist
    if mask_m.any():
        df.loc[mask_m, 'value'] = df.loc[mask_m, 'value'] / 1000.0
        df.loc[mask_m, 'unit'] = 'km'
    
    mask_mi = (df['unit'] == 'mi') & mask_dist
    if mask_mi.any():
        df.loc[mask_mi, 'value'] = df.loc[mask_mi, 'value'] * 1.60934
        df.loc[mask_mi, 'unit'] = 'km'
    
    return df

def _cleanup_workouts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        # Ensure minimum columns even if empty
        return pd.DataFrame(columns=['startDate', 'endDate', 'duration', 'totalDistance', 'totalEnergyBurned', 'workoutActivityType'])
    
    df['startDate'] = pd.to_datetime(df['startDate'], utc=True)
    df['endDate'] = pd.to_datetime(df['endDate'], utc=True)
    
    # Standardize workout attributes
    numeric_cols = ['duration', 'totalDistance', 'totalEnergyBurned']
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate duration if missing (convert to minutes)
    mask_duration_nan = df['duration'].isna() | (df['duration'] == 0)
    if mask_duration_nan.any():
        df.loc[mask_duration_nan, 'duration'] = (df.loc[mask_duration_nan, 'endDate'] - df.loc[mask_duration_nan, 'startDate']).dt.total_seconds() / 60.0
    
    # Ensure workoutActivityType exists
    if 'workoutActivityType' not in df.columns:
        df['workoutActivityType'] = 'Unknown'
    
    # Normalize workout distance to km
    if 'totalDistanceUnit' in df.columns:
        mask_m = df['totalDistanceUnit'] == 'm'
        df.loc[mask_m, 'totalDistance'] = df.loc[mask_m, 'totalDistance'] / 1000.0
        
        mask_mi = df['totalDistanceUnit'] == 'mi'
        df.loc[mask_mi, 'totalDistance'] = df.loc[mask_mi, 'totalDistance'] * 1.60934
        
    return df
