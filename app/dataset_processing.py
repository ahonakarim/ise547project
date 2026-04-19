"""Clean uploaded-style tabular files: normalized columns, primary time column, processed CSV."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.column_normalization import normalize_column_name, rename_dataframe_columns

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

# Stronger signals win when multiple columns parse as datetimes.
_TIME_NAME_SCORE = re.compile(
    r"pickup|dropoff|invoice|timestamp|datetime|_at$|_date$|^date_|event|created",
    re.IGNORECASE,
)


def _dtype_label(series: pd.Series) -> str:
    return str(series.dtype)


def infer_schema_records(df: pd.DataFrame) -> list[dict[str, str]]:
    """Return list of ``{column, dtype}`` using pandas dtypes after coercion."""
    return [{"column": str(c), "dtype": _dtype_label(df[c])} for c in df.columns]


def infer_primary_time_column(df: pd.DataFrame) -> str | None:
    """Pick one primary time column from normalized names, if clearly datetime-like."""
    scored: list[tuple[int, float, str]] = []  # hint_score, parse_ratio, col

    for col in df.columns:
        name = str(col)
        series = df[col]
        # Avoid treating small integers (e.g. child counts) as epoch timestamps.
        if (
            pd.api.types.is_integer_dtype(series)
            or pd.api.types.is_float_dtype(series)
        ) and not _TIME_NAME_SCORE.search(name):
            continue

        parsed = pd.to_datetime(series, errors="coerce", utc=False)
        if len(df) == 0:
            continue
        ratio = float(parsed.notna().mean())
        if ratio < 0.85:
            continue
        hint = 2 if _TIME_NAME_SCORE.search(name) else (1 if re.search(r"date|time", name, re.I) else 0)
        scored.append((hint, ratio, str(col)))

    if not scored:
        return None
    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return scored[0][2]


def coerce_time_column_to_datetime_strings(df: pd.DataFrame, time_col: str | None) -> pd.DataFrame:
    """Parse ``time_col`` and store ISO-like ``YYYY-MM-DD HH:MM:SS`` strings (naive)."""
    if not time_col or time_col not in df.columns:
        return df
    out = df.copy()
    parsed = pd.to_datetime(out[time_col], errors="coerce")
    out[time_col] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
    out.loc[parsed.isna(), time_col] = ""
    return out


def process_dataframe(
    df: pd.DataFrame,
    *,
    primary_time_override: str | None = None,
) -> tuple[pd.DataFrame, str | None, list[dict[str, str]]]:
    """Normalize column names, infer or override primary time column, coerce time to ISO strings.

    Returns ``(cleaned_df, primary_time_column_or_none, schema_records)``.
    """
    cleaned = rename_dataframe_columns(df)
    if primary_time_override:
        cand = normalize_column_name(primary_time_override)
        time_col = cand if cand in cleaned.columns else infer_primary_time_column(cleaned)
    else:
        time_col = infer_primary_time_column(cleaned)

    cleaned = coerce_time_column_to_datetime_strings(cleaned, time_col)
    schema = infer_schema_records(cleaned)
    return cleaned, time_col, schema


def save_processed_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def write_schema_manifest(manifest: dict[str, Any], path: Path | None = None) -> Path:
    path = path or (PROCESSED_DIR / "dataset_schemas.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path
