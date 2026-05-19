/*
  stg_units.sql
  Staging model for vehicle/unit records.

  One row per vehicle involved in a crash.
  Cleans types, standardises names, normalises flags.
*/

with source as (

    select * from {{ source('raw', 'raw_units') }}

),

cleaned as (

    select
        -- Keys
        cast(report_id as varchar) as report_id,
        cast(unit_no as integer) as unit_number,

        -- Vehicle details
        unit_type,
        try_cast(veh_year as integer) as vehicle_year,
        cast(veh_reg_state as varchar) as vehicle_reg_state,
        cast(postcode as varchar) as driver_postcode,

        -- Driver/rider details
        sex as driver_sex,
        try_cast(age as integer) as driver_age,
        lic_state as licence_state,
        licence_class,
        licence_type,

        -- Movement
        direction_of_travel,
        unit_movement,

        -- Occupants
        cast(number_occupants as integer) as number_occupants,
        cast(no_of_cas as integer) as casualties_in_unit,

        -- Towing
        case
            when upper(towing) = 'Y' then true
            else false
        end as is_towing,

        -- Rollover
        case
            when upper(rollover) = 'Y' then true
            else false
        end as rolled_over,

        -- Fire
        case
            when upper(fire) = 'Y' then true
            else false
        end as caught_fire

    from source
    where report_id is not null

)

select * from cleaned

