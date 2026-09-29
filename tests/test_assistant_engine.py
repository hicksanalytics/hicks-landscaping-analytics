import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import duckdb

from assistant_engine import answer, run_tool


class AssistantEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.duckdb"
        con = duckdb.connect(str(self.db))
        con.execute("CREATE SCHEMA analytics")
        con.execute("""CREATE TABLE analytics.fct_job_profitability AS
            SELECT * FROM (VALUES
                (1, DATE '2026-07-01', 'Crew A', 'Mowing', 'Franklin',
                 100.0, 10.0, 10.0, 80.0, 2.0, 0),
                (2, DATE '2026-07-02', 'Crew A', 'Mowing', 'Franklin',
                 900.0, 400.0, 50.0, 450.0, 8.0, 1),
                (3, DATE '2026-07-03', 'Crew B', 'Irrigation', 'Nashville',
                 200.0, 70.0, 30.0, 100.0, 4.0, 0)
            ) AS t(job_id, completed_date, crew_name, service_name, city,
                   billed_revenue, labor_cost, actual_material_cost,
                   gross_profit, actual_labor_hours, rework_flag)""")
        con.execute("""CREATE TABLE analytics.mart_estimate_performance AS
            SELECT 'Mowing' AS service_name, 10 AS estimates_sent,
                   4 AS estimates_won, 0.4 AS win_rate, 1000.0 AS quoted_value""")
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_weighted_margin_and_bounded_dates(self):
        result = run_tool("analyze_jobs", {
            "group_by": "crew", "start_date": "2026-07-01", "end_date": "2026-08-01"
        }, self.db)
        a = next(row for row in result["rows"] if row["group_name"] == "Crew A")
        self.assertEqual(a["gross_margin_pct"], 53.0)  # 530 / 1000, not mean(80%, 50%)
        self.assertIn("error", run_tool("analyze_jobs", {
            "group_by": "crew; DROP TABLE", "start_date": "2026-07-01",
            "end_date": "2026-08-01"
        }, self.db))
        self.assertIn("error", run_tool("low_margin_jobs", {
            "start_date": "2026-09-01", "end_date": "2026-10-01"
        }, self.db))

    def test_tool_call_round_trip(self):
        call = SimpleNamespace(type="function_call", name="analyze_jobs",
            arguments='{"group_by":"crew","start_date":"2026-07-01","end_date":"2026-08-01"}',
            call_id="call_1")
        first = SimpleNamespace(output=[call], output_text="")
        second = SimpleNamespace(output=[], output_text="Crew A margin was 53%.")

        class FakeResponses:
            def __init__(self): self.calls = []
            def create(self, **kwargs):
                self.calls.append(kwargs)
                return [first, second][len(self.calls) - 1]

        fake = SimpleNamespace(responses=FakeResponses())
        message, trace = answer("How did Crew A do in July?", self.db, "unused", client=fake)
        self.assertEqual(message, "Crew A margin was 53%.")
        self.assertEqual(trace[0]["result"]["rows"][0]["gross_margin_pct"], 53.0)
        self.assertEqual(fake.responses.calls[1]["input"][-1]["call_id"], "call_1")
        self.assertEqual(fake.responses.calls[1]["input"][-1]["type"], "function_call_output")


if __name__ == "__main__":
    unittest.main()
