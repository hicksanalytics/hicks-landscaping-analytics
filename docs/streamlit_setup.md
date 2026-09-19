# Add Streamlit to the Hicks Landscaping Analytics repo

Copy these files into the root of your existing `hicks-landscaping-analytics` repository:

- `app.py`
- `requirements.txt` (replace the existing file)
- `.streamlit/config.toml`

Your repository should then look like:

```text
hicks-landscaping-analytics/
├── app.py
├── hicks_landscaping.duckdb
├── requirements.txt
├── scripts/
├── models/
├── data/
├── outputs/
└── .streamlit/
    └── config.toml
```

## Install the new dependencies on Windows

You do not need to activate the virtual environment. From PowerShell in the repo folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Rebuild the analytics database

```powershell
.\.venv\Scripts\python.exe scripts\build_duckdb.py
```

## Launch the app

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit should open the app in your browser. The local URL is normally:

```text
http://localhost:8501
```

## Commit the app

After confirming it works:

```powershell
git status
git add .
git commit -m "Add Streamlit landscaping analytics app"
git push
```

## Current pages

1. Executive Overview
2. Job Profitability
3. Crew Performance
4. Sales & Estimates

The next planned phase is an AI Business Analyst experience on top of the curated analytics data.
