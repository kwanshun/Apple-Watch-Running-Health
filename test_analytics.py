import pandas as pd
import numpy as np
from analytics.metrics import calculate_acwr, calculate_tsb, aggregate_daily_metrics
from parser.xml_parser import parse_export_zip
import os

def test_analytics():
    zip_path = "Reference-Folder/export.zip"
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found.")
        return
    
    print(f"Loading data from {zip_path}...")
    with open(zip_path, 'rb') as f:
        records_df, workouts_df, all_records = parse_export_zip(f)
    
    print("Aggregating daily metrics...")
    daily_df = aggregate_daily_metrics(records_df)
    
    if daily_df.empty:
        print("No daily metrics aggregated.")
        return
    
    print(f"Daily metrics: {len(daily_df)} days")
    print(daily_df.columns.tolist())
    
    # Calculate ACWR based on Distance Walking/Running
    dist_col = 'HKQuantityTypeIdentifierDistanceWalkingRunning'
    if dist_col in daily_df.columns:
        print("\nCalculating ACWR for Distance...")
        daily_df['acwr'] = calculate_acwr(daily_df[dist_col])
        print(daily_df[['acwr']].dropna().tail())
    
    # Calculate TSB
    if dist_col in daily_df.columns:
        print("\nCalculating TSB for Distance...")
        tsb, atl, ctl = calculate_tsb(daily_df[dist_col])
        daily_df['tsb'] = tsb
        daily_df['atl'] = atl
        daily_df['ctl'] = ctl
        print(daily_df[['tsb', 'atl', 'ctl']].dropna().tail())

if __name__ == "__main__":
    test_analytics()
