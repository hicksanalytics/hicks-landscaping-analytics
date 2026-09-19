select
    e.job_id,
    e.estimate_id,
    e.scheduled_date,
    e.completed_date,
    date_trunc('month', e.completed_date) as completed_month,

    c.customer_id,
    c.customer_name,
    c.customer_type,
    c.contract_type,
    c.acquisition_channel,
    c.property_tier,

    s.service_id,
    s.service_name,
    s.service_category,
    s.billing_type,
    s.target_margin,

    cr.crew_id,
    cr.crew_name,
    cr.home_base as crew_home_base,

    e.city,
    e.billed_revenue,
    e.labor_cost,
    e.actual_material_cost,
    e.gross_profit,
    e.gross_margin_pct,

    e.estimated_labor_hours,
    e.actual_labor_hours,
    e.labor_variance_hours,
    e.labor_variance_pct,

    e.estimated_material_cost,
    e.material_variance,
    e.material_variance_pct,

    e.rework_flag,
    e.weather_delay_flag,
    e.travel_minutes,
    e.customer_rating
from int_job_economics e
left join stg_customers c using (customer_id)
left join stg_services s using (service_id)
left join stg_crews cr using (crew_id)
