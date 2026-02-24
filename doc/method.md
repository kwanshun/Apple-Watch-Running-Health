# Data Processing Methodology

This document describes the process of transforming raw Apple Health data from an `export.zip` file into interactive visual charts.

## 1. Dual-Source Data Strategy

The application adopts a dual-source strategy to balance detail with performance, utilizing both the `export.xml` and GPX files for different analytical purposes.

### A. High-Level Summaries (`export.xml`)
The `export.xml` is used for high-level summaries, such as **"Average Pace per Month"** or **"Pace Trends over the last year."**

**Reasoning:**
1.  **Centralization vs. Fragmentation:** `export.xml` is a single source containing a high-level summary of every workout. To calculate a monthly average, the app only needs to read one file. Conversely, GPX files are fragmented; every GPS-tracked run is a separate file, making it resource-intensive to parse dozens or hundreds of files for a long-term trend.
2.  **Processing Speed and Memory:** `export.xml` includes pre-calculated summaries (total distance, total duration). Calculating "Average Pace" from these is a simple division taking milliseconds. Processing raw data from GPX files (thousands of track points per run) across an entire year would involve millions of data points, significantly slowing down performance.
3.  **Data Availability:** Not all runs have GPX files (e.g., treadmill runs or areas with poor GPS). However, Apple Health always creates a workout entry in `export.xml`. Relying only on GPX would result in missing data for indoor activities.

### B. Detailed Activity Analysis (GPX Files)
GPX files are used to generate the actual **"Pace vs. Distance"** or **"Pace vs. Time"** charts for individual runs, and to provide the most accurate **Total Distance** and **Average Pace** for outdoor workouts.

**Reasoning:**
- **Granularity:** GPX files provide the smooth, detailed second-by-second curve that runners expect to see for an in-depth review of a specific session.
- **Accuracy:** GPX distance calculation (using Haversine) avoids common XML issues such as double-counting records from multiple devices (Watch + iPhone) or missing summary attributes in the `<Workout>` tag.

## 2. Data Extraction and Parsing

The application handles the Apple Health export by unzipping the archive and focusing on several key components:

### Key Files Extracted
- **`export.xml`**: The primary data source containing all health records and workout summaries.
- **GPX Files**: Located in the `workout-routes/` directory within the zip. These files contain high-resolution GPS coordinates (longitude, latitude, elevation) and timestamps for specific outdoor workouts.
- **XML Tags**: The parser specifically targets `<Record>` and `<Workout>` tags using efficient streaming techniques (like `lxml.etree.iterparse`) to handle files that can often exceed 1GB in size.

### Data Types Read Directly from HealthKit
The following metrics are extracted directly from the XML records as "source-of-truth" samples:
- `HKQuantityTypeIdentifierHeartRate`: Heart rate readings.
- `HKQuantityTypeIdentifierRunningPower`: Power output (Watts).
- `HKQuantityTypeIdentifierRunningVerticalOscillation`: Vertical bounce (cm).
- `HKQuantityTypeIdentifierRunningGroundContactTime`: Time spent on the ground (ms).
- `HKQuantityTypeIdentifierRunningStrideLength`: Distance of each step (m).
- `HKQuantityTypeIdentifierVO2Max`: Estimated maximal oxygen consumption.
- `HKQuantityTypeIdentifierRestingHeartRate`: Daily resting heart rate.
- `HKCategoryTypeIdentifierSleepAnalysis`: Sleep stages (Core, Deep, REM, Awake).

## 3. Calculated and Derived Metrics

Not all data displayed in the charts exists in raw form. Several key metrics are calculated to provide deeper insights:

- **Distance**: While individual distance records exist, the total distance for a specific workout is often validated by summing up all `HKQuantityTypeIdentifierDistanceWalkingRunning` samples that fall within the workout's start and end times.
- **Running Pace**: Pace is calculated over the entire course of a workout by dividing the **Total Duration** (in minutes) by the **Total Distance** (in kilometers).
  - *Formula*: `Pace = Duration (min) / Distance (km)`
- **Efficiency Factor (EF)**: A measure of aerobic efficiency calculated by dividing the **Average Power** or **Pace** by the **Average Heart Rate**.
- **Acute:Chronic Workload Ratio (ACWR)**: Calculated by comparing the workload of the last 7 days (Acute) against the average workload of the last 28 days (Chronic).

## 4. Advanced Processing Logic

To ensure data from different sensors (which might record at slightly different intervals) can be compared accurately, the app uses specialized merging techniques:

> **Note: 多表配對 (Merge Logic - pd.merge_asof)**
> 由於 Apple Watch 的各種指標（VO, GCT, SL）記錄時間點並非完全同步（可能相差幾毫秒），`pd.merge_asof` 允許程式在指定的 **tolerance (容忍度，如 2 秒)** 內尋找最接近的時間點進行對齊合併，避免因時間微差導致數據無法對應。

## 5. Visualization Pipeline

Once the data is cleaned and aligned:
1. **Aggregation**: Raw high-frequency samples are aggregated into daily or workout-level summaries.
2. **Filtering**: The app filters for specific activity types, primarily focusing on `HKWorkoutActivityTypeRunning`.
3. **Chart Generation**: Processed dataframes are passed to visualization libraries (like Plotly or Streamlit) to generate interactive time-series charts, enabling users to zoom into specific runs or view long-term health trends.