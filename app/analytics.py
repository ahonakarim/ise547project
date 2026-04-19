"""Pandas analytics engine for MVP structured query execution."""

from __future__ import annotations

from typing import Callable

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

from app.constants import CHART_VALUE_COLUMN, ERR_EXECUTION
from app.charts import make_bar_chart, make_line_chart, make_scatter_plot
from app.schemas import BackendResult, FilterCondition, StructuredQuery
from app.utils import build_error_result, normalize_result


def apply_filters(df: pd.DataFrame, filters: list[FilterCondition]) -> pd.DataFrame:
    """Apply MVP filter conditions and return a filtered DataFrame copy."""
    filtered_df = df.copy()

    for condition in filters:
        column = condition.column
        value = condition.value
        operator = condition.operator
        series = filtered_df[column]

        if operator == "==":
            mask = series == value
        elif operator == "!=":
            mask = series != value
        elif operator == ">":
            mask = series > value
        elif operator == ">=":
            mask = series >= value
        elif operator == "<":
            mask = series < value
        elif operator == "<=":
            mask = series <= value
        elif operator == "contains":
            mask = series.astype(str).str.contains(str(value), case=False, na=False)
        else:
            raise ValueError(f"Unsupported filter operator: {operator}")

        filtered_df = filtered_df[mask]

    return filtered_df


def _compute_aggregation(series: pd.Series, aggregation: str) -> float | int:
    """Compute one MVP aggregation on a pandas Series."""
    aggregation_map: dict[str, Callable[[], float | int]] = {
        "count": lambda: int(series.count()),
        "sum": lambda: series.sum(),
        "mean": lambda: series.mean(),
        "median": lambda: series.median(),
        "min": lambda: series.min(),
        "max": lambda: series.max(),
    }
    if aggregation not in aggregation_map:
        raise ValueError(f"Unsupported aggregation: {aggregation}")
    return aggregation_map[aggregation]()


def _build_chart_data(
    table_df: pd.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str,
    title: str = "",
) -> dict[str, object] | None:
    """Create chart metadata and figure object for supported chart types."""
    if chart_type in {"none", "table"}:
        return None

    if chart_type == "bar":
        figure = make_bar_chart(table_df, x_col, y_col, title=title)
    elif chart_type == "line":
        figure = make_line_chart(table_df, x_col, y_col, title=title)
    elif chart_type == "scatter":
        figure = make_scatter_plot(table_df, x_col, y_col, title=title)
    else:
        return None

    return {
        "chart_type": chart_type,
        "x": x_col,
        "y": y_col,
        "figure": figure,
    }


def run_summary_stat(df: pd.DataFrame, query: StructuredQuery) -> BackendResult:
    """Execute a summary_stat query on one metric column."""
    try:
        value = _compute_aggregation(df[query.metric_column], query.aggregation)  # type: ignore[index]
        return normalize_result(
            {
                "result_type": "scalar",
                "value": value,
                "table": None,
                "chart_data": None,
                "message": f"{query.aggregation}({query.metric_column}) computed successfully.",
                "error": None,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive
        return build_error_result(f"Failed to run summary_stat: {exc}", error_code=ERR_EXECUTION)


def run_grouped_aggregation(df: pd.DataFrame, query: StructuredQuery) -> BackendResult:
    """Execute grouped_aggregation with a stable output contract.

    Output table schema is always:
    - `<groupby_column>`: group key
    - `value`: aggregated metric value (standardized via CHART_VALUE_COLUMN)

    Sorting is deterministic:
    - primary: `value` descending
    - secondary (tie-break): `<groupby_column>` ascending
    """
    try:
        grouped = (
            df.groupby(query.groupby_column, dropna=False)[query.metric_column]  # type: ignore[index]
            .agg(query.aggregation)  # type: ignore[arg-type]
            .reset_index()
        )
        grouped.columns = [query.groupby_column, CHART_VALUE_COLUMN]  # type: ignore[list-item]
        grouped = grouped.sort_values(
            by=[CHART_VALUE_COLUMN, query.groupby_column],  # type: ignore[list-item]
            ascending=[False, True],
        ).reset_index(drop=True)

        return normalize_result(
            {
                "result_type": "table",
                "value": None,
                "table": grouped.to_dict(orient="records"),
                "chart_data": _build_chart_data(
                    grouped,
                    query.chart_type,
                    query.groupby_column,  # type: ignore[arg-type]
                    CHART_VALUE_COLUMN,
                    title=query.chart_title or "",
                ),
                "message": "Grouped aggregation computed successfully.",
                "error": None,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive
        return build_error_result(f"Failed to run grouped_aggregation: {exc}", error_code=ERR_EXECUTION)


def run_filtered_aggregation(df: pd.DataFrame, query: StructuredQuery) -> BackendResult:
    """Execute filtered_aggregation by filtering first, then aggregating metric."""
    try:
        filtered_df = apply_filters(df, query.filters)
        value = _compute_aggregation(filtered_df[query.metric_column], query.aggregation)  # type: ignore[index]

        return normalize_result(
            {
                "result_type": "scalar",
                "value": value,
                "table": None,
                "chart_data": None,
                "message": f"Filtered aggregation computed on {len(filtered_df)} rows.",
                "error": None,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive
        return build_error_result(f"Failed to run filtered_aggregation: {exc}", error_code=ERR_EXECUTION)


def run_time_series(df: pd.DataFrame, query: StructuredQuery) -> BackendResult:
    """Execute time_series aggregation by day/week/month."""
    try:
        working = df.copy()
        tc = query.time_column  # type: ignore[assignment]
        if tc not in working.columns:
            return build_error_result("time_column missing from DataFrame.", error_code=ERR_EXECUTION)
        if not is_datetime64_any_dtype(working[tc]):
            working[tc] = pd.to_datetime(working[tc], errors="coerce")
        working = working.dropna(subset=[tc])
        # Pandas 3 uses ME (month-end) instead of the removed M alias.
        freq_map = {"day": "D", "week": "W", "month": "ME"}
        freq = freq_map[query.time_granularity]  # type: ignore[index]

        series = (
            working.set_index(tc)[query.metric_column]  # type: ignore[index]
            .resample(freq)
            .agg(query.aggregation)  # type: ignore[arg-type]
            .dropna()
        )
        table_df = series.reset_index()
        table_df.columns = [query.time_column, CHART_VALUE_COLUMN]  # type: ignore[list-item]
        table_df[query.time_column] = table_df[query.time_column].astype(str)  # type: ignore[index]

        return normalize_result(
            {
                "result_type": "timeseries",
                "value": None,
                "table": table_df.to_dict(orient="records"),
                "chart_data": _build_chart_data(
                    table_df,
                    query.chart_type,
                    query.time_column,  # type: ignore[arg-type]
                    CHART_VALUE_COLUMN,
                    title=query.chart_title or "",
                ),
                "message": "Time-series aggregation computed successfully.",
                "error": None,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive
        return build_error_result(f"Failed to run time_series: {exc}", error_code=ERR_EXECUTION)


def execute_structured_query(df: pd.DataFrame, query: StructuredQuery) -> BackendResult:
    """Dispatch a validated StructuredQuery to the correct MVP analytics handler."""
    if query.task_type == "summary_stat":
        return run_summary_stat(df, query)
    if query.task_type == "grouped_aggregation":
        return run_grouped_aggregation(df, query)
    if query.task_type == "filtered_aggregation":
        return run_filtered_aggregation(df, query)
    if query.task_type == "time_series":
        return run_time_series(df, query)
    return build_error_result(
        f"Unsupported task type: {query.task_type}",
        error_code=ERR_EXECUTION,
    )
