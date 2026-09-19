select
    cast(invoice_id as integer) as invoice_id,
    cast(job_id as integer) as job_id,
    cast(customer_id as integer) as customer_id,
    cast(invoice_date as date) as invoice_date,
    cast(invoice_amount as double) as invoice_amount,
    payment_status,
    try_cast(nullif(days_to_pay, '') as integer) as days_to_pay,
    try_cast(nullif(paid_date, '') as date) as paid_date
from {{ ref('invoices') }}
