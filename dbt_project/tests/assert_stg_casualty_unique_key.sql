select
    report_id,
    unit_number,
    casualty_number,
    count(*) as row_count
from {{ ref('stg_casualty') }}
group by
    report_id,
    unit_number,
    casualty_number
having count(*) > 1
