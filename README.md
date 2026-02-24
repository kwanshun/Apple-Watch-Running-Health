---
title: Apple Healthkit Analysier
emoji: 🏃
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.42.0
app_file: main.py
pinned: false
---

# Apple Watch Running & Health Trend Analysis

A Streamlit-based web application designed to transform raw Apple HealthKit export data into actionable performance and health insights for runners. It is built based on https://github.com/alxdrcirilo/apple-health-parser

## Objective
This app implements the technical and design roadmap specified in `Reference-Folder/Apple Watch HealthKit Running & Health Trend Analy.md`. It focuses on visualizing long-term trends by correlating running performance (output) with physiological health markers (input).

## Key Features
- **Advanced Running Dynamics:** Visualization of Running Power, Vertical Oscillation, Ground Contact Time, and Stride Length (native to watchOS 9+).
- **Injury Prevention (ACWR):** Tracking the Acute:Chronic Workload Ratio to manage training load safely.
- **Fitness Progression (EF):** Calculating the Efficiency Factor (Output/HR) to prove aerobic improvements.
- **Readiness Dashboard (TSB & HRV):** Correlating Training Stress Balance with Heart Rate Variability and Resting Heart Rate.
- **Sleep Trends:** Analysis of sleep stages and duration relative to training load.

## Documentation
- [PRD.md](doc/PRD.md): Functional requirements and goals.
- [ARCHITECTURE.md](doc/ARCHITECTURE.md): Technical specifications and system design.
- [AGENTS.md](AGENTS.md): Project context and coding standards.

## Pipeline
1. **Upload:** User provides `export.zip` from the Health app.
2. **Extract:** In-memory parsing of `export.xml` (adapting logic from `alxdrcirilo/apple-health-parser`).
3. **Analyze:** Calculation of ACWR, EF, TSB, and rolling baselines.
4. **Visualize:** Interactive Plotly/Altair dashboards with dual-axis charts and date-range filtering.

## Privacy
**Zero Server-Side Storage.** All data processing occurs locally within the session on the client's machine. Your sensitive HealthKit data is never uploaded to or stored on a server.

## Data Limitations
- **Older Workouts:** For older workouts (typically from earlier iOS/watchOS versions), Apple may only export a single "Workout Summary" record instead of high-frequency time-series data. In such cases, a continuous curve for metrics like Heart Rate may not be visible in the "Metric Timelines" page.
- **數據限制：** 對於較舊的運動記錄（通常來自較早的 iOS/watchOS 版本），Apple 可能僅導出單條「運動摘要」記錄，而非高頻率的序列數據。在這種情況下，「指標分析」頁面中的心率等指標可能無法顯示連續曲線。

## Getting Started
1. Install dependencies: `pip install streamlit pandas plotly lxml`
2. Run the app: `streamlit run main.py`
3. Upload your `export.zip`.
