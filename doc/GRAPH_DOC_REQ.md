# Graph Documentation Requirements

Based on `doc/PRD.md`, each analysis or graph in the application must be accompanied by a dedicated documentation file stored in the `graph_doc` directory. This documentation explains the technical and analytical logic to stakeholders.

## Document Structure

Each analysis document should follow this standardized format:

1. **Graph Name:** The title of the analysis (e.g., "Running Form Analysis (Advanced)").
2. **Required Data Files:** List of necessary CSV files (e.g., `RunningVerticalOscillation.csv`, `RunningGroundContactTime.csv`).
3. **Graph Purpose:** 
    - **Objective:** What the graph intends to visualize.
    - **Data Source:** Origin of the data (e.g., XML export, GPX file).
    - **Data Types:** Specific metrics involved (e.g., `RunningVerticalOscillation`, `RunningStrideLength`).
4. **Graph Significance:** Interpretation guide for the visualization (e.g., quadrant analysis, trend meanings).
5. **Graph Metrics/Axes:** 
    - **X-axis:** Metric and baseline.
    - **Y-axis:** Metric and baseline.
    - **Other Visuals:** Meaning of bubble size, colors, etc.
6. **Calculation Logic & Methods:** 
    - **Pre-processing:** Data cleaning or transformation steps.
    - **Merging Logic:** Methods for synchronizing different data streams (e.g., `pd.merge_asof` with specific tolerances).
    - **Formulas:** Specific mathematical equations used for derived metrics.
    - **Units:** Explicit mention of units and any necessary conversions.
