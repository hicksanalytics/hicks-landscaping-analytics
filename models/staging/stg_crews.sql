select
    cast(crew_id as integer) as crew_id,
    crew_name,
    home_base,
    supervisor,
    cast(crew_size as integer) as crew_size,
    cast(labor_efficiency_factor as double) as labor_efficiency_factor
from {{ ref('crews') }}
