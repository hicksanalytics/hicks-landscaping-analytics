"""Export only synthetic aggregate facts and anonymized low-margin job samples."""

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "facts.json"


def build():
    aggregates = defaultdict(lambda: defaultdict(float))
    lows = defaultdict(list)
    with (ROOT / "outputs/job_profitability.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            month = row["completed_date"][:7]
            if not ("2025-01" <= month <= "2026-08"):
                continue
            revenue = float(row["billed_revenue"])
            profit = float(row["gross_profit"])
            for dimension, column in (("crew", "crew_name"), ("service", "service_name"),
                                      ("city", "city"), ("month", None)):
                key = (month, dimension, row[column] if column else month)
                group = aggregates[key]
                group["jobs"] += 1
                for label, source in (("revenue", "billed_revenue"), ("gross_profit", "gross_profit"),
                                      ("labor_cost", "labor_cost"), ("material_cost", "actual_material_cost"),
                                      ("labor_hours", "actual_labor_hours"), ("rework", "rework_flag")):
                    group[label] += float(row[source])
            lows[month].append({
                "job_id": row["job_id"], "month": month, "date": row["completed_date"],
                "crew": row["crew_name"], "service": row["service_name"], "city": row["city"],
                "revenue": round(revenue, 2), "gross_profit": round(profit, 2),
                "gross_margin_pct": round(100 * profit / revenue, 2) if revenue else None,
                "labor_hours": round(float(row["actual_labor_hours"]), 2),
                "rework_flag": int(row["rework_flag"]),
            })
    data = {
        "aggregates": [
            {"month": month, "dimension": dimension, "name": name,
             **{field: round(value, 4) for field, value in values.items()}}
            for (month, dimension, name), values in sorted(aggregates.items())
        ],
        "low_margin_jobs": [item for month in sorted(lows)
                            for item in sorted(lows[month],
                                               key=lambda x: x["gross_margin_pct"] if x["gross_margin_pct"] is not None else 999)[:10]],
        "estimates": [],
    }
    with (ROOT / "outputs/estimate_performance.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            data["estimates"].append({
                "service": row["service_name"], "sent": int(row["estimates_sent"]),
                "won": int(row["estimates_won"]),
                "win_rate_pct": round(100 * float(row["win_rate"]), 2),
                "quoted_value": round(float(row["quoted_value"]), 2),
            })
    OUT.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print(f"Wrote {OUT}: {len(data['aggregates'])} groups, "
          f"{len(data['low_margin_jobs'])} anonymized job samples")


if __name__ == "__main__":
    build()
