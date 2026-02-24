# Physiological Analysis Trends

## Required Data Files
- `VO2Max.csv` (Extracted from `HKQuantityTypeIdentifierVO2Max`)
- `RestingHeartRate.csv` (Extracted from `HKQuantityTypeIdentifierRestingHeartRate`)
- `RunningSpeed.csv` (Extracted from `HKQuantityTypeIdentifierRunningSpeed`)

## Graph Purpose
- **Objective:** To visualize long-term trends of core physiological and performance metrics, enabling runners to correlate their cardiovascular fitness (VO2 Max) and recovery state (RHR) with their actual performance output (Running Speed).
- **Data Source:** Apple Health XML export (`export.xml`).
- **Data Types:** 
    - `HKQuantityTypeIdentifierVO2Max`
    - `HKQuantityTypeIdentifierRestingHeartRate`
    - `HKQuantityTypeIdentifierRunningSpeed`

## Graph Significance
This multi-pane visualization provides a holistic view of the runner's physiological evolution over time:

- **VO2 Max Trend:** Represents the maximum rate of oxygen consumption. A steady upward trend indicates improving cardiovascular fitness and aerobic capacity.
- **Resting Heart Rate (RHR) Trend:** A key marker of cardiovascular efficiency and autonomic nervous system balance. Lowering RHR often reflects improved fitness or effective recovery. Spikes in RHR can indicate overtraining, illness, or high stress.
- **Running Speed Trend:** Provides a performance baseline. Correlating speed with physiological markers helps determine if performance gains are driven by physiological improvements or increased effort.

## Graph Metrics/Axes
- **X-axis (Shared):** **Date/Time**. The x-axis is shared across all three subplots to allow for direct vertical comparison of trends.
- **Y-axis (VO2 Max):** **ml/kg/min**. Visualizes the aerobic capacity.
- **Y-axis (Resting Heart Rate):** **bpm (Beats Per Minute)**. Visualizes heart health and recovery.
- **Y-axis (Running Speed):** **km/h**. Visualizes performance pace.
- **Markers:** **Daily Averages**. Individual points represent the mean value recorded for that specific day.
- **Solid Lines:** **7-Day Moving Average**. A smoothing line used to filter out daily noise and highlight the underlying trend.

## Calculation Logic & Methods
- **Pre-processing:** 
    - Data is filtered based on the user-selected date range (e.g., Last 6 Months, All Data).
    - `Running Speed` is converted from Apple's default `m/s` to `km/h`.
- **Merging Logic:** 
    - Each metric is resampled to a daily frequency (`'D'`) using the `mean()` aggregation.
    - Linear interpolation is applied to fill gaps of up to 14 days to ensure trend continuity in the visualization.
- **Formulas:**
    - **Speed Conversion:** `Running Speed (km/h) = Running Speed (m/s) * 3.6`
    - **7-Day Moving Average:** `rolling(window=7, min_periods=1).mean()`
- **Units:**
    - VO2 Max: ml/kg/min
    - Resting Heart Rate: bpm
    - Running Speed: km/h
