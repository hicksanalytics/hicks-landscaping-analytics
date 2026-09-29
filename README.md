# Hicks Analytics | Landscaping Profitability Analytics

A portfolio analytics-engineering project for **Hicks Analytics** using a fictional Middle Tennessee landscaping company.

The goal is to answer the questions a service-business owner actually cares about:

- Which jobs make or lose money?
- Which crews are most efficient?
- Which services have the best margins?
- Where are estimates consistently wrong?
- Which cities create the most revenue and travel burden?
- Which lead sources convert?
- Where are rework and weather delays hurting operations?

## Business scenario

**Volunteer Lawn & Landscape** is a fictional landscaping company serving:

- Nolensville
- Franklin
- Brentwood
- Spring Hill
- Nashville

The source data covers January 2025 through August 2026 and includes customers, estimates, jobs, labor, services, crews, invoices, and synthetic weather.

## Architecture

```text
Raw CSVs
   |
   v
Staging Models
   |
   v
Intermediate Business Logic
   |
   v
Analytics Marts
   |
   +--> BI Dashboard
   |
   +--> AI Business Analyst
```

## Core models

### `fct_job_profitability`
One row per completed job. This is the main fact table for profitability analysis.

### `mart_executive_monthly`
Monthly scorecard for owners and managers.

### `mart_crew_performance`
Crew-level revenue, margin, labor efficiency, rework, travel, and rating metrics.

### `mart_service_performance`
Service-line profitability and estimating accuracy.

### `mart_city_performance`
Revenue, margin, travel, and customer concentration by service area.

### `mart_estimate_performance`
Estimate volume, win rate, quoted value, and average estimate size.

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python scripts/build_duckdb.py
streamlit run app.py
```

This creates:

```text
hicks_landscaping.duckdb
outputs/
  executive_monthly.csv
  crew_performance.csv
  service_performance.csv
  city_performance.csv
  estimate_performance.csv
```

## Dashboard plan

See `docs/dashboard_blueprint.md`.

The Streamlit app opens in **Guided Demo** mode, a five-step owner story that lets a
prospect identify a labor-efficiency problem, investigate the cause, model an
improvement, and review an action plan. **Explore Dashboard** preserves the full
self-service experience and detailed filters.

### Ask the Data · AI analyst

The sidebar's **Ask the Data** experience lets visitors ask questions about the
fictional business. The model chooses from three application-owned tools:
`analyze_jobs`, `low_margin_jobs`, and `estimate_conversion`. The server builds
parameterized DuckDB queries against approved analytics marts and shows each
tool result under **See the data lookups**. Visitors do not supply executable
SQL. Job analysis excludes the incomplete September 2026 data.

Set `OPENAI_API_KEY` in the server environment or Streamlit secrets to enable
the assistant. Optionally set `OPENAI_MODEL` (default `gpt-6-sol`). Never put an
API key in JavaScript, committed secrets, or a static Cloudflare deployment.
The UI allows ten questions per session and three API rounds per question; this
is a demonstration limit, **not** a robust public rate limit. Before enabling
unrestricted public traffic, add an edge/server rate limit and a spending cap.

The current `landscapingdemo.hicksanalytics.com` Cloudflare deployment is a
separate static build. Updating this Streamlit repository does not publish the
assistant there. A Cloudflare deployment needs a server-side Worker/API and a
chat UI wired to that API; this Python module cannot run inside a static page.

Recommended first dashboard pages:

1. Executive Overview
2. Job Profitability
3. Crew Performance
4. Sales & Estimates
5. Customers & Service Area

## Portfolio positioning

This project is not meant to demonstrate "how to make charts."

It demonstrates an end-to-end consulting workflow:

**Business problem → source data → data modeling → KPI definitions → analytical marts → dashboard → recommendations → AI layer**

That is the story Hicks Analytics should sell.

## Next phase

Connect the marts to Power BI, Qlik, or Tableau and build the owner-facing dashboard. Then add an AI analysis layer that can answer business questions using curated analytics tables.


## dbt workflow

For the portfolio-grade dbt path, see `docs/dbt_workflow.md`. The project includes seeds, staging models, intermediate logic, marts, tests, and documentation.
