select
    e.service_id,
    s.service_name,
    count(*) as estimates_sent,
    sum(case when e.estimate_status = 'Won' then 1 else 0 end) as estimates_won,
    sum(case when e.estimate_status = 'Won' then 1 else 0 end)
      / nullif(count(*), 0)::double as win_rate,
    sum(e.quoted_revenue) as quoted_value,
    avg(e.quoted_revenue) as avg_estimate_value
from stg_estimates e
left join stg_services s using (service_id)
group by 1,2
order by quoted_value desc
