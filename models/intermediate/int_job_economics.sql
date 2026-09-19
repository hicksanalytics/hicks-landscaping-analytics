with jobs as (
    select * from stg_jobs
),
labor as (
    select * from int_job_labor_summary
)

select
    j.*,
    coalesce(l.labor_cost, 0) as labor_cost,
    j.billed_revenue
      - coalesce(l.labor_cost, 0)
      - j.actual_material_cost as gross_profit,
    case
      when j.billed_revenue = 0 then null
      else (
        j.billed_revenue
        - coalesce(l.labor_cost, 0)
        - j.actual_material_cost
      ) / j.billed_revenue
    end as gross_margin_pct,
    j.actual_labor_hours - j.estimated_labor_hours as labor_variance_hours,
    case
      when j.estimated_labor_hours = 0 then null
      else (j.actual_labor_hours - j.estimated_labor_hours)
           / j.estimated_labor_hours
    end as labor_variance_pct,
    j.actual_material_cost - j.estimated_material_cost as material_variance,
    case
      when j.estimated_material_cost = 0 then null
      else (j.actual_material_cost - j.estimated_material_cost)
           / j.estimated_material_cost
    end as material_variance_pct
from jobs j
left join labor l using (job_id)
