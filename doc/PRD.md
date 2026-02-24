# Product Requirements Document (PRD): Apple Watch Running & Health Trend Analysis

## 1. Project Overview
The **Apple Watch Running & Health Trend Analysis** app is a web-based application designed to implement the "Comprehensive Technical and Design Roadmap" for transforming raw Apple HealthKit data into actionable running and health insights. 

### 1.1 Goal
**XML (Zip) → CSV → Advanced Analytics & Interactive Dashboard**
Implement a specialized reporting tool based on the specifications in `Reference-Folder/Apple Watch HealthKit Running & Health Trend Analy.md`.

## 2. User Interface & Experience

### 2.1 Data Input
- **File Uploader:** Drag and drop `export.zip` directly from iPhone.
- **Background Processing:** In-memory unzipping and parsing of `export.xml`.

### 2.2 Date Range Selection (Date Zones)
Filter all metrics and charts by:
- Last Week, Last Month, Last 3 Months, Last Year, All Data.

## 3. Core Metrics & Algorithms

### 3.1 Running Performance (Output)
- **Advanced Dynamics (watchOS 9+):** Running Power (Watts), Vertical Oscillation (cm), Ground Contact Time (ms), Stride Length (m).
- **Standard Metrics:** Distance, Pace, Cadence, Heart Rate.

### 3.2 Health & Recovery (Input)
- **Recovery Markers:** Heart Rate Variability (HRV - SDNN), Resting Heart Rate (RHR).
- **Fitness Indicators:** VO2 Max, Cardio Recovery (1-minute heart rate drop).

### 3.3 Sleep Analysis
- **Sleep Metrics:** Total Sleep Duration, Deep Sleep, REM Sleep, Core/Light Sleep.
- **Sleep Quality:** Consistency and efficiency (time in bed vs. time asleep).

### 3.4 Key Algorithms
- **Acute:Chronic Workload Ratio (ACWR):** 7-day vs 28-day rolling workload for injury prevention (Target: 0.8–1.3).
- **Efficiency Factor (EF):** Output (Pace/Power) vs. Input (Heart Rate) to track aerobic fitness gains.
- **Training Stress Balance (TSB):** Fitness (CTL) minus Fatigue (ATL) to determine "Readiness" or "Form."

### 3.5 Export & Storage
- **Dashboard Export:** Allow users to export charts and summary reports as PDF or Image files.
- **Data Export:** Option to export processed analytics as CSV.
- **Database Integration:** Opt-in feature to save processed health trends to a secure **Supabase** database for historical tracking.

## 4. Privacy & Data Security
- **Local-by-Default Processing:** All HealthKit data is processed in-memory or within the user's local session.
- **Opt-in Persistence:** Data is only saved to a server (Supabase) if the user explicitly chooses to "Save to Cloud" and authenticates.
- **No Automatic Storage:** Zero health data, raw or processed, is stored on a permanent server by default.
- **No External Data Transmission:** The app must not send any HealthKit data to third-party APIs except for the user-selected storage (local or Supabase).
- **Ephemeral Sessions:** Unsaved local data is cleared automatically when the user closes the browser tab or the session expires.

## 5. Visualization Requirements

### 5.1 Performance vs. Cost Chart (Decoupling)
- **Dual-Axis Line Chart:** Pace/Power on one axis, Heart Rate on the other to visualize cardiac drift and efficiency trends.

### 5.2 Load Management Gauge
- **ACWR Visualization:** Gauge or bar chart with color-coded safety zones (Green: 0.8-1.3, Red: >1.5).

### 5.3 Health Readiness Dashboard
- **Deviation Analysis:** Bar chart showing today's HRV and RHR relative to their 30-day moving average baselines.

### 5.4 Smoothed Trend Lines
- **Data Context:** Bold rolling average lines (7-day/30-day) overlaid on faint raw data points to highlight the "forest for the trees."

## 6. Success Criteria
1. Accurate extraction of watchOS 9 advanced running dynamics.
2. Functional dashboard for ACWR, Efficiency Factor, and Health Readiness.
3. Responsive date-zone filtering across all visualization components.

## 7. Documentation for Analysis
Each analysis/graph in the application must be accompanied by a dedicated documentation file stored in the `graph_doc` directory.

Detailed specifications for these documents can be found in [GRAPH_DOC_REQ.md](GRAPH_DOC_REQ.md).
