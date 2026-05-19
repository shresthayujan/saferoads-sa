"""
ingestion/scraper.py
====================
Phase 1 - SafeRoads SA ingestion pipeline.

What this script does:
  1. Scrapes data.sa.gov.au and downloads all road crash CSVs
  2. Detects overlapping year files and picks the best (widest) ones
  3. Merges, deduplicates and cleans into 3 master tables
  4. Loads those tables into DuckDB as raw source tables

Future-proof design:
  - Year ranges are parsed dynamically from filenames
  - When SA Gov publishes 2025 or 2026 data, this script
    will automatically detect and prefer the wider file.
    No manual changes needed.
"""

import os
import re
import glob
import logging
import zipfile

import duckdb
import pandas as pd
from playwright.sync_api import sync_playwright

# ============================================================
# CONFIG
# ============================================================

# Paths — relative to project root
RAW_DATA_PATH  = os.path.join("data", "raw")
WAREHOUSE_PATH = os.path.join("warehouse", "saferoads.duckdb")
LOG_PATH       = os.path.join("logs", "ingestion.log")

# The 3 table types we expect from SA Gov
TABLE_TYPES = ["Crash", "Casualty", "Units"]

# SA Gov dataset page
SA_GOV_URL    = "https://data.sa.gov.au"
DATASET_NAME  = "Road Crash Data"

# ============================================================
# LOGGING SETUP
# ============================================================

os.makedirs(RAW_DATA_PATH, exist_ok=True)
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ============================================================
# DOWNLOAD FILES
# ============================================================

def download_files():
    """
    Uses Playwright to scrape data.sa.gov.au and download
    all road crash resource files into data/raw/.
    Skips files that have already been downloaded.
    """
    log.info("=" * 55)
    log.info("STAGE 1 — DOWNLOADING FILES")
    log.info("=" * 55)

    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=True)
        page    = browser.new_page()

        log.info(f"Navigating to {SA_GOV_URL} ...")
        page.goto(SA_GOV_URL)

        # Search for the dataset
        page.wait_for_selector("#edit-keys")
        page.locator("#edit-keys").fill("road crash data")
        page.locator("#edit-keys").press("Enter")
        page.wait_for_load_state("networkidle")

        # Click the dataset link
        page.get_by_role("link", name=DATASET_NAME, exact=True).first.click()
        page.wait_for_selector(".resource-list", timeout=10000)

        download_links = page.locator("a.resource-url-analytics")
        count = download_links.count()
        log.info(f"Found {count} resources on the page.")

        for i in range(count):
            url = download_links.nth(i).get_attribute("href")

            if not url:
                continue

            filename = url.split("/")[-1]

            # Skip non-CSV and non-ZIP files (e.g. PDFs, metadata)
            if not filename.endswith((".csv", ".zip")):
                log.info(f"[{i+1}/{count}] Skipping non-data file: {filename}")
                continue

            save_path = os.path.join(RAW_DATA_PATH, filename)

            # Skip if already downloaded
            if os.path.exists(save_path):
                log.info(f"[{i+1}/{count}] Already exists, skipping: {filename}")
                continue

            log.info(f"[{i+1}/{count}] Downloading: {filename}")
            try:
                with page.expect_download(timeout=60000) as dl_info:
                    page.evaluate(f"window.location.href = '{url}'")

                download = dl_info.value
                download.save_as(save_path)
                log.info(f"  Saved: {filename}")

                # Unzip if needed
                if save_path.endswith(".zip"):
                    log.info(f"  Unzipping: {filename}")
                    with zipfile.ZipFile(save_path, "r") as zf:
                        zf.extractall(RAW_DATA_PATH)
                    os.remove(save_path)
                    log.info(f"  Unzipped and removed zip.")

            except Exception as e:
                log.error(f"  Failed to download {filename}: {e}")

        browser.close()
    log.info("Downloading files complete.\n")


# ============================================================
# OVERLAP DETECTION (FUTURE-PROOFING)
# ============================================================

def parse_year_range(filename: str):
    """
    Given a filename like:
      2019-2023_DATA_SA_Crash.csv  → returns (2019, 2023)
      2012_DATA_SA_Crash.csv       → returns (2012, 2012)
      unexpected_name.csv          → returns None

    This works for ANY year range SA Gov might publish in future,
    e.g. 2019-2025, 2019-2026, 2025, 2026 — all handled automatically.
    """
    basename = os.path.basename(filename)

    # Multi-year pattern e.g. 2019-2023
    multi = re.match(r"^(20\d{2})-(20\d{2})_", basename)
    if multi:
        return (int(multi.group(1)), int(multi.group(2)))

    # Single-year pattern e.g. 2012
    single = re.match(r"^(20\d{2})_", basename)
    if single:
        yr = int(single.group(1))
        return (yr, yr)

    return None


def select_best_files():
    """
    For each table type (Crash, Casualty, Units):
      - Finds all matching CSV files in data/raw/
      - Detects which years are covered by multi-year files
      - Drops single-year files whose year is already covered
      - If multiple multi-year files overlap, keeps the WIDEST one
        (this handles future releases like 2019-2025 replacing 2019-2023)

    Returns a dict: { "Crash": [list of paths], "Casualty": [...], ... }
    """
    log.info("=" * 55)
    log.info("STAGE 2 — OVERLAP DETECTION")
    log.info("=" * 55)

    files_to_use = {}

    for table_type in TABLE_TYPES:
        all_files = glob.glob(
            os.path.join(RAW_DATA_PATH, f"*_DATA_SA_{table_type}.csv")
        )

        if not all_files:
            log.warning(f"No files found for table type: {table_type}")
            files_to_use[table_type] = []
            continue

        # Parse year ranges for every file
        parsed = []
        for f in all_files:
            yr = parse_year_range(f)
            if yr:
                parsed.append((f, yr[0], yr[1]))
            else:
                log.warning(f"  Could not parse year from: {os.path.basename(f)}")

        # Sort by range width descending (widest first), then by start year
        parsed.sort(key=lambda x: (-(x[2] - x[1]), x[1]))

        # Skip any file whose years are fully covered
        covered_years = set()
        selected = []

        for filepath, start, end in parsed:
            file_years = set(range(start, end + 1))

            if file_years.issubset(covered_years):
                log.info(
                    f"  SKIP (fully covered): {os.path.basename(filepath)}"
                )
                continue

            selected.append(filepath)
            covered_years.update(file_years)
            log.info(
                f"  USE: {os.path.basename(filepath)} "
                f"(years {start}–{end})"
            )

        files_to_use[table_type] = selected
        log.info(f"  → {len(selected)} file(s) selected for {table_type}\n")

    log.info("Stage 2 complete.\n")
    return files_to_use


# ============================================================
# MERGE, DEDUPLICATE AND CLEAN
# ============================================================

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies consistent cleaning rules to any table:
      - Strips and lowercases column names
      - Replaces spaces with underscores
      - Removes special characters from column names
      - Drops completely empty rows
    """
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    df.dropna(how="all", inplace=True)
    return df


def merge_and_clean(files_to_use: dict) -> dict:
    """
    For each table type:
      - Reads and concatenates all selected CSVs
      - Deduplicates on report_id (and unit/casualty number where relevant)
      - Cleans column names
      - Returns a dict of cleaned DataFrames
    """
    log.info("=" * 55)
    log.info("STAGE 3 — MERGE, DEDUPLICATE AND CLEAN")
    log.info("=" * 55)

    # Deduplicate keys per table
    dedup_keys = {
        "Crash"    : ["report_id"],
        "Casualty" : ["report_id", "casualty_number"],
        "Units"    : ["report_id", "und_unit_number"],
    }

    master = {}

    for table_type in TABLE_TYPES:
        files = files_to_use.get(table_type, [])

        if not files:
            log.warning(f"No files to process for {table_type}. Skipping.")
            continue

        dfs = []
        for f in files:
            log.info(f"  Reading: {os.path.basename(f)}")
            df = pd.read_csv(f, low_memory=False)
            dfs.append(df)

        combined = pd.concat(dfs, ignore_index=True)
        rows_before = len(combined)

        combined = clean_dataframe(combined)

        # Deduplicate using the most specific key available
        keys = dedup_keys.get(table_type, ["report_id"])
        available_keys = [k for k in keys if k in combined.columns]

        if available_keys:
            combined.drop_duplicates(subset=available_keys, inplace=True)
        else:
            combined.drop_duplicates(inplace=True)

        rows_after = len(combined)

        log.info(f"  {table_type}: {rows_before} rows → {rows_after} rows "
                 f"({rows_before - rows_after} duplicates removed)")

        master[table_type] = combined

    log.info("Stage 3 complete.\n")
    return master


# ============================================================
# LOAD INTO DUCKDB
# ============================================================

def load_to_duckdb(master: dict):
    """
    Loads each cleaned DataFrame into DuckDB as a raw source table.
    Tables created:
      raw_crash    ← from Crash CSVs
      raw_casualty ← from Casualty CSVs
      raw_units    ← from Units CSVs

    Uses CREATE OR REPLACE so re-running this script is always safe.
    """
    log.info("=" * 55)
    log.info("STAGE 4 — LOADING INTO DUCKDB")
    log.info("=" * 55)

    os.makedirs("warehouse", exist_ok=True)

    con = duckdb.connect(WAREHOUSE_PATH)

    table_map = {
        "Crash"    : "raw_crash",
        "Casualty" : "raw_casualty",
        "Units"    : "raw_units",
    }

    for table_type, df in master.items():
        table_name = table_map[table_type]
        log.info(f"  Loading {len(df)} rows into DuckDB table: {table_name}")

        # Register the DataFrame as a temporary view then write it
        con.register("_temp_df", df)
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM _temp_df")
        con.unregister("_temp_df")

        # Checkpoint
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        log.info(f"  ✓ {table_name}: {count} rows confirmed in DuckDB")

    con.close()
    log.info(f"Warehouse saved to: {WAREHOUSE_PATH}")
    log.info("Stage 4 complete.\n")


# ============================================================
# MAIN
# ============================================================

def main():
    log.info("SafeRoads SA — Ingestion Pipeline Starting")
    log.info(f"Raw data path : {RAW_DATA_PATH}")
    log.info(f"Warehouse     : {WAREHOUSE_PATH}\n")

    download_files()
    files_to_use = select_best_files()
    master       = merge_and_clean(files_to_use)
    load_to_duckdb(master)

    log.info("=" * 55)
    log.info("Pipeline complete! DuckDB is ready for dbt.")
    log.info("=" * 55)


if __name__ == "__main__":
    main()
