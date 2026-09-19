from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "hicks_landscaping.duckdb"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

con = duckdb.connect(str(DB))
con.execute("create schema if not exists raw")
con.execute("create schema if not exists analytics")

raw_tables = [
    "customers","services","crews","employees","estimates",
    "jobs","job_labor","invoices","weather_daily"
]

for table in raw_tables:
    path = (RAW / f"{table}.csv").as_posix()
    con.execute(f"""
        create or replace table raw.{table} as
        select * from read_csv_auto('{path}', header=true)
    """)

# Staging views
con.execute("""
create or replace view analytics.stg_customers as
select
    cast(customer_id as integer) customer_id,
    customer_name, customer_type, city, zip_code,
    cast(signup_date as date) signup_date,
    status customer_status, contract_type, acquisition_channel, property_tier
from raw.customers
""")

con.execute("""
create or replace view analytics.stg_services as
select
    cast(service_id as integer) service_id,
    service_name, service_category, billing_type,
    cast(default_price as double) default_price,
    cast(default_est_labor_hours as double) default_est_labor_hours,
    cast(default_material_cost as double) default_material_cost,
    cast(target_margin as double) target_margin
from raw.services
""")

con.execute("""
create or replace view analytics.stg_crews as
select
    cast(crew_id as integer) crew_id,
    crew_name, home_base, supervisor,
    cast(crew_size as integer) crew_size,
    cast(labor_efficiency_factor as double) labor_efficiency_factor
from raw.crews
""")

con.execute("""
create or replace view analytics.stg_estimates as
select
    cast(estimate_id as integer) estimate_id,
    cast(customer_id as integer) customer_id,
    cast(service_id as integer) service_id,
    cast(estimate_date as date) estimate_date,
    cast(quoted_revenue as double) quoted_revenue,
    cast(quoted_labor_hours as double) quoted_labor_hours,
    cast(quoted_material_cost as double) quoted_material_cost,
    estimate_status,
    try_cast(won_date as date) won_date
from raw.estimates
""")

con.execute("""
create or replace view analytics.stg_jobs as
select
    cast(job_id as integer) job_id,
    try_cast(estimate_id as integer) estimate_id,
    cast(customer_id as integer) customer_id,
    cast(service_id as integer) service_id,
    cast(crew_id as integer) crew_id,
    cast(scheduled_date as date) scheduled_date,
    cast(completed_date as date) completed_date,
    job_status, city,
    cast(billed_revenue as double) billed_revenue,
    cast(estimated_labor_hours as double) estimated_labor_hours,
    cast(actual_labor_hours as double) actual_labor_hours,
    cast(estimated_material_cost as double) estimated_material_cost,
    cast(actual_material_cost as double) actual_material_cost,
    cast(rework_flag as integer) rework_flag,
    cast(weather_delay_flag as integer) weather_delay_flag,
    cast(travel_minutes as integer) travel_minutes,
    cast(customer_rating as double) customer_rating
from raw.jobs
""")

con.execute("""
create or replace view analytics.stg_job_labor as
select
    cast(job_id as integer) job_id,
    cast(employee_id as integer) employee_id,
    cast(crew_id as integer) crew_id,
    cast(work_date as date) work_date,
    cast(labor_hours as double) labor_hours,
    cast(labor_cost as double) labor_cost
from raw.job_labor
""")

con.execute("""
create or replace view analytics.int_job_labor_summary as
select job_id, sum(labor_hours) labor_hours_from_detail, sum(labor_cost) labor_cost
from analytics.stg_job_labor
group by 1
""")

con.execute("""
create or replace view analytics.int_job_economics as
select
    j.*,
    coalesce(l.labor_cost,0) labor_cost,
    j.billed_revenue - coalesce(l.labor_cost,0) - j.actual_material_cost gross_profit,
    case when j.billed_revenue=0 then null
         else (j.billed_revenue - coalesce(l.labor_cost,0) - j.actual_material_cost)/j.billed_revenue
    end gross_margin_pct,
    j.actual_labor_hours - j.estimated_labor_hours labor_variance_hours,
    case when j.estimated_labor_hours=0 then null
         else (j.actual_labor_hours-j.estimated_labor_hours)/j.estimated_labor_hours
    end labor_variance_pct,
    j.actual_material_cost-j.estimated_material_cost material_variance,
    case when j.estimated_material_cost=0 then null
         else (j.actual_material_cost-j.estimated_material_cost)/j.estimated_material_cost
    end material_variance_pct
from analytics.stg_jobs j
left join analytics.int_job_labor_summary l using(job_id)
""")

con.execute("""
create or replace table analytics.fct_job_profitability as
select
    e.job_id, e.estimate_id, e.scheduled_date, e.completed_date,
    date_trunc('month', e.completed_date) completed_month,
    c.customer_id, c.customer_name, c.customer_type, c.contract_type,
    c.acquisition_channel, c.property_tier,
    s.service_id, s.service_name, s.service_category, s.billing_type, s.target_margin,
    cr.crew_id, cr.crew_name, cr.home_base crew_home_base,
    e.city, e.billed_revenue, e.labor_cost, e.actual_material_cost,
    e.gross_profit, e.gross_margin_pct,
    e.estimated_labor_hours, e.actual_labor_hours,
    e.labor_variance_hours, e.labor_variance_pct,
    e.estimated_material_cost, e.material_variance, e.material_variance_pct,
    e.rework_flag, e.weather_delay_flag, e.travel_minutes, e.customer_rating
from analytics.int_job_economics e
left join analytics.stg_customers c using(customer_id)
left join analytics.stg_services s using(service_id)
left join analytics.stg_crews cr using(crew_id)
""")

con.execute("""
create or replace table analytics.mart_executive_monthly as
select
    completed_month,
    count(*) jobs_completed,
    count(distinct customer_id) active_customers,
    sum(billed_revenue) revenue,
    sum(labor_cost) labor_cost,
    sum(actual_material_cost) material_cost,
    sum(gross_profit) gross_profit,
    sum(gross_profit)/nullif(sum(billed_revenue),0) gross_margin_pct,
    avg(billed_revenue) avg_job_value,
    sum(billed_revenue)/nullif(sum(actual_labor_hours),0) revenue_per_labor_hour,
    avg(rework_flag) rework_rate,
    avg(weather_delay_flag) weather_delay_rate,
    avg(customer_rating) avg_customer_rating
from analytics.fct_job_profitability
group by 1 order by 1
""")

con.execute("""
create or replace table analytics.mart_crew_performance as
select
    crew_id, crew_name,
    count(*) jobs_completed,
    sum(billed_revenue) revenue,
    sum(gross_profit) gross_profit,
    sum(gross_profit)/nullif(sum(billed_revenue),0) gross_margin_pct,
    sum(actual_labor_hours) actual_labor_hours,
    sum(billed_revenue)/nullif(sum(actual_labor_hours),0) revenue_per_labor_hour,
    avg(labor_variance_pct) avg_labor_variance_pct,
    avg(rework_flag) rework_rate,
    avg(travel_minutes) avg_travel_minutes,
    avg(customer_rating) avg_customer_rating
from analytics.fct_job_profitability
group by 1,2 order by revenue desc
""")

con.execute("""
create or replace table analytics.mart_service_performance as
select
    service_id, service_name, service_category, billing_type,
    count(*) jobs_completed,
    sum(billed_revenue) revenue,
    sum(gross_profit) gross_profit,
    sum(gross_profit)/nullif(sum(billed_revenue),0) gross_margin_pct,
    avg(labor_variance_pct) avg_labor_variance_pct,
    avg(material_variance_pct) avg_material_variance_pct,
    avg(customer_rating) avg_customer_rating
from analytics.fct_job_profitability
group by 1,2,3,4 order by revenue desc
""")

con.execute("""
create or replace table analytics.mart_city_performance as
select
    city,
    count(*) jobs_completed,
    count(distinct customer_id) customers_served,
    sum(billed_revenue) revenue,
    sum(gross_profit) gross_profit,
    sum(gross_profit)/nullif(sum(billed_revenue),0) gross_margin_pct,
    avg(travel_minutes) avg_travel_minutes,
    avg(weather_delay_flag) weather_delay_rate,
    avg(customer_rating) avg_customer_rating
from analytics.fct_job_profitability
group by 1 order by revenue desc
""")

con.execute("""
create or replace table analytics.mart_estimate_performance as
select
    e.service_id, s.service_name,
    count(*) estimates_sent,
    sum(case when e.estimate_status='Won' then 1 else 0 end) estimates_won,
    sum(case when e.estimate_status='Won' then 1 else 0 end)/nullif(count(*),0)::double win_rate,
    sum(e.quoted_revenue) quoted_value,
    avg(e.quoted_revenue) avg_estimate_value
from analytics.stg_estimates e
left join analytics.stg_services s using(service_id)
group by 1,2 order by quoted_value desc
""")

OUT.mkdir(exist_ok=True)

exports = {
    "job_profitability": "analytics.fct_job_profitability",
    "executive_monthly": "analytics.mart_executive_monthly",
    "crew_performance": "analytics.mart_crew_performance",
    "service_performance": "analytics.mart_service_performance",
    "city_performance": "analytics.mart_city_performance",
    "estimate_performance": "analytics.mart_estimate_performance",
}

for name, table in exports.items():
    con.execute(f"COPY {table} TO '{(OUT/f'{name}.csv').as_posix()}' (HEADER, DELIMITER ',')")

# Simple data-quality checks
checks = {
    "job_id_unique": "select count(*) = count(distinct job_id) from analytics.fct_job_profitability",
    "job_id_not_null": "select count(*) = count(job_id) from analytics.fct_job_profitability",
    "revenue_non_negative": "select count(*) = 0 from analytics.fct_job_profitability where billed_revenue < 0",
    "margin_reasonable": "select count(*) = 0 from analytics.fct_job_profitability where gross_margin_pct < -1 or gross_margin_pct > 1",
    "crew_ids_present": "select count(*) = 0 from analytics.fct_job_profitability where crew_id is null",
}
failed = []
for name, sql in checks.items():
    ok = con.execute(sql).fetchone()[0]
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failed.append(name)

if failed:
    raise SystemExit(f"Data quality checks failed: {failed}")

print(f"\nBuilt DuckDB database: {DB}")
print(f"Exports: {OUT}")
