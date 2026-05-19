/*
  mart_conditions_analysis.sql

  One row per combination of road/weather/time conditions.
  Answers: Which environmental conditions produce the worst crash outcomes?

  Dimensions:
    - weather_condition
    - road_surface
    - moisture_condition
    - day_or_night
    - speed_limit (area speed zone)
*/

with crash_base as (

    select
        weather_condition,
        road_surface,
        moisture_condition,
        day_or_night,
        speed_limit,
        csef_severity,
        total_fatalities,
        total_serious_injuries,
        total_minor_injuries,
        total_casualties,
        dui_involved,
        drugs_involved
    from {{ ref('stg_crash') }}
    where weather_condition is not null
      and road_surface is not null

),

aggregated as (

    select
        weather_condition,
        road_surface,
        moisture_condition,
        day_or_night,
        speed_limit,

        -- Volume
        count(*) as total_crashes,

        -- Outcomes
        sum(total_fatalities) as total_fatalities,
        sum(total_serious_injuries) as total_serious_injuries,
        sum(total_minor_injuries) as total_minor_injuries,
        sum(total_casualties) as total_casualties,

        -- Severity breakdown
        sum(case when csef_severity = '4: Fatal' then 1 else 0 end) as fatal_crashes,
        sum(case when csef_severity = '3: SI' then 1 else 0 end) as serious_injury_crashes,

        -- Rates
        round(
            100.0 * sum(total_fatalities) / nullif(count(*), 0),
            3
        ) as fatality_rate_pct,

        round(
            100.0 * sum(total_serious_injuries) / nullif(count(*), 0),
            3
        ) as serious_injury_rate_pct,

        -- Substance involvement
        sum(case when dui_involved = true then 1 else 0 end) as dui_crashes,
        sum(case when drugs_involved = true then 1 else 0 end) as drug_crashes

    from crash_base
    group by
        weather_condition,
        road_surface,
        moisture_condition,
        day_or_night,
        speed_limit

)

select
    weather_condition,
    road_surface,
    moisture_condition,
    day_or_night,
    speed_limit,
    total_crashes,
    total_fatalities,
    total_serious_injuries,
    total_minor_injuries,
    total_casualties,
    fatal_crashes,
    serious_injury_crashes,
    fatality_rate_pct,
    serious_injury_rate_pct,
    dui_crashes,
    drug_crashes
from aggregated
order by total_fatalities desc, total_crashes desc
