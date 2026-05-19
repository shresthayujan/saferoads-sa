/*
  mart_vehicle_analysis.sql

  One row per vehicle type + vehicle age group combination.
  Answers: Which vehicles are involved most in crashes, and which are most dangerous?

  Joins stg_units with stg_crash to bring in severity context.
  Derives vehicle age bands.
*/

with units_base as (

    select
        u.report_id,
        u.unit_type,
        u.vehicle_year,
        u.driver_age,
        u.driver_sex,
        u.casualties_in_unit,
        u.rolled_over,
        u.caught_fire,
        u.is_towing,
        u.number_occupants,

        -- Vehicle age band (relative to dataset end ~2024)
        case
            when u.vehicle_year is null             then 'Unknown'
            when (2024 - u.vehicle_year) <= 2       then '0–2 years'
            when (2024 - u.vehicle_year) <= 5       then '3–5 years'
            when (2024 - u.vehicle_year) <= 10      then '6–10 years'
            when (2024 - u.vehicle_year) <= 20      then '11–20 years'
            else '20+ years'
        end as vehicle_age_group,

        cr.csef_severity,
        cr.crash_year,
        cr.crash_type,
        cr.dui_involved,
        cr.drugs_involved

    from {{ ref('stg_units') }} u
    left join {{ ref('stg_crash') }} cr
        on u.report_id = cr.report_id

),

aggregated as (

    select
        crash_year,
        unit_type,
        vehicle_age_group,
        csef_severity,

        -- Volume
        count(*) as total_units_involved,

        -- Outcomes
        sum(casualties_in_unit) as total_casualties,

        -- Dangerous events
        sum(case when rolled_over = true then 1 else 0 end) as rollover_count,
        sum(case when caught_fire = true then 1 else 0 end) as fire_count,

        -- Rates
        round(
            100.0 * sum(case when rolled_over = true then 1 else 0 end)
                / nullif(count(*), 0),
            3
        ) as rollover_rate_pct,

        round(
            100.0 * sum(case when caught_fire = true then 1 else 0 end)
                / nullif(count(*), 0),
            3
        ) as fire_rate_pct,

        -- Substance involvement (from crash level)
        sum(case when dui_involved = true then 1 else 0 end) as dui_involved_units,
        sum(case when drugs_involved = true then 1 else 0 end) as drug_involved_units,

        -- Towing
        sum(case when is_towing = true then 1 else 0 end) as towing_count

    from units_base
    where unit_type is not null
      and crash_year is not null

    group by
        crash_year,
        unit_type,
        vehicle_age_group,
        csef_severity

)

select
    crash_year,
    unit_type,
    vehicle_age_group,
    csef_severity,
    total_units_involved,
    total_casualties,
    rollover_count,
    fire_count,
    rollover_rate_pct,
    fire_rate_pct,
    dui_involved_units,
    drug_involved_units,
    towing_count
from aggregated
order by crash_year, total_units_involved desc
