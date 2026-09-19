# dbt Workflow

From the repository root:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

dbt seed --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

The CSV files in `data/raw` are loaded as dbt seeds. Staging models standardize types, intermediate models calculate reusable job economics, and mart models expose business-ready tables.
