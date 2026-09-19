select
    crew_id,
    crew_name,
    count(*) as jobs_completed,
    sum(billed_revenue) as revenue,
    sum(gross_profit) as gross_profit,
    sum(gross_profit) / nullif(sum(billed_revenue), 0) as gross_margin_pct,
    sum(actual_labor_hours) as actual_labor_hours,
    sum(billed_revenue) / nullif(sum(actual_labor_hours), 0) as revenue_per_labor_hour,
    avg(labor_variance_pct) as avg_labor_variance_pct,
    avg(rework_flag) as rework_rate,
    avg(travel_minutes) as avg_travel_minutes,
    avg(customer_rating) as avg_customer_rating
from fct_job_profitability
group by 1,2
order by revenue desc
