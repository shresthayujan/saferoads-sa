select
    report_id,
    unit_number,
    count(*) as row_count
from {{ ref('stg_units') }}
group by
    report_id,
    unit_number
having count(*) > 1
