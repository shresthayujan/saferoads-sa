# 🛣️ SafeRoads SA — South Australia Road Crash Analytics

An end-to-end Data & Analytics Engineering capstone project built on real South Australian government road-crash data.

## 📌 Project Overview

SafeRoads SA is a portfolio project that demonstrates the full modern data stack — from raw data ingestion through to an interactive analytics dashboard. It covers data engineering fundamentals (scraping, cleaning, warehousing) and analytics engineering best practices (modelling, testing, documentation).

## 🗂️ Project Architecture

```
Raw Data (SA Gov CSVs)
        │
        ▼
┌───────────────────┐
│  Python Scraper   │  ← Playwright + Pandas
│  & Ingestion      │     Downloads, cleans, deduplicates CSVs
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   DuckDB          │  ← Local analytical warehouse
│   Warehouse       │     raw_crash · raw_casualty · raw_units
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   dbt             │  ← Staging + Mart models + data tests
│   Transforms      │     stg_crash · stg_casualty · stg_units
│                   │     5 mart models
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   Marimo          │  ← Interactive analytics dashboard
│   Dashboard       │     KPIs · Charts · Filters
└───────────────────┘
```

## 📊 Mart Models

| Mart | Description |
|------|-------------|
| `mart_crash_severity_trends` | Year-on-year crash severity and DUI/drug trends |
| `mart_high_risk_locations` | Suburb-level crash hotspot ranking |
| `mart_conditions_analysis` | Weather, road surface, and lighting breakdown |
| `mart_casualty_demographics` | Age group, sex, and casualty type analysis |
| `mart_vehicle_analysis` | Vehicle type involvement and rollover/fire rates |

## 🧰 Tech Stack

| Layer | Tool |
|-------|------|
| Scraping & Ingestion | Python · Playwright · Pandas |
| Warehouse | DuckDB |
| Transformation & Testing | dbt-core · dbt-duckdb |
| Analytics & Visualisation | Marimo · Altair |
| Version Control | Git · GitHub |
| Environment | Zorin OS · Python venv |

## 📁 Project Structure

```
saferoads-sa/
├── scraper/          # Playwright-based CSV downloader
├── ingestion/        # Data cleaning & DuckDB loader
├── dbt_project/      # dbt models, tests, and configs
│   ├── models/
│   │   ├── staging/  # Cleaned & typed staging models
│   │   └── marts/    # Analytical mart models
├── notebooks/        # Marimo interactive dashboard
├── warehouse/        # Local DuckDB file
├── config/           # Project configuration files
├── logs/             # Pipeline run logs
└── docs/             # Project documentation
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/shresthayujan/saferoads-sa.git
cd saferoads-sa
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
playwright install firefox
```

### 4. Run the ingestion pipeline

```bash
python ingestion/pipeline.py
```

### 5. Run dbt transformations

```bash
cd dbt_project
dbt run
dbt test
```

### 6. Launch the Marimo dashboard

```bash
marimo run notebooks/sa_road_crashes.py
```

## 📦 Data Source

Road crash data sourced from the [South Australian Government Open Data Portal](https://data.sa.gov.au). Data covers **2012 – 2024** across crash, casualty, and unit records.

## 👤 Author

**Yujan Shrestha**
Data Engineer
[GitHub](https://github.com/shresthayujan)

---
*Built as a capstone portfolio project — 2026*
