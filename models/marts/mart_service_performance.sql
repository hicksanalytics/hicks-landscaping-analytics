select
    service_id,
    service_name,
    service_category,
    billing_type,
    count(*) as jobs_completed,
    sum(billed_revenue) as revenue,
    sum(gross_profit) as gross_profit,
    sum(gross_profit) / nullif(sum(billed_revenue), 0) as gross_margin_pct,
    avg(labor_variance_pct) as avg_labor_variance_pct,
    avg(material_variance_pct) as avg_material_variance_pct,
    avg(customer_rating) as avg_customer_rating
from fct_job_profitability
group by 1,2,3,4
order by revenue desc
