/*
  mart_high_risk_locations.sql

  One row per suburb + LGA combination.
  Answers: Where in South Australia do the most severe crashes happen?

  Metrics:
    - Total crashes, fatalities, serious injuries per location
    - Fatality rate (fatalities per 100 crashes)
    - Most common crash type per location
    - DUI involvement rate per location
*/

with crash_base as (

    select
        suburb,
        lga_name,
        postcode,
        csef_severity,
        crash_type,
        dui_involved,
        drugs_involved,
        total_fatalities,
        total_serious_injuries,
        total_minor_injuries,
        total_casualties,
        longitude,
        latitude
    from {{ ref('stg_crash') }}
    where suburb is not null
      and lga_name is not null

),

aggregated as (

    select
        suburb,
        lga_name,
        postcode,

        -- Volume
        count(*) as total_crashes,

        -- Outcomes
        sum(total_fatalities) as total_fatalities,
        sum(total_serious_injuries) as total_serious_injuries,
        sum(total_minor_injuries) as total_minor_injuries,
        sum(total_casualties) as total_casualties,

        -- Severity counts
        sum(case when csef_severity = '4: Fatal' then 1 else 0 end) as fatal_crashes,
        sum(case when csef_severity = '3: SI' then 1 else 0 end) as serious_injury_crashes,
        sum(case when csef_severity = '2: MI' then 1 else 0 end) as minor_injury_crashes,
        sum(case when csef_severity = '1: PDO' then 1 else 0 end) as pdo_crashes,

        -- Rates
        round(
            100.0 * sum(total_fatalities) / nullif(count(*), 0),
            3
        ) as fatality_rate_pct,

        round(
            100.0 * sum(case when dui_involved = true then 1 else 0 end)
                / nullif(count(*), 0),
            2
        ) as dui_rate_pct,

        -- Approximate centre point of suburb (average of recorded coords)
        round(avg(longitude), 6) as avg_longitude,
        round(avg(latitude), 6) as avg_latitude

    from crash_base
    group by suburb, lga_name, postcode

)

select
    suburb,
    lga_name,
    postcode,
    total_crashes,
    total_fatalities,
    total_serious_injuries,
    total_minor_injuries,
    total_casualties,
    fatal_crashes,
    serious_injury_crashes,
    minor_injury_crashes,
    pdo_crashes,
    fatality_rate_pct,
    dui_rate_pct,
    avg_longitude,
    avg_latitude
from aggregated
order by total_fatalities desc, total_crashes desc
