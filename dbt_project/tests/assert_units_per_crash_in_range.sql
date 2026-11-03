with counts as (

    select
        (select count(*) from {{ ref('stg_units') }}) as unit_count,
        (select count(*) from {{ ref('stg_crash') }}) as crash_count

)

select
    unit_count,
    crash_count,
    cast(unit_count as double) / nullif(crash_count, 0) as units_per_crash
from counts
where cast(unit_count as double) / nullif(crash_count, 0) not between 1.5 and 3.0
