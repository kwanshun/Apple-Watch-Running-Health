import streamlit as st
import pandas as pd
from utils.export_helpers import create_csv_zip

def show_raw_data_page(all_records_dict):
    st.title("📄 Raw Data")
    st.header("Reference Project Mirror: Raw Data Export")
    st.write("""
    This page mimics the functionality of the `apple-health-parser` reference project. 
    It extracts every unique record type found in your Apple Health XML and allows you to download them as raw CSV files.
    """)
    
    if all_records_dict:
        st.subheader(f"Discovered {len(all_records_dict)} Record Types")
        
        summary_data = []
        for r_type, df in all_records_dict.items():
            summary_data.append({
                "Record Type": r_type,
                "Count": len(df),
                "Columns": ", ".join(df.columns)
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
        st.subheader("Download All Records")
        with st.spinner("Preparing ZIP file..."):
            zip_data = create_csv_zip(all_records_dict)
            st.download_button(
                label="📥 Download All Records as CSV (ZIP)",
                data=zip_data,
                file_name="apple_health_raw_data.zip",
                mime="application/zip"
            )
        
        st.subheader("Preview Individual Record Types")
        selected_type = st.selectbox("Select a record type to preview:", options=sorted(list(all_records_dict.keys())))
        if selected_type:
            st.write(f"Showing the last 100 records for `{selected_type}`")
            st.dataframe(all_records_dict[selected_type].tail(100), use_container_width=True)
    else:
        st.info("No records found to export.")
