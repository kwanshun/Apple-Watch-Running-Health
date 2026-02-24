# Running Form Analysis (Advanced)

## Required Data Files
- `RunningGroundContactTime.csv`
- `RunningVerticalOscillation.csv`
- `RunningStrideLength.csv`

## Graph Purpose
- **Objective:** To provide a comprehensive visualization of running dynamics across multiple workouts or a specific period, allowing for long-term trend analysis of running form efficiency.
- **Data Source:** Apple Health XML export (extracted as raw `<Record>` tags).
- **Data Types:** 
    - `HKQuantityTypeIdentifierRunningGroundContactTime`
    - `HKQuantityTypeIdentifierRunningVerticalOscillation`
    - `HKQuantityTypeIdentifierRunningStrideLength`

## Graph Significance
The visualization utilizes a quadrant analysis to classify running form based on Ground Contact Time (GCT) and Vertical Oscillation (VO). This classification helps runners understand their mechanical strengths and weaknesses:

- **Elite / Efficient (Bottom-Left):** Low GCT (< 260ms) and Low VO (< 10cm). This quadrant represents high turnover and minimal vertical waste, characteristic of efficient distance running.
- **Power / Bouncy (Top-Left):** Low GCT (< 260ms) and High VO (> 10cm). Indicates a powerful, elastic gait but with potentially excessive vertical movement that could be converted to forward momentum.
- **Glider / Flat (Bottom-Right):** High GCT (> 260ms) and Low VO (< 10cm). Characterized by a "shuffling" gait. While safe and low-impact, it may limit speed due to lack of flight time and power.
- **Heavy / Inefficient (Top-Right):** High GCT (> 260ms) and High VO (> 10cm). Suggests energy is being wasted both on the ground and in vertical height, often seen during fatigue or in beginners.

## Graph Metrics/Axes
- **X-axis:** **Ground Contact Time (ms)**. A baseline reference is set at 260ms to distinguish between "fast" and "slow" foot strikes.
- **Y-axis:** **Vertical Oscillation (cm)**. A baseline reference is set at 10cm to distinguish between "bouncy" and "flat" gaits.
- **Bubble Size:** **Stride Length (m)**. Larger bubbles represent longer strides, allowing users to see how stride length correlates with efficiency.
- **Color:** **Vertical Ratio (%)**. Uses the "Plasma" scale to visualize the percentage of vertical movement relative to stride length. A lower vertical ratio usually indicates better efficiency.

## Calculation Logic & Methods
- **Pre-processing:** 
    - Raw records are filtered by the specific HKQuantity identifiers for VO, GCT, and Stride Length.
    - All metric values are converted to numeric format, with non-numeric entries coerced to NaN.
- **Merging Logic:** 
    - As Apple Watch records these metrics asynchronously, the dataframes are synchronized using `pd.merge_asof` on the `startDate` timestamp.
    - A **2-second tolerance** is applied with `direction='nearest'` to ensure related data points are correctly aligned.
    - Rows with missing values (NaN) after the merge are dropped to maintain chart accuracy.
- **Formulas:**
    - **Vertical Ratio:** `(RunningVerticalOscillation / (RunningStrideLength * 100)) * 100`
    - *Note: `RunningStrideLength` is converted from meters to centimeters to match the units of Vertical Oscillation.*
- **Units:**
    - Ground Contact Time: Milliseconds (ms)
    - Vertical Oscillation: Centimeters (cm)
    - Stride Length: Meters (m)
    - Vertical Ratio: Percentage (%)
