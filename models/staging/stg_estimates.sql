select
    cast(estimate_id as integer) as estimate_id,
    cast(customer_id as integer) as customer_id,
    cast(service_id as integer) as service_id,
    cast(estimate_date as date) as estimate_date,
    cast(quoted_revenue as double) as quoted_revenue,
    cast(quoted_labor_hours as double) as quoted_labor_hours,
    cast(quoted_material_cost as double) as quoted_material_cost,
    estimate_status,
    try_cast(nullif(won_date, '') as date) as won_date
from {{ ref('estimates') }}
