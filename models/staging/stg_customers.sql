select
    cast(customer_id as integer) as customer_id,
    customer_name,
    customer_type,
    city,
    zip_code,
    cast(signup_date as date) as signup_date,
    status as customer_status,
    contract_type,
    acquisition_channel,
    property_tier
from {{ ref('customers') }}
