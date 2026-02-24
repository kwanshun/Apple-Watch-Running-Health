## Project Context: Apple Watch Running & Health Trend Analysis

**Description:** A web-based application designed to transform raw Apple HealthKit data (exported XML) into actionable insights and interactive visualizations for runners.

## Tech Stack
- **Language:** Python 3.10+
- **Web Framework:** Streamlit (for rapid data app development)
- **Database/Auth:** Supabase (`supabase-py`)
- **Data Processing:** `pandas` (time-series manipulation), `numpy`
- **XML Parsing:** `lxml`, `xml.etree.ElementTree`
- **Visualization:** `Plotly` (interactive charts), `Altair`
- **Archive Handling:** `zipfile`

## Folder Structure
- `parser/`: Modular logic for unzipping and XML parsing.
- `analytics/`: Implementation of core algorithms (ACWR, EF, TSB, Sleep).
- `ui/`: Streamlit components and dashboard layouts.
- `utils/`: Common helpers (date/unit formatting, `supabase_client.py`).
- `main.py`: Application entry point.

## Core Pipeline (XML to CSV to Dashboard)
1. **Input:** User uploads `export.zip` from iPhone Health app.
2. **Extraction:** Unzip and parse `export.xml` in-memory.
3. **Transformation:** 
 - Parse `<Record>` and `<Workout>` tags.
 - Aggregate raw samples into daily and workout-level summaries.
 - Calculate derivative metrics: ACWR, EF, TSB.
4. **Visualization:** Interactive dashboard with dual-axis charts and date-range filtering.
5. **Storage (Optional):** Opt-in to save summaries to Supabase or local CSV.

## Key Algorithms & Metrics
- **Acute:Chronic Workload Ratio (ACWR):** 7-day vs 28-day rolling workload (Sweet spot: 0.8–1.3).
- **Efficiency Factor (EF):** Output (Pace/Power) / Input (Heart Rate).
- **Training Stress Balance (TSB):** Fitness (CTL) - Fatigue (ATL).
- **Health Markers:** HRV (Heart Rate Variability), RHR (Resting Heart Rate), VO2 Max, Cardio Recovery, Sleep Analysis (Stages & Quality).

## Coding Standards
- **Data Integrity:** Adhere to `.cursor/rules/apple-health-data-standards.mdc` for XML parsing and aggregation.
- **Python:** Use type hints and strict naming conventions.
- **Components:** Modularize logic into appropriate folders.
- **Docstrings:** Follow PEP 257 (Google/NumPy style).
- **Early Returns:** Prefer early returns over nested conditionals.
- **Privacy:** Data is processed locally by default. Persistent storage (Supabase) is strictly opt-in and requires user action.

## Operational Commands
- **Dev Server:** `streamlit run main.py`
- **Dependencies:** `pip install streamlit pandas plotly lxml numpy supabase`
- **Parsing Reference:** Adapt logic from `alxdrcirilo/apple-health-parser`.

## Documentation First
- Refer to `doc/PRD.md` for functional requirements.
- Refer to `doc/ARCHITECTURE.md` for technical specifications and tech stack.
- Update these files or create a task-specific `spec.md` before implementing major features to ground the AI's "vibe."
