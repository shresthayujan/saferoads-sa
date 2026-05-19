import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import duckdb
    import pandas as pd
    import altair as alt

    # ── Connection ──────────────────────────────────────────────────────────────
    DB_PATH = "warehouse/saferoads.duckdb"
    con = duckdb.connect(DB_PATH, read_only=True)

    # ── Load mart tables ─────────────────────────────────────────────────────────
    df_severity   = con.execute("SELECT * FROM main_marts.mart_crash_severity_trends").df()
    df_locations  = con.execute("SELECT * FROM main_marts.mart_high_risk_locations").df()
    df_conditions = con.execute("SELECT * FROM main_marts.mart_conditions_analysis").df()
    df_casualty   = con.execute("SELECT * FROM main_marts.mart_casualty_demographics").df()
    df_vehicle    = con.execute("SELECT * FROM main_marts.mart_vehicle_analysis").df()

    con.close()
    return (
        alt,
        df_casualty,
        df_conditions,
        df_locations,
        df_severity,
        df_vehicle,
        mo,
    )


@app.cell
def _(df_severity, mo):
    # ── KPI Summary Row ──────────────────────────────────────────────────────────
    total_crashes    = int(df_severity["total_crashes"].sum())
    total_fatalities = int(df_severity["total_fatalities"].sum())
    total_si         = int(df_severity["total_serious_injuries"].sum())
    total_casualties = int(df_severity["total_casualties"].sum())
    year_min         = int(df_severity["crash_year"].min())
    year_max         = int(df_severity["crash_year"].max())

    mo.hstack([
        mo.stat(
            label="📅 Data Period",
            value=f"{year_min} – {year_max}",
        ),
        mo.stat(
            label="💥 Total Crashes",
            value=f"{total_crashes:,}",
        ),
        mo.stat(
            label="💀 Total Fatalities",
            value=f"{total_fatalities:,}",
        ),
        mo.stat(
            label="🏥 Serious Injuries",
            value=f"{total_si:,}",
        ),
        mo.stat(
            label="🚑 Total Casualties",
            value=f"{total_casualties:,}",
        ),
    ], justify="space-around")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 📈 Crash Severity Trends
    How crash outcomes — fatalities, serious injuries, and minor injuries — have changed across South Australia over the selected period.
    """)
    return


@app.cell
def _(df_severity, mo):
    # ── Global Year Range Filter ─────────────────────────────────────────────────
    years = sorted(df_severity["crash_year"].dropna().astype(int).unique().tolist())

    year_range = mo.ui.range_slider(
        start=min(years),
        stop=max(years),
        value=[min(years), max(years)],
        step=1,
        label="📅 Year Range",
        debounce=True
    )

    year_range
    return (year_range,)


@app.cell
def _(mo, year_range):
    # ── Year Range Label ─────────────────────────────────────────────────────────
    mo.md(f"**📅 Selected: {year_range.value[0]} – {year_range.value[1]}**")

    return


@app.cell
def _(alt, df_severity, mo, year_range):
    # ── Crash Severity Trends ────────────────────────────────────────────────────
    severity_data = df_severity[
        (df_severity["crash_year"] >= year_range.value[0]) &
        (df_severity["crash_year"] <= year_range.value[1])
    ]

    severity_melted = severity_data.groupby("crash_year")[
        ["total_fatalities", "total_serious_injuries", "total_minor_injuries"]
    ].sum().reset_index().melt(
        id_vars=["crash_year"],
        var_name="severity_type",
        value_name="count"
    )

    chart_severity = alt.Chart(severity_melted).mark_line(point=True).encode(
        x=alt.X("crash_year:O", title="Year"),
        y=alt.Y("count:Q", title="Count"),
        color=alt.Color("severity_type:N", title="Severity Type"),
        tooltip=["crash_year:O", "severity_type:N", "count:Q"]
    ).properties(
        title="Crash Severity Trends Over Time",
        width=650,
        height=350
    )

    mo.ui.altair_chart(chart_severity)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 📍 High Risk Locations
    The top 20 suburbs ranked by total crash volume. Use this to identify geographic hotspots across South Australia.
    """)
    return


@app.cell
def _(df_locations, mo):
    # ── High Risk Locations ──────────────────────────────────────────────────────
    # Note: mart_high_risk_locations has no crash_year column, showing all-time top 20
    locations_data = df_locations.sort_values("total_crashes", ascending=False).head(20)

    mo.ui.table(
        locations_data,
        label="📍 Top 20 High Risk Locations"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 🌦️ Crash Conditions Analysis
    Breakdown of crashes by weather, road surface, moisture, and lighting conditions. Covers the full dataset period.
    """)
    return


@app.cell
def _(alt, df_conditions, mo):
    # ── Conditions Analysis ──────────────────────────────────────────────────────
    conditions_data = df_conditions.groupby("weather_condition")[
        ["total_crashes", "total_fatalities", "total_serious_injuries"]
    ].sum().reset_index().sort_values("total_crashes", ascending=False).head(10)

    chart_conditions = alt.Chart(conditions_data).mark_bar().encode(
        x=alt.X("total_crashes:Q", title="Total Crashes"),
        y=alt.Y("weather_condition:N", title="Weather Condition", sort="-x"),
        color=alt.Color("total_fatalities:Q", title="Total Fatalities",
                        scale=alt.Scale(scheme="orangered")),
        tooltip=[
            alt.Tooltip("weather_condition:N", title="Weather"),
            alt.Tooltip("total_crashes:Q", title="Total Crashes"),
            alt.Tooltip("total_fatalities:Q", title="Fatalities"),
            alt.Tooltip("total_serious_injuries:Q", title="Serious Injuries")
        ]
    ).properties(
        title="Crashes by Weather Condition (Top 10)",
        width=650,
        height=350
    )

    mo.ui.altair_chart(chart_conditions)

    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 👤 Casualty Demographics
    Casualties grouped by age and type (Driver, Passenger, Rider, Pedestrian) across the selected year range.
    """)
    return


@app.cell
def _(alt, df_casualty, mo, year_range):
    # ── Casualty Demographics ────────────────────────────────────────────────────
    casualty_data = df_casualty[
        (df_casualty["crash_year"] >= year_range.value[0]) &
        (df_casualty["crash_year"] <= year_range.value[1])
    ].groupby(["age_group", "casualty_type"])["total_casualties"].sum().reset_index()

    chart_casualty = alt.Chart(casualty_data).mark_bar().encode(
        x=alt.X("age_group:N", title="Age Group"),
        y=alt.Y("total_casualties:Q", title="Total Casualties"),
        color=alt.Color("casualty_type:N", title="Casualty Type"),
        tooltip=[
            alt.Tooltip("age_group:N", title="Age Group"),
            alt.Tooltip("casualty_type:N", title="Type"),
            alt.Tooltip("total_casualties:Q", title="Casualties")
        ]
    ).properties(
        title="Casualties by Age Group and Type",
        width=650,
        height=350
    )

    mo.ui.altair_chart(chart_casualty)

    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 🚗 Vehicle Analysis
    Top 10 vehicle types by involvement, coloured by total casualties. Filtered by the selected year range.
    """)
    return


@app.cell
def _(alt, df_vehicle, mo, year_range):
    # ── Vehicle Analysis ─────────────────────────────────────────────────────────
    vehicle_data = df_vehicle[
        (df_vehicle["crash_year"] >= year_range.value[0]) &
        (df_vehicle["crash_year"] <= year_range.value[1])
    ].groupby("unit_type")[
        ["total_units_involved", "total_casualties", "rollover_count", "fire_count"]
    ].sum().reset_index().sort_values("total_units_involved", ascending=False).head(10)

    chart_vehicle = alt.Chart(vehicle_data).mark_bar().encode(
        x=alt.X("total_units_involved:Q", title="Total Units Involved"),
        y=alt.Y("unit_type:N", title="Vehicle Type", sort="-x"),
        color=alt.Color("total_casualties:Q", title="Total Casualties",
                        scale=alt.Scale(scheme="blues")),
        tooltip=[
            alt.Tooltip("unit_type:N", title="Vehicle Type"),
            alt.Tooltip("total_units_involved:Q", title="Units Involved"),
            alt.Tooltip("total_casualties:Q", title="Casualties"),
            alt.Tooltip("rollover_count:Q", title="Rollovers"),
            alt.Tooltip("fire_count:Q", title="Fires")
        ]
    ).properties(
        title="Top 10 Vehicle Types by Involvement",
        width=650,
        height=350
    )

    mo.ui.altair_chart(chart_vehicle)
    return


@app.cell
def _(mo):
    # ── Footer ───────────────────────────────────────────────────────────────────
    mo.md("""
    ---
    <div style="text-align: center; color: grey; font-size: 0.85em; padding: 1rem 0;">

    📊 **SafeRoads SA** — South Australia Road Crash Analytics Dashboard

    Data sourced from the [South Australian Government Open Data Portal](https://data.sa.gov.au)

    Built with 🦆 DuckDB · 🔧 dbt · 🌊 Marimo · 🐍 Python

    [GitHub Repository](https://github.com/shresthayujan/saferoads-sa)

    </div>
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()