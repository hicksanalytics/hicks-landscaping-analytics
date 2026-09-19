select
    cast(employee_id as integer) as employee_id,
    employee_name,
    cast(crew_id as integer) as crew_id,
    role,
    cast(hourly_rate as double) as hourly_rate,
    cast(hire_date as date) as hire_date
from {{ ref('employees') }}
