/*
  stg_crash.sql
  Staging model for raw crash events.

  Cleans and type-casts the raw_crash table:
  - Standardises column names (snake_case, descriptive)
  - Casts types explicitly (integers, floats, timestamps)
  - Normalises Y/N flags to boolean
  - Filters out any rows missing a report_id (shouldn't exist, but defensive)
*/

with source as (

    select * from {{ source('raw', 'raw_crash') }}

),

cleaned as (

    select
        -- Primary key
        cast(report_id as varchar) as report_id,

        -- Location fields
        stats_area,
        suburb,
        cast(postcode as varchar) as postcode,
        lga_name,
        cast(accloc_x as double) as longitude,
        cast(accloc_y as double) as latitude,
        position_type,
        unique_loc,

        -- Date and time
        cast(year as integer) as crash_year,
        cast(month as integer) as crash_month,
        cast(day as integer) as crash_day,
        time as crash_time,
        crash_date_time,

        -- Crash classification
        csef_severity,
        crash_type,
        daynight as day_or_night,
        unit_resp as responsible_unit,

        -- Road and environment conditions
        area_speed as speed_limit,
        road_surface,
        moisture_cond as moisture_condition,
        weather_cond as weather_condition,
        horizontal_align,
        vertical_align,
        other_feat as other_feature,
        traffic_ctrls as traffic_controls,

                -- Contributing factors (presence-only flags: Y = true, NULL = false)
        case
            when upper(dui_involved) = 'Y' then true
            else false
        end as dui_involved,

        case
            when upper(drugs_involved) = 'Y' then true
            else false
        end as drugs_involved,

        -- Counts
        cast(total_units as integer) as total_units,
        cast(total_cas as integer) as total_casualties,
        cast(total_fats as integer) as total_fatalities,
        cast(total_si as integer) as total_serious_injuries,
        cast(total_mi as integer) as total_minor_injuries,

        entity_code

    from source
    where report_id is not null

)

select * from cleaned
