# Workout Time-Series Analysis

## Required Data Files

- `HeartRate.csv` (from XML)
- `RunningPower.csv` (from XML)
- `RunningVerticalOscillation.csv` (from XML)
- `RunningGroundContactTime.csv` (from XML)
- `RunningStrideLength.csv` (from XML)
- `route_YYYY-MM-DD_H.MMpm.gpx` (GPX file for GPS data)

## Graph Purpose

- **Objective:** To provide a synchronized, multi-metric timeline of a single workout, enabling runners to see how their heart rate, pace, power, and running form interact over the course of the session.
- **Data Source:** 
  - **XML Records:** Heart Rate, Running Power, Vertical Oscillation, Ground Contact Time, Stride Length.
  - **GPX Files:** Elevation and Pace (GPS-derived).
- **Data Types:** 
  - `HKQuantityTypeIdentifierHeartRate` (bpm)
  - `HKQuantityTypeIdentifierRunningPower` (Watts)
  - `HKQuantityTypeIdentifierRunningVerticalOscillation` (cm)
  - `HKQuantityTypeIdentifierRunningGroundContactTime` (ms)
  - `HKQuantityTypeIdentifierRunningStrideLength` (m)
  - `ele` (Elevation in meters from GPX)
  - `pace_smoothed` (Smoothed Pace in min/km derived from GPX points)

## Graph Significance

- **Unified Insight:** By aligning all metrics on a single time-axis, users can identify correlations such as how fatigue (increasing HR) affects running form (increasing GCT or decreasing SL) or how elevation changes impact power and pace.
- **Interactive Exploration:** A unified tooltip and vertical spike line allow for precise point-in-time analysis across all 7 subplots simultaneously.

## Graph Metrics/Axes

- **X-axis:** **Minutes from Start**. A relative time scale representing the elapsed duration of the workout.
- **Y-axes (7 Subplots):**
  1. **Heart Rate (bpm):** Cardio intensity.
  2. **Pace (min/km):** Running speed (Inverted axis: lower min/km is faster).
  3. **Vertical Oscillation (cm):** Vertical displacement.
  4. **Ground Contact Time (ms):** Time spent on the ground per step.
  5. **Stride Length (m):** Distance covered per step.
  6. **Power (Watts):** Mechanical work output.
  7. **Elevation (m):** Terrain altitude.

## Calculation Logic & Methods

- **Pre-processing:** 
  - **GPX Processing:** Calculates distance between points using the Haversine formula, determines pace from time/distance deltas, and applies a 10-point rolling average to smooth pace data.
  - **Timezone Normalization:** All timestamps (XML and GPX) are forced to UTC-aware `datetime64[ns, UTC]` to ensure compatibility during merging.
- **Merging Logic:** 
  - `**align_workout_data`:** Merges XML-derived metrics onto the GPX timeline using `pd.merge_asof`.
  - **Tolerance:** A **5-second tolerance** is used to synchronize the asynchronous recording of various metrics.
  - **Rounding:** The relative minutes column (`rel_min`) is rounded to **2 decimal places**. This is critical for Plotly's `hovermode="x unified"` to correctly identify matching X-coordinates across all 7 traces.
- **Units:**
  - Heart Rate: Beats per minute (bpm)
  - Pace: Minutes per kilometer (min/km)
  - Power: Watts (W)
  - Vertical Oscillation: Centimeters (cm)
  - Ground Contact Time: Milliseconds (ms)
  - Stride Length: Meters (m)
  - Elevation: Meters (m)

