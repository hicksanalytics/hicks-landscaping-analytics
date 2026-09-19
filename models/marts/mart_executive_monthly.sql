select
    completed_month,
    count(*) as jobs_completed,
    count(distinct customer_id) as active_customers,
    sum(billed_revenue) as revenue,
    sum(labor_cost) as labor_cost,
    sum(actual_material_cost) as material_cost,
    sum(gross_profit) as gross_profit,
    sum(gross_profit) / nullif(sum(billed_revenue), 0) as gross_margin_pct,
    avg(billed_revenue) as avg_job_value,
    sum(billed_revenue) / nullif(sum(actual_labor_hours), 0) as revenue_per_labor_hour,
    avg(rework_flag) as rework_rate,
    avg(weather_delay_flag) as weather_delay_rate,
    avg(customer_rating) as avg_customer_rating
from fct_job_profitability
group by 1
order by 1
