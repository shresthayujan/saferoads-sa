with crashes as (

    select
        report_id,
        year,
        month,
        day,
        time,
        suburb,
        regexp_extract(report_id, '([^-]+)$', 1) as release
    from {{ source('raw', 'raw_crash') }}

)

select
    year,
    month,
    day,
    time,
    suburb,
    count(distinct release) as release_count
from crashes
group by
    year,
    month,
    day,
    time,
    suburb
having count(distinct release) > 1
