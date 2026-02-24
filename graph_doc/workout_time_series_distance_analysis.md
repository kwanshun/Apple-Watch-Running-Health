# Workout Time-Series Analysis (Distance-Based)

## Required Data Files

- `HeartRate.csv` (from XML)
- `RunningPower.csv` (from XML)
- `RunningVerticalOscillation.csv` (from XML)
- `RunningGroundContactTime.csv` (from XML)
- `RunningStrideLength.csv` (from XML)
- `route_YYYY-MM-DD_H.MMpm.gpx` (Required for GPS/Distance data)

## Graph Purpose

- **Objective:** To provide a synchronized, multi-metric timeline of a single workout, using **cumulative distance** as the baseline. This allows runners to analyze performance and form relative to the progression of the course (e.g., "how did my form break down at kilometer 10?").
- **Data Source:** 
  - **XML Records:** Heart Rate, Running Power, Vertical Oscillation, Ground Contact Time, Stride Length.
  - **GPX Files:** GPS coordinates (for distance), Elevation, and Pace.
- **Data Types:** 
  - `HKQuantityTypeIdentifierHeartRate` (bpm)
  - `HKQuantityTypeIdentifierRunningPower` (Watts)
  - `HKQuantityTypeIdentifierRunningVerticalOscillation` (cm)
  - `HKQuantityTypeIdentifierRunningGroundContactTime` (ms)
  - `HKQuantityTypeIdentifierRunningStrideLength` (m)
  - `cum_dist_km`: Cumulative distance in kilometers (derived from GPS).
  - `ele`: Elevation in meters.
  - `pace_smoothed`: Smoothed pace in min/km.

## Graph Significance

- **Distance-Relative Analysis:** Unlike time-based charts, this view highlights how metrics change over the physical distance covered. It is particularly useful for identifying fatigue patterns at specific milestones or analyzing performance on specific segments of a route.
- **Form Correlation:** Enables observation of how running dynamics (VO, GCT, SL) fluctuate with terrain (Elevation) and speed (Pace) across the workout's geography.

## Graph Metrics/Axes

- **X-axis:** **Distance (km)**. The cumulative distance covered from the start of the workout.
- **Y-axes (7 Subplots):**
  1. **Heart Rate (bpm)**
  2. **Pace (min/km)** (Inverted: lower values at the top)
  3. **Vertical Oscillation (cm)**
  4. **Ground Contact Time (ms)**
  5. **Stride Length (m)**
  6. **Power (Watts)**
  7. **Elevation (m)**
- **Other Visuals:**
  - **Unified Hover:** A single vertical spike line and tooltip container that synchronizes across all 7 subplots.
  - **Filtered Averages:** When noise filtering is enabled, the legend displays the recalculated average for each metric excluding the first/last 2 minutes.

## Calculation Logic & Methods

- **Pre-processing:** 
  - **Distance Calculation:** Derived using the **Haversine formula** between sequential GPS coordinates in the GPX file.
  - **Pace Smoothing:** Calculated from time/distance deltas and smoothed using a **10-point rolling average** to filter GPS noise.
  - **Timezone Normalization:** Both XML and GPX timestamps are converted to `UTC` to ensure precise alignment.
  - **Noise Filtering:** Optional toggle to nullify the first **2 minutes** and last **2 minutes** of data to remove warm-up/cool-down artifacts.
- **Merging Logic:** 
  - **Asynchronous Alignment:** XML dynamics (recorded at irregular intervals) are merged onto the GPX timeline using `pd.merge_asof`.
  - **Tolerance:** A **5-second window** is used to match health records with the nearest GPS point.
  - **Interpolation:** GPS-derived metrics (elevation, distance) are linearly interpolated between dynamics data points to maintain a continuous series.
- **Units:**
  - Heart Rate: bpm
  - Pace: min/km
  - Distance: km
  - Power: W
  - Vertical Oscillation: cm
  * Ground Contact Time: ms
  * Stride Length: m
  * Elevation: m
