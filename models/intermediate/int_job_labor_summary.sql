select
    job_id,
    sum(labor_hours) as labor_hours_from_detail,
    sum(labor_cost) as labor_cost
from stg_job_labor
group by 1
