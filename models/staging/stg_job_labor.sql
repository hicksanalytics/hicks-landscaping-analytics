select
    cast(job_id as integer) as job_id,
    cast(employee_id as integer) as employee_id,
    cast(crew_id as integer) as crew_id,
    cast(work_date as date) as work_date,
    cast(labor_hours as double) as labor_hours,
    cast(labor_cost as double) as labor_cost
from {{ ref('job_labor') }}
