import streamlit as st
import pandas as pd
from ui.components import plot_running_form_bubble
from analytics.metrics import get_running_dynamics_bubble_data

def show_running_analysis_page(daily_df, workouts_df, all_running):
    """
    Displays the "跑步風格" page.

    Args:
        daily_df (pd.DataFrame): Daily aggregated health data.
        workouts_df (pd.DataFrame): Individual workout data.
        all_running (pd.DataFrame): Filtered running workout data.
    """
    st.title("跑步風格")
    
    st.subheader("🏃‍♂️ Running Form Analysis (Advanced)")
    if 'records_df' in st.session_state and not st.session_state['records_df'].empty:
        records = st.session_state['records_df']
        
        # Get merged dynamics data
        merged = get_running_dynamics_bubble_data(records)
        
        if not merged.empty:
            # Date Filter Selector
            max_date = merged['startDate'].max()
            filter_options = {
                "1 Week": 7,
                "1 Month": 30,
                "3 Months": 90,
                "6 Months": 180,
                "1 Year": 365
            }

            if 'form_analysis_range_btn' not in st.session_state:
                st.session_state['form_analysis_range_btn'] = "3 Months"

            st.write("Filter Range (from most recent data):")
            cols = st.columns(len(filter_options))
            for i, label in enumerate(filter_options.keys()):
                is_selected = st.session_state['form_analysis_range_btn'] == label
                if cols[i].button(label, key=f"btn_{label}", use_container_width=True, 
                                 type="primary" if is_selected else "secondary"):
                    st.session_state['form_analysis_range_btn'] = label
                    st.rerun()

            selected_range = st.session_state['form_analysis_range_btn']
            days = filter_options[selected_range]
            filtered_merged = merged[merged['startDate'] >= (max_date - pd.Timedelta(days=days))]
            
            st.write(f"Analyzing {len(filtered_merged)} data points from {filtered_merged['startDate'].min().strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
            
            plot_running_form_bubble(filtered_merged, key="dynamics_form_bubble_page")

            # --- New Section: 6-Month Trend Analysis ---
            st.markdown("---")
            st.subheader("📈 6-Month Running Form Trend")
            st.write("Comparing your running form across the last 6 months.")

            # Get clean month boundaries for the last 6 months
            # We base it on the max_date in the merged dataset
            latest_month_start = max_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Create a 2x3 grid (2 rows, 3 columns)
            for row in range(2):
                cols = st.columns(3)
                for col in range(3):
                    month_idx = row * 3 + col
                    # Calculate start and end of the target month
                    target_month_start = latest_month_start - pd.DateOffset(months=month_idx)
                    target_month_end = target_month_start + pd.DateOffset(months=1)
                    
                    month_label = target_month_start.strftime('%B %Y')
                    
                    # Filter data for this month
                    month_data = merged[(merged['startDate'] >= target_month_start) & (merged['startDate'] < target_month_end)]
                    
                    with cols[col]:
                        st.markdown(f"#### {month_label}")
                        if not month_data.empty:
                            st.caption(f"{len(month_data)} data points")
                            plot_running_form_bubble(
                                month_data, 
                                key=f"trend_bubble_{month_idx}", 
                                height=400
                            )
                        else:
                            st.info(f"No data available for {month_label}")
        else:
            st.info("Required metrics (Vertical Oscillation, Ground Contact Time, Stride Length) not found or could not be aligned in raw records.")
    else:
        st.info("Raw health records not available for advanced form analysis.")
