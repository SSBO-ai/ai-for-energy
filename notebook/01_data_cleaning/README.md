# 01 Data Cleaning (Refactored)

This folder is a shortened, standardized version of the original `01_data_cleaning` workflows.

## Scope
- Files `01_dataclean_1` to `01_dataclean_6` follow one generic pattern.
- `01_dataclean_7_energy_prices.ipynb` is kept separate (copied as-is) due to a different source structure.

## Standard Pipeline (01_dataclean_1 to 01_dataclean_6)
1. Read and concatenate yearly CSV files.
2. Select required columns and rename to project-standard names.
3. Split `period` into `period_start` / `period_end`.
4. Parse CET/CEST labels and convert both boundaries to UTC:
   - CET -> UTC = local time - 1 hour
   - CEST -> UTC = local time - 2 hours
5. Build calendar columns from `period_start_utc`.
6. Aggregate quarter-hour records to hourly means for numerical columns.
7. Save hourly source file to `../../data_cleaned/by_source/*.csv`.

## Period Format Examples
The utilities support mixed period strings such as:
- `31/03/2024 01:15:00 - 31/03/2024 01:30:00`
- `31/03/2024 01:45:00 (CET) - 31/03/2024 03:00:00 (CEST)`
- `27/10/2024 02:45:00 (CEST) - 27/10/2024 02:00:00 (CET)`

Timezone state is inferred row-by-row from explicit `(CET)` / `(CEST)` markers.

## Generic Modules
- `cleaning_utils.py`: reusable cleaning and aggregation functions.
- `verify_time_consistency.py`: reusable consistency checks for merge readiness:
  - quarter-hour completeness checks (96 periods/day expected)
  - hourly completeness checks (24 periods/day expected)
  - frequency diagnostics

## Recommended Usage
In each notebook:
1. Define source-specific file list and column mapping.
2. Call `run_source_pipeline(...)` from `cleaning_utils.py`.
3. Run verification functions from `verify_time_consistency.py`.
4. Export hourly cleaned file.

## Merge Readiness Note
Even if the final artifact is hourly, quarter-hour checks should be done before aggregation to detect DST anomalies and missing raw intervals early.
