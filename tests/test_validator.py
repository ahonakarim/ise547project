"""Basic validation tests for StructuredQuery and DataFrame checks."""

from __future__ import annotations

import pandas as pd

from app.schemas import StructuredQuery
from app.validator import validate_structured_query


def _sample_df() -> pd.DataFrame:
    """Create a small in-memory DataFrame for validator tests."""
    return pd.DataFrame(
        {
            "sales": [100.0, 200.0, 300.0],
            "region": ["East", "West", "East"],
            "age": [30, 42, 55],
            "event_date": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
        }
    )


def test_valid_summary_query_passes_validation() -> None:
    """A valid summary_stat query should pass."""
    query = StructuredQuery(
        task_type="summary_stat",
        metric_column="sales",
        aggregation="mean",
        chart_type="none",
    )

    is_valid, errors = validate_structured_query(query, _sample_df())

    assert is_valid is True
    assert errors == []


def test_invalid_metric_column_fails_validation() -> None:
    """Missing metric column should return a clear validation error."""
    query = StructuredQuery(
        task_type="summary_stat",
        metric_column="missing_metric",
        aggregation="mean",
        chart_type="none",
    )

    is_valid, errors = validate_structured_query(query, _sample_df())

    assert is_valid is False
    assert any("missing_metric" in message for message in errors)


def test_invalid_groupby_column_fails_validation() -> None:
    """Missing groupby column should fail grouped_aggregation validation."""
    query = StructuredQuery(
        task_type="grouped_aggregation",
        metric_column="sales",
        aggregation="sum",
        groupby_column="missing_group",
        chart_type="bar",
    )

    is_valid, errors = validate_structured_query(query, _sample_df())

    assert is_valid is False
    assert any("missing_group" in message for message in errors)


def test_invalid_time_column_fails_validation() -> None:
    """Missing time column should fail time_series validation."""
    query = StructuredQuery(
        task_type="time_series",
        metric_column="sales",
        aggregation="sum",
        time_column="missing_time",
        time_granularity="month",
        chart_type="line",
    )

    is_valid, errors = validate_structured_query(query, _sample_df())

    assert is_valid is False
    assert any("missing_time" in message for message in errors)
