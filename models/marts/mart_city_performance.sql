select
    city,
    count(*) as jobs_completed,
    count(distinct customer_id) as customers_served,
    sum(billed_revenue) as revenue,
    sum(gross_profit) as gross_profit,
    sum(gross_profit) / nullif(sum(billed_revenue), 0) as gross_margin_pct,
    avg(travel_minutes) as avg_travel_minutes,
    avg(weather_delay_flag) as weather_delay_rate,
    avg(customer_rating) as avg_customer_rating
from fct_job_profitability
group by 1
order by revenue desc
