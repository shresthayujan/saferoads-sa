with staging_count as (

    select count(*) as row_count
    from {{ ref('stg_casualty') }}

),

raw_count as (

    select count(*) as row_count
    from {{ source('raw', 'raw_casualty') }}

)

select
    staging_count.row_count as staging_row_count,
    raw_count.row_count as raw_row_count
from staging_count
cross join raw_count
where staging_count.row_count != raw_count.row_count
