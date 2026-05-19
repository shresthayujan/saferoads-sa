/*
  mart_crash_severity_trends.sql

  One row per year per severity level.
  Answers: How have crash outcomes changed over time in South Australia?

  Metrics:
    - Total crashes by severity and year
    - Total fatalities, serious injuries, minor injuries
    - DUI-involved crash count
    - Drug-involved crash count
    - Rolling context for trend analysis
*/

with crash_base as (

    select
        crash_year,
        csef_severity,
        dui_involved,
        drugs_involved,
        total_fatalities,
        total_serious_injuries,
        total_minor_injuries,
        total_casualties
    from {{ ref('stg_crash') }}
    where crash_year is not null
      and csef_severity is not null

),

aggregated as (

    select
        crash_year,
        csef_severity,

        -- Volume
        count(*) as total_crashes,

        -- Outcomes
        sum(total_fatalities) as total_fatalities,
        sum(total_serious_injuries) as total_serious_injuries,
        sum(total_minor_injuries) as total_minor_injuries,
        sum(total_casualties) as total_casualties,

        -- Contributing factors
        sum(case when dui_involved = true then 1 else 0 end) as dui_crashes,
        sum(case when drugs_involved = true then 1 else 0 end) as drug_crashes,

        -- Rates (per 100 crashes)
        round(
            100.0 * sum(case when dui_involved = true then 1 else 0 end) / count(*),
            2
        ) as dui_rate_pct,

        round(
            100.0 * sum(case when drugs_involved = true then 1 else 0 end) / count(*),
            2
        ) as drug_rate_pct

    from crash_base
    group by crash_year, csef_severity

)

select
    crash_year,
    csef_severity,
    total_crashes,
    total_fatalities,
    total_serious_injuries,
    total_minor_injuries,
    total_casualties,
    dui_crashes,
    drug_crashes,
    dui_rate_pct,
    drug_rate_pct
from aggregated
order by crash_year, csef_severity