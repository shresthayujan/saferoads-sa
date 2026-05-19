/*
  stg_casualty.sql
  Staging model for casualty records.

  One row per person involved in a crash as a casualty.

  Key fix: the raw 'hospital' column contains the hospital NAME (not Y/N).
  We derive two columns from it:
    - hospitalised   → boolean (true if any hospital name was recorded)
    - hospital_name  → varchar (the actual hospital name, NULL if not hospitalised)
  'XXXXXX' means the name was redacted by SA Gov — treated as hospitalised=true.
*/

with source as (

    select * from {{ source('raw', 'raw_casualty') }}

),

cleaned as (

    select
        -- Keys
        cast(report_id as varchar) as report_id,
        cast(und_unit_number as integer) as unit_number,
        cast(casualty_number as integer) as casualty_number,

        -- Person details
        casualty_type,
        sex,
        try_cast(age as integer) as age,

        -- Injury information
        injury_extent,
        position_in_veh as position_in_vehicle,

        -- Safety equipment
        seat_belt,
        helmet,

        -- Thrown from vehicle (presence-only flag)
        case
            when upper(thrown_out) = 'Y' then true
            else false
        end as thrown_out,

        -- Hospitalised: derived from whether a hospital name was recorded
        case
            when hospital is not null
             and trim(hospital) != '' then true
            else false
        end as hospitalised,

        -- Hospital name: raw value, NULL if not hospitalised
        -- 'XXXXXX' = redacted by SA Government (still hospitalised)
        case
            when hospital is not null
             and trim(hospital) != '' then trim(hospital)
            else null
        end as hospital_name

    from source
    where report_id is not null

)

select * from cleaned