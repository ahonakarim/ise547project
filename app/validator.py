"""Validation layer for StructuredQuery against a pandas DataFrame."""

from __future__ import annotations

import pandas as pd

from app.schemas import BackendResult, StructuredQuery
from app.utils import build_error_result, is_datetime_series, is_numeric_series

_NUMERIC_OPS: set[str] = {">", ">=", "<", "<="}
_TEXT_OPS: set[str] = {"contains"}


def _validate_required_columns(query: StructuredQuery, df: pd.DataFrame) -> list[str]:
    """Validate that query-referenced columns exist in the DataFrame."""
    errors: list[str] = []
    available = set(df.columns.astype(str))

    required_columns: list[str] = []
    if query.metric_column:
        required_columns.append(query.metric_column)
    if query.groupby_column:
        required_columns.append(query.groupby_column)
    if query.time_column:
        required_columns.append(query.time_column)
    required_columns.extend(f.column for f in query.filters)

    for col in required_columns:
        if col not in available:
            errors.append(f"Column '{col}' does not exist in the uploaded dataset.")
    return errors


def _validate_dtype_constraints(query: StructuredQuery, df: pd.DataFrame) -> list[str]:
    """Validate numeric and datetime compatibility for query fields."""
    errors: list[str] = []

    if query.metric_column and query.metric_column in df.columns:
        metric_series = df[query.metric_column]
        if query.aggregation in {"sum", "mean", "median", "min", "max"} and not is_numeric_series(metric_series):
            errors.append(
                f"Column '{query.metric_column}' must be numeric for aggregation '{query.aggregation}'."
            )

    if query.task_type == "time_series" and query.time_column and query.time_column in df.columns:
        if not is_datetime_series(df[query.time_column]):
            errors.append(
                f"Column '{query.time_column}' must be datetime-compatible for task_type 'time_series'."
            )

    return errors


def _validate_filter_compatibility(query: StructuredQuery, df: pd.DataFrame) -> list[str]:
    """Validate filter operators and values against DataFrame column types."""
    errors: list[str] = []
    for item in query.filters:
        if item.column not in df.columns:
            # Column existence handled separately; avoid noisy duplicates.
            continue

        series = df[item.column]
        if item.operator in _NUMERIC_OPS and not is_numeric_series(series):
            errors.append(f"Filter '{item.operator}' requires numeric column; '{item.column}' is not numeric.")

        if item.operator in _TEXT_OPS and is_numeric_series(series):
            errors.append(f"Filter 'contains' should be used with text-like columns; '{item.column}' is numeric.")

        if item.operator == "contains" and not isinstance(item.value, str):
            errors.append("Filter 'contains' requires a string value.")

    return errors


def _validate_task_constraints(query: StructuredQuery) -> list[str]:
    """Validate task-level constraints specific to MVP-supported task types."""
    errors: list[str] = []

    if query.task_type == "summary_stat" and query.groupby_column:
        errors.append("task_type 'summary_stat' must not include 'groupby_column'.")

    return errors


def validate_structured_query(query: StructuredQuery, df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate a structured query against the uploaded DataFrame.

    Returns:
        (is_valid, errors): boolean validity flag and a list of clear messages.
    """
    if df.empty:
        return False, ["Uploaded dataset is empty."]

    errors: list[str] = []
    errors.extend(_validate_required_columns(query, df))
    errors.extend(_validate_task_constraints(query))
    errors.extend(_validate_dtype_constraints(query, df))
    errors.extend(_validate_filter_compatibility(query, df))
    return len(errors) == 0, errors


def validate_query_or_error_result(query: StructuredQuery, df: pd.DataFrame) -> tuple[bool, BackendResult | None]:
    """Validate query and return a normalized error result when invalid."""
    is_valid, errors = validate_structured_query(query, df)
    if is_valid:
        return True, None
    message = "; ".join(errors)
    return False, build_error_result(message=message, error_code="validation_error")

