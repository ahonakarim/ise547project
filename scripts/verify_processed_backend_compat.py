"""Verify cleaned CSVs in data/processed/ against MVP StructuredQuery + validator rules.

Prints JSON summary: task support, metric columns (numeric vs count-only), groupby columns,
and primary time column usability.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_float_dtype,
    is_integer_dtype,
    is_numeric_dtype,
    is_string_dtype,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.analytics import execute_structured_query  # noqa: E402
from app.schemas import StructuredQuery  # noqa: E402
from app.utils import is_datetime_series, is_numeric_series  # noqa: E402
from app.validator import validate_structured_query  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
MANIFEST = PROCESSED / "dataset_schemas.json"


def _metric_numeric_columns(df: pd.DataFrame) -> list[str]:
    out: list[str] = []
    for c in df.columns:
        s = df[c]
        if is_numeric_series(s) and not is_bool_dtype(s):
            out.append(str(c))
    return sorted(out)


def _metric_count_any_columns(df: pd.DataFrame) -> list[str]:
    """Columns usable with aggregation ``count`` (any dtype)."""
    return sorted(str(c) for c in df.columns)


def _groupby_columns(df: pd.DataFrame, *, exclude_datetime_like: bool = True) -> list[str]:
    """Discrete / string-like columns suitable for ``groupby_column`` (exclude plain floats).

    When ``exclude_datetime_like`` is True, omit columns that parse as datetimes so they
    are reserved for ``time_series`` rather than mistaken for categorical dimensions.
    """
    out: list[str] = []
    for c in df.columns:
        s = df[c]
        if is_float_dtype(s):
            continue
        if exclude_datetime_like and is_datetime_series(s):
            continue
        if (
            is_integer_dtype(s)
            or is_bool_dtype(s)
            or is_string_dtype(s)
            or s.dtype == object
            or isinstance(s.dtype, pd.CategoricalDtype)
        ):
            out.append(str(c))
    return sorted(out)


def _primary_time_from_manifest(ds_id: str) -> str | None:
    if not MANIFEST.is_file():
        return None
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = data.get("datasets", {}).get(ds_id, {})
    return entry.get("primary_time_column")


def _smoke(
    df: pd.DataFrame,
    *,
    time_col: str | None,
    metric: str,
    groupby: str,
    filter_col: str,
    filter_val,
) -> dict[str, bool]:
    """Run minimal valid queries per task type (best-effort columns)."""
    ok: dict[str, bool] = {}
    tests = [
        (
            "summary_stat",
            StructuredQuery(
                task_type="summary_stat",
                metric_column=metric,
                aggregation="mean",
                chart_type="none",
            ),
        ),
        (
            "grouped_aggregation",
            StructuredQuery(
                task_type="grouped_aggregation",
                metric_column=metric,
                aggregation="sum",
                groupby_column=groupby,
                chart_type="bar",
            ),
        ),
        (
            "filtered_aggregation",
            StructuredQuery(
                task_type="filtered_aggregation",
                metric_column=metric,
                aggregation="mean",
                filters=[{"column": filter_col, "operator": "==", "value": filter_val}],
                chart_type="none",
            ),
        ),
    ]
    for name, q in tests:
        valid, _errs = validate_structured_query(q, df)
        if not valid:
            ok[name] = False
            continue
        res = execute_structured_query(df, q)
        ok[name] = res.error is None and res.result_type != "error"

    if time_col and time_col in df.columns:
        q = StructuredQuery(
            task_type="time_series",
            metric_column=metric,
            aggregation="sum",
            time_column=time_col,
            time_granularity="month",
            chart_type="line",
        )
        valid, _errs = validate_structured_query(q, df)
        if not valid:
            ok["time_series"] = False
        else:
            res = execute_structured_query(df, q)
            ok["time_series"] = res.error is None and res.result_type == "timeseries"
    else:
        ok["time_series"] = False
    return ok


def analyze_dataset(ds_id: str, csv_path: Path) -> dict:
    df = pd.read_csv(csv_path, low_memory=False)
    time_col = _primary_time_from_manifest(ds_id)
    time_ok = bool(time_col and time_col in df.columns and is_datetime_series(df[time_col]))

    metrics_num = _metric_numeric_columns(df)
    metrics_all = _metric_count_any_columns(df)
    groupbys = _groupby_columns(df)

    metric = metrics_num[0] if metrics_num else metrics_all[0]
    groupby = next((g for g in groupbys if g != metric), groupbys[0])
    # filter: pick a string column with a stable value
    filter_col, filter_val = groupby, df[groupby].dropna().iloc[0]
    if filter_col == metric:
        filter_col = groupbys[1] if len(groupbys) > 1 else groupbys[0]
        filter_val = df[filter_col].dropna().iloc[0]

    smoke = _smoke(df, time_col=time_col if time_ok else None, metric=metric, groupby=groupby, filter_col=filter_col, filter_val=filter_val)
    if not time_ok:
        smoke["time_series"] = False

    task_support = {
        "summary_stat": smoke.get("summary_stat", False),
        "grouped_aggregation": smoke.get("grouped_aggregation", False),
        "filtered_aggregation": smoke.get("filtered_aggregation", False),
        "time_series": bool(time_ok and smoke.get("time_series", False)),
    }

    return {
        "dataset_id": ds_id,
        "csv": str(csv_path.relative_to(ROOT)),
        "rows": len(df),
        "primary_time_column": time_col,
        "time_column_parseable_as_datetime": time_ok,
        "task_support": task_support,
        "metric_columns_numeric_aggregations": metrics_num,
        "metric_columns_count_supported": metrics_all,
        "groupby_columns": groupbys,
        "smoke_queries_ok": smoke,
    }


def main() -> None:
    datasets = [
        ("insurance", PROCESSED / "insurance_cleaned.csv"),
        ("yellow_tripdata_2026_01", PROCESSED / "yellow_tripdata_2026_01_cleaned.csv"),
        ("online_retail_ii", PROCESSED / "online_retail_ii_cleaned.csv"),
    ]
    report: dict = {"datasets": {}}
    for ds_id, path in datasets:
        if not path.is_file():
            report["datasets"][ds_id] = {"error": f"missing file: {path}"}
            continue
        report["datasets"][ds_id] = analyze_dataset(ds_id, path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
