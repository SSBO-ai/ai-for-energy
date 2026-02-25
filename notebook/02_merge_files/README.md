# 02 Merge Files - Review and Refactoring Notes

This README summarizes the current `02_merge_files` workflow, readability findings, decisions, and proposed simplifications.

## Current Pipeline (Observed)

1. `02_1_merge_hourly_utc_files.ipynb`
- Reads cleaned source files from `../../data_cleaned/by_source`.
- Left-merges all sources on `period_start_utc`.
- Performs hourly continuity checks.
- Writes merged base file:
  - `../../data_cleaned/merged/Merge_all_prices_load_gen_res.csv`

2. `02_2_imputed_data_for_2019_to_2025.ipynb`
- Reads merged base file.
- Visualizes missingness.
- Applies domain-specific imputation + limited interpolation.
- Writes:
  - `../../data_cleaned/merged/Data_imputed_2019_to_2025.csv`

3. `02_3_data_tranfromation_to_fourier.ipynb`
- Reads imputed file.
- Adds Fourier features + holiday/day type.
- Writes:
  - `../../data_cleaned/merged/Data_imputed_2019_to_2025_with_Frourier_and_holidays.csv`

4. `02_4_merge_gas_prices.ipynb`
- Merges gas-price source to daily and then hourly views.
- Creates multiple outputs:
  - `../../data_cleaned/merged/02_4_clean_data_daily_mean.csv`
  - `../../data_cleaned/merged/02_4_clean_data_rich_columns.csv`
  - `../../data_cleaned/merged/02_4_clean_data.csv`
  - per-hour daily files under `../../data_cleaned/merged_hour/`

5. `02_data_quality_checks_on_NaN_values.ipynb`
- Additional QA/diagnostic notebook for missingness and plausibility.

## Readability and Clarity Assessment

### What is good
- Logical stage separation (merge -> impute -> transform -> enrich with gas).
- Domain-aware imputation rationale appears in notebook 2.
- Missingness visuals are useful for communication and audit.

### Main clarity issues
- Repeated ad-hoc helper logic inside notebooks (plotting/imputation snippets).
- Several intermediate files with overlapping meaning.
- Naming inconsistency/typos (`Frourier`).
- Some debug leftovers and duplicate save calls.
- QA notebook is separate from pipeline but partly overlaps checks in pipeline notebooks.

## Direct Fixes Applied

1. **Fixed swapped aggregation mapping** in `02_4_merge_gas_prices.ipynb`:
- `gen_forecast_da` now correctly aggregates from `gen_forecast_da`.
- `load_forecast_da` now correctly aggregates from `load_forecast_da`.

2. **Removed invalid debug expression** in `02_3_data_tranfromation_to_fourier.ipynb`:
- Replaced `-mutual_info_regression(...)` with a safe commented placeholder.

## Imputation Graphs - Placement Decision

Question: Are imputation strategy graphs readable and in a good place?

Decision:
- **Yes**, notebook `02_2_imputed_data_for_2019_to_2025.ipynb` is the right place for strategy plots, because:
  - It is where missingness is diagnosed.
  - It is where the imputation rules are applied.
  - It allows before/after visual explanation in the same narrative.

Recommendation for readability:
- Keep only 2-4 canonical plots in notebook 2 (missingness overview + 1-2 key windows + after-imputation check).
- Move optional exploratory plots to a separate `*_exploration` notebook if needed.

## Proposed Simplification Plan (Reduce Scripts and Intermediate Files)

### A) Keep same stages, but tighten outputs
- Keep one output per stage (avoid duplicates unless required downstream).
- Suggested core artifacts only:
  1. `merge_base.csv`
  2. `imputed.csv`
  3. `features.csv`
  4. `final_clean_data.csv`

### B) Extract shared logic to module(s)
Create `notebook/02_merge_files/merge_utils.py` with reusable functions:
- `load_sources(...)`
- `merge_on_period_start_utc(...)`
- `check_hourly_continuity(...)`
- `apply_imputation_rules(...)`
- `interpolate_limited(...)`
- `add_fourier_features(...)`
- `merge_gas_prices_daily_hourly(...)`

### C) Make notebook roles explicit
- `02_1`: assembly + merge quality checks only
- `02_2`: imputation policy + policy plots + save
- `02_3`: feature engineering only
- `02_4`: gas enrichment + final dataset only
- `02_quality`: pure QA report notebook (optional)

### D) Add run configuration cell in each notebook
Common config block:
- input file path(s)
- output file path
- date filters
- flags (`SAVE_INTERMEDIATE`, `RUN_EXTRA_QA`)

## Consistency Checks - Recommended Minimum

At merge stage (`02_1`):
- uniqueness of `period_start_utc`
- continuity of hourly timeline
- 1-hour duration between `period_start_utc` and `period_end_utc`

At imputation stage (`02_2`):
- missingness before/after by column
- count of values filled by each strategy
- no impossible values after interpolation (optional thresholds)

At final stage (`02_4`):
- no key-column nulls for required training features
- date range sanity
- final row count and schema contract check

## If Further Refactoring Is Requested

The next clean step is to implement `merge_utils.py` and reduce notebook code by 30-50% while keeping the same outputs.

