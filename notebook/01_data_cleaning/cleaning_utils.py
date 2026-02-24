from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import pandas as pd


@dataclass
class PipelineResult:
    raw: pd.DataFrame
    quarter_hour: pd.DataFrame
    hourly: pd.DataFrame


def load_raw_files(files: Iterable[str], delimiter: str = ",") -> pd.DataFrame:
    return pd.concat((pd.read_csv(f, delimiter=delimiter) for f in files), ignore_index=True)


def select_and_rename(
    raw_df: pd.DataFrame,
    keep_cols: list[str],
    rename_map: dict[str, str],
    row_selection_col: Optional[str] = None,
    row_selection_drop_value: Optional[str] = None,
) -> pd.DataFrame:
    df = raw_df.copy()
    if row_selection_col and row_selection_drop_value is not None and row_selection_col in df.columns:
        df = df[df[row_selection_col] != row_selection_drop_value]
    df = df[keep_cols].rename(columns=rename_map)
    return df


def split_period(df: pd.DataFrame, period_col: str = "period") -> pd.DataFrame:
    out = df.copy()
    out[["period_start", "period_end"]] = out[period_col].str.split(" - ", n=1, expand=True)
    return out


def parse_period_with_dst_to_utc(df: pd.DataFrame, col: str) -> pd.DataFrame:
    out = df.copy()

    tz_state = "CET"
    tz_list = []
    for val in out[col].astype(str):
        if "CEST" in val:
            tz_state = "CEST"
        elif "CET" in val:
            tz_state = "CET"
        tz_list.append(tz_state)

    base_dt = pd.to_datetime(
        out[col].astype(str).str.replace(r"\s*\(.*\)$", "", regex=True),
        dayfirst=True,
        errors="coerce",
    )

    out[f"{col}_labeled"] = (
        base_dt.dt.strftime("%d/%m/%Y %H:%M:%S") + " (" + pd.Series(tz_list, index=out.index) + ")"
    )

    offset_hours = pd.Series(tz_list, index=out.index).map({"CET": 1, "CEST": 2})
    out[f"{col}_utc"] = base_dt - pd.to_timedelta(offset_hours, unit="h")
    return out




def coerce_numeric_with_context(
    df: pd.DataFrame,
    value_cols: list[str],
    context_cols: Optional[list[str]] = None,
    raise_on_invalid: bool = False,
    max_examples: int = 20,
) -> pd.DataFrame:
    """Coerce selected value columns to numeric and optionally report invalid raw values.

    Invalid means value cannot be parsed as numeric but is non-empty in raw text.
    """
    out = df.copy()
    context_cols = context_cols or []

    invalid_frames = []
    for col in value_cols:
        raw = out[col]
        num = pd.to_numeric(raw, errors="coerce")

        raw_str = raw.astype(str).str.strip()
        invalid_mask = num.isna() & raw.notna() & (raw_str != "")

        if invalid_mask.any():
            cols_to_show = [c for c in context_cols if c in out.columns] + [col]
            bad = out.loc[invalid_mask, cols_to_show].copy()
            bad["invalid_column"] = col
            invalid_frames.append(bad.head(max_examples))

        out[col] = num

    if invalid_frames:
        report = pd.concat(invalid_frames, ignore_index=True)
        msg = (
            "Non-numeric values were found and coerced to NaN. "
            "Sample rows (with context):\n"
            + report.to_string(index=False)
        )
        if raise_on_invalid:
            raise ValueError(msg)
        else:
            print(msg)

    return out

def add_calendar_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.assign(
        date=lambda x: pd.to_datetime(x["period_start_utc"].dt.date, errors="coerce"),
        year=lambda x: x["period_start_utc"].dt.year,
        month=lambda x: x["period_start_utc"].dt.month,
        day=lambda x: x["period_start_utc"].dt.day,
        dayofyear=lambda x: x["period_start_utc"].dt.dayofyear,
        hour=lambda x: x["period_start_utc"].dt.hour,
        week=lambda x: x["period_start_utc"].dt.isocalendar().week.astype("Int64"),
        dayofweek=lambda x: x["period_start_utc"].dt.dayofweek,
    )
    return out


def aggregate_hourly(df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    # Safety: enforce numeric dtype right before aggregation.
    for c in value_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    group_cols = ["date", "year", "month", "day", "dayofyear", "hour", "week", "dayofweek"]
    agg = {c: (c, "mean") for c in value_cols}
    agg.update({
        "period_start_utc": ("period_start_utc", "min"),
        "period_end_utc": ("period_end_utc", "max"),
        "c_by_hour": ("year", "size"),
    })
    return df.groupby(group_cols, as_index=False).agg(**agg)


def run_source_pipeline(
    files: list[str],
    keep_cols: list[str],
    rename_map: dict[str, str],
    value_cols: list[str],
    row_selection_col: Optional[str] = None,
    row_selection_drop_value: Optional[str] = None,
    include_calendar_columns: bool = True,
) -> PipelineResult:
    raw = load_raw_files(files)
    df = select_and_rename(
        raw, keep_cols=keep_cols, rename_map=rename_map,
        row_selection_col=row_selection_col, row_selection_drop_value=row_selection_drop_value,
    )
    df = split_period(df, period_col="period")
    df = parse_period_with_dst_to_utc(df, col="period_start")
    df = parse_period_with_dst_to_utc(df, col="period_end")

    # Ensure numeric aggregation columns are truly numeric (aligns with original notebook behavior)
    df = coerce_numeric_with_context(
        df,
        value_cols=value_cols,
        context_cols=['period', 'period_start_utc', 'period_end_utc'],
        raise_on_invalid=False,
    )

    quarter = df.drop(columns=["period", "period_start", "period_end", "period_start_labeled", "period_end_labeled"])

    if include_calendar_columns:
        quarter = add_calendar_columns(quarter)
        hourly = aggregate_hourly(quarter, value_cols=value_cols)
    else:
        # Keep quarter-hour UTC table and defer calendar engineering to later stages (e.g., 02_merge_files)
        hourly = pd.DataFrame()

    return PipelineResult(raw=raw, quarter_hour=quarter, hourly=hourly)


# Backward-compatible alias (deprecated name)
add_timezone_and_utc = parse_period_with_dst_to_utc
