import pandas as pd
import zipfile
import io
from typing import Dict

def create_csv_zip(all_records: Dict[str, pd.DataFrame]) -> bytes:
    """
    Creates a zip file containing CSVs for each record type.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for record_type, df in all_records.items():
            # Clean record type name for filename
            filename = f"{record_type.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')}.csv"
            csv_data = df.to_csv(index=False)
            zip_file.writestr(filename, csv_data)
    
    return zip_buffer.getvalue()
