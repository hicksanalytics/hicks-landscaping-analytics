select
    cast(service_id as integer) as service_id,
    service_name,
    service_category,
    billing_type,
    cast(default_price as double) as default_price,
    cast(default_est_labor_hours as double) as default_est_labor_hours,
    cast(default_material_cost as double) as default_material_cost,
    cast(target_margin as double) as target_margin
from {{ ref('services') }}
