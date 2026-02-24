# Single Workout Deep Dive (Running Form Analysis)

## Required Data Files
- `RunningGroundContactTime.csv`
- `RunningVerticalOscillation.csv`
- `RunningStrideLength.csv`

## Graph Purpose
- **Objective:** To provide a detailed visualization of running form metrics for a specific workout, allowing users to analyze their efficiency and technique within a single session.
- **Data Source:** Apple Health XML export (extracted as raw `<Record>` tags).
- **Data Types:** 
    - `HKQuantityTypeIdentifierRunningGroundContactTime`
    - `HKQuantityTypeIdentifierRunningVerticalOscillation`
    - `HKQuantityTypeIdentifierRunningStrideLength`

## Graph Significance
The visualization uses a quadrant analysis to classify running form based on Ground Contact Time (GCT) and Vertical Oscillation (VO):

- **Elite / Efficient (Bottom-Left):** Low GCT (< 260ms) and Low VO (< 10cm). Indicates rapid turnover and minimal vertical waste.
- **Power / Bouncy (Top-Left):** Low GCT (< 260ms) and High VO (> 10cm). Suggests powerful but potentially vertically excessive movement.
- **Glider / Flat (Bottom-Right):** High GCT (> 260ms) and Low VO (< 10cm). Characterized by a shuffling gait with minimal vertical oscillation.
- **Heavy / Inefficient (Top-Right):** High GCT (> 260ms) and High VO (> 10cm). Often indicates fatigue or suboptimal mechanics where energy is wasted both on the ground and in vertical height.

## Graph Metrics/Axes
- **X-axis:** **Ground Contact Time (ms)**. Baseline reference is set at 260ms.
- **Y-axis:** **Vertical Oscillation (cm)**. Baseline reference is set at 10cm.
- **Bubble Size:** **Stride Length (m)**. Larger bubbles represent longer strides.
- **Color:** **Vertical Ratio (%)**. Uses the "Plasma" scale to visualize the percentage of vertical movement relative to stride length.

## Workout Summary Metrics
The "Single Workout Deep Dive" section displays three key summary metrics for the selected workout:

1.  **Distance (GPS/XML):**
    *   **GPX Source:** If a matching GPX route (starting within 120 seconds of the workout) is found, the distance is calculated using the Haversine formula across GPS coordinates.
    *   **Workout Source:** If no GPX is found, the value is pulled directly from the `totalDistance` attribute of the `<Workout>` tag in the XML export.
    *   **Record Fallback:** If the workout attribute is missing, the distance is calculated by summing raw `DistanceWalkingRunning` records that fall within the workout's time window and share the same data source.
2.  **Pace (GPS/XML):**
    *   **Calculation:** Total Duration (in minutes) divided by the Total Distance (calculated above).
    *   **Formatting:** Displayed in `MM:SS /km` format.
3.  **Dynamics Points:**
    *   **Definition:** The total count of data points where all three core dynamics (VO, GCT, and Stride Length) were successfully aligned within a 2-second window during the workout's duration. This represents the sample size of the bubble chart.

## Calculation Logic & Methods
- **Pre-processing:** 
    - Filter raw records by type for VO, GCT, and Stride Length.
    - Convert values to numeric, coercing errors.
- **Merging Logic:** 
    - Dataframes are synchronized using `pd.merge_asof` on the `startDate` timestamp.
    - A **2-second tolerance** is applied with `direction='nearest'` to align the asynchronously recorded HealthKit metrics.
    - Rows with missing values after the merge are dropped to ensure data integrity for the bubble chart.
- **Formulas:**
    - **Vertical Ratio:** `(RunningVerticalOscillation / (RunningStrideLength * 100)) * 100`
    - Note: `RunningStrideLength` is converted from meters to centimeters for the ratio calculation.
- **Units:**
    - Ground Contact Time: Milliseconds (ms)
    - Vertical Oscillation: Centimeters (cm)
    - Stride Length: Meters (m)
    - Vertical Ratio: Percentage (%)
