import sys
import os
import pandas as pd

# Add the current directory to sys.path to import modular folders
sys.path.append(os.getcwd())

from parser.xml_parser import parse_export_zip

def test_parser():
    zip_path = "Reference-Folder/export.zip"
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found.")
        return
    
    print(f"Testing parser with {zip_path}...")
    try:
        with open(zip_path, 'rb') as f:
            records_df, workouts_df, all_records = parse_export_zip(f)
            
        print(f"Successfully parsed!")
        print(f"Records: {len(records_df)} rows")
        print(f"Workouts: {len(workouts_df)} rows")
        
        if not records_df.empty:
            print("\nTop 5 Record Types:")
            print(records_df['type'].value_counts().head(5))
            
        if not workouts_df.empty:
            print("\nTop 5 Workout Types:")
            print(workouts_df['workoutActivityType'].value_counts().head(5))
            
    except Exception as e:
        print(f"Parsing failed: {e}")

if __name__ == "__main__":
    test_parser()
