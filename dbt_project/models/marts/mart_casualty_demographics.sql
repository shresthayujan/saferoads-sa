/*
  mart_casualty_demographics.sql

  One row per age group + sex + casualty type combination.
  Answers: Who is most at risk on South Australian roads?

  Joins stg_casualty with stg_crash to bring in severity context.
  Derives age bands for grouping.
*/

with casualty_base as (

    select
        c.report_id,
        c.casualty_type,
        c.sex,
        c.age,
        c.injury_extent,
        c.hospitalised,
        c.thrown_out,
        c.seat_belt,
        c.helmet,

        -- Age banding
        case
            when c.age < 18                     then 'Under 18'
            when c.age between 18 and 25        then '18–25'
            when c.age between 26 and 39        then '26–39'
            when c.age between 40 and 59        then '40–59'
            when c.age between 60 and 74        then '60–74'
            when c.age >= 75                    then '75+'
            else 'Unknown'
        end as age_group,

        cr.csef_severity,
        cr.crash_year,
        cr.crash_type

    from {{ ref('stg_casualty') }} c
    left join {{ ref('stg_crash') }} cr
        on c.report_id = cr.report_id

),

aggregated as (

    select
        age_group,
        sex,
        casualty_type,
        injury_extent,
        csef_severity,
        crash_year,

        -- Volume
        count(*) as total_casualties,

        -- Hospitalisation
        sum(case when hospitalised = true then 1 else 0 end) as hospitalised_count,

        round(
            100.0 * sum(case when hospitalised = true then 1 else 0 end)
                / nullif(count(*), 0),
            2
        ) as hospitalisation_rate_pct,

        -- Safety equipment non-use
        sum(case when upper(seat_belt) in ('Not Worn', 'Unknown')
                  then 1 else 0 end) as no_seatbelt_count,

        sum(case when thrown_out = true then 1 else 0 end) as thrown_out_count

    from casualty_base
    where sex is not null
      and casualty_type is not null

    group by
        age_group,
        sex,
        casualty_type,
        injury_extent,
        csef_severity,
        crash_year

)

select
    crash_year,
    age_group,
    sex,
    casualty_type,
    injury_extent,
    csef_severity,
    total_casualties,
    hospitalised_count,
    hospitalisation_rate_pct,
    no_seatbelt_count,
    thrown_out_count
from aggregated
order by crash_year, total_casualties desc