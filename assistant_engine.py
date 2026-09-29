"""Curated function tools for the public-facing landscaping analyst demo."""

import json

import duckdb

DIMENSIONS = {
    "crew": "crew_name",
    "service": "service_name",
    "city": "city",
    "month": "strftime(completed_date, '%Y-%m')",
}

INSTRUCTIONS = """You are the Hicks Analytics landscaping demo analyst. All data is
fictional. Use completed jobs from January 2025 through August 2026; September
2026 has only a partial day of source data and is deliberately excluded.
Use the provided tools for every numerical claim. Be concise, cite the exact
period and grouping, and say when a question cannot be answered by these data.
Gross margin is SUM(gross_profit) / SUM(billed_revenue), not an average of row
margins. Gross profit excludes overhead. Never infer proven causes from a
correlation. For comparisons, request separate periods or group by month.
The available tools provide aggregate job economics, low-margin jobs, and
estimate conversion. Do not ask for or disclose personal customer information.
"""

TOOLS = [
    {
        "type": "function", "name": "analyze_jobs", "strict": True,
        "description": "Aggregate completed jobs by crew, service, city, or month over a date range. Returns weighted gross margin, costs, labor and rework metrics.",
        "parameters": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "enum": list(DIMENSIONS)},
                "start_date": {"type": "string", "description": "Inclusive YYYY-MM-DD; use 2025-01-01 for all data."},
                "end_date": {"type": "string", "description": "Exclusive YYYY-MM-DD; use 2026-09-01 for all data."},
            },
            "required": ["group_by", "start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function", "name": "low_margin_jobs", "strict": True,
        "description": "Find the ten lowest gross-margin completed jobs in a date range, without customer names. Use to inspect outliers after an aggregate finding.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
            },
            "required": ["start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function", "name": "estimate_conversion", "strict": True,
        "description": "Get lifetime estimate sent/won counts, win rate and quoted value by service. These data are not available by date.",
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
]


def _dates(start, end):
    # Preserve a bounded public demo even when a model supplies poor arguments.
    from datetime import date
    try:
        a, b = date.fromisoformat(start), date.fromisoformat(end)
    except (ValueError, TypeError):
        raise ValueError("Dates must use YYYY-MM-DD.")
    if not (date(2025, 1, 1) <= a < b <= date(2026, 9, 1)):
        raise ValueError("Select a range within 2025-01-01 through 2026-08-31.")
    return a, b


def run_tool(name, args, db_path):
    """Accept structured arguments, build our own SQL, and return small JSON results."""
    try:
        if name == "analyze_jobs":
            group = DIMENSIONS.get(args.get("group_by"))
            if not group:
                raise ValueError("Unsupported grouping.")
            start, end = _dates(args.get("start_date"), args.get("end_date"))
            sql = f"""
                SELECT {group} AS group_name, COUNT(*) AS jobs,
                    ROUND(SUM(billed_revenue), 2) AS revenue,
                    ROUND(SUM(gross_profit), 2) AS gross_profit,
                    ROUND(100 * SUM(gross_profit) / NULLIF(SUM(billed_revenue), 0), 2) AS gross_margin_pct,
                    ROUND(SUM(labor_cost), 2) AS labor_cost,
                    ROUND(SUM(actual_material_cost), 2) AS material_cost,
                    ROUND(SUM(actual_labor_hours), 2) AS labor_hours,
                    ROUND(100 * AVG(rework_flag), 2) AS rework_rate_pct
                FROM analytics.fct_job_profitability
                WHERE completed_date >= ? AND completed_date < ?
                GROUP BY 1 ORDER BY 1 LIMIT 30
            """
            params = [start, end]
        elif name == "low_margin_jobs":
            start, end = _dates(args.get("start_date"), args.get("end_date"))
            sql = """
                SELECT job_id, completed_date, crew_name, service_name, city,
                    ROUND(billed_revenue, 2) AS revenue,
                    ROUND(gross_profit, 2) AS gross_profit,
                    ROUND(100 * gross_profit / NULLIF(billed_revenue, 0), 2) AS gross_margin_pct,
                    ROUND(actual_labor_hours, 2) AS labor_hours, rework_flag
                FROM analytics.fct_job_profitability
                WHERE completed_date >= ? AND completed_date < ?
                ORDER BY gross_margin_pct ASC NULLS LAST LIMIT 10
            """
            params = [start, end]
        elif name == "estimate_conversion":
            sql = """
                SELECT service_name, estimates_sent, estimates_won,
                    ROUND(100 * win_rate, 2) AS win_rate_pct,
                    ROUND(quoted_value, 2) AS quoted_value
                FROM analytics.mart_estimate_performance
                ORDER BY estimates_sent DESC LIMIT 20
            """
            params = []
        else:
            raise ValueError("Unknown tool.")
        con = duckdb.connect(str(db_path), read_only=True, config={"enable_external_access": "false"})
        try:
            cursor = con.execute(sql, params)
            columns = [item[0] for item in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return {"rows": rows, "row_count": len(rows)}
        finally:
            con.close()
    except (ValueError, duckdb.Error) as exc:
        return {"error": str(exc)}


def answer(question, db_path, api_key, model="gpt-6-sol", client=None):
    """One question, up to three model calls. Return answer and visible tool trace."""
    if not question.strip() or len(question) > 350:
        raise ValueError("Ask a question of 350 characters or fewer.")
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=25)
    history = [{"role": "user", "content": question}]
    trace = []
    for _ in range(3):
        response = client.responses.create(
            model=model, instructions=INSTRUCTIONS, tools=TOOLS,
            input=history, store=False, max_output_tokens=600,
        )
        history.extend(response.output)
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text or "I couldn't complete that analysis. Try a narrower question.", trace
        for call in calls[:3]:
            try:
                args = json.loads(call.arguments)
                result = run_tool(call.name, args, db_path)
            except (json.JSONDecodeError, TypeError) as exc:
                args, result = {}, {"error": f"Invalid tool arguments: {exc}"}
            trace.append({"tool": call.name, "arguments": args,
                          "result": json.loads(json.dumps(result, default=str))})
            history.append({"type": "function_call_output", "call_id": call.call_id,
                            "output": json.dumps(result, default=str)})
        if len(calls) > 3:
            return "That request required too many data lookups. Please narrow the question.", trace
    return "That request exceeded the demo's analysis limit. Please narrow the question.", trace
