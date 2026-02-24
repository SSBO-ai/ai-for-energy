from __future__ import annotations

import argparse
from typing import Optional

import pandas as pd


def summarize_frequency(df: pd.DataFrame, ts_col: str) -> pd.Series:
    s = pd.to_datetime(df[ts_col], errors='coerce').dropna().sort_values()
    diffs = s.diff().dropna()
    return diffs.value_counts().sort_index()


def check_completeness_per_day(df: pd.DataFrame, ts_col: str, expected_count: int) -> pd.DataFrame:
    s = pd.to_datetime(df[ts_col], errors='coerce')
    day_counts = s.dt.floor('D').value_counts().sort_index().rename('n_periods').to_frame()
    day_counts['expected'] = expected_count
    day_counts['is_complete'] = day_counts['n_periods'] == day_counts['expected']
    return day_counts


def run_checks(df: pd.DataFrame, ts_col: str = 'period_start_utc') -> None:
    print('--- Frequency summary ---')
    print(summarize_frequency(df, ts_col))

    print('\n--- 15-min completeness (expected 96/day) ---')
    c15 = check_completeness_per_day(df, ts_col, expected_count=96)
    print(c15['is_complete'].value_counts(dropna=False))
    if (~c15['is_complete']).any():
        print('Sample incomplete 15-min days:')
        print(c15[~c15['is_complete']].head())


def run_hourly_checks(df_hourly: pd.DataFrame, ts_col: str = 'period_start_utc') -> None:
    print('\n--- Hourly completeness (expected 24/day) ---')
    c1h = check_completeness_per_day(df_hourly, ts_col, expected_count=24)
    print(c1h['is_complete'].value_counts(dropna=False))
    if (~c1h['is_complete']).any():
        print('Sample incomplete hourly days:')
        print(c1h[~c1h['is_complete']].head())


def main() -> None:
    parser = argparse.ArgumentParser(description='Verify time consistency for cleaned source files.')
    parser.add_argument('csv_path', help='Path to CSV file to verify')
    parser.add_argument('--ts-col', default='period_start_utc', help='Timestamp column name')
    parser.add_argument('--hourly', action='store_true', help='Run hourly completeness check (24/day)')
    args = parser.parse_args()

    df = pd.read_csv(args.csv_path)
    if args.hourly:
        run_hourly_checks(df, ts_col=args.ts_col)
    else:
        run_checks(df, ts_col=args.ts_col)


if __name__ == '__main__':
    main()
