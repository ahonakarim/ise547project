"""MVP analytics tests using deterministic in-memory DataFrames."""

from __future__ import annotations

import pandas as pd

from app.analytics import (
    execute_structured_query,
    run_filtered_aggregation,
    run_grouped_aggregation,
    run_summary_stat,
    run_time_series,
)
from app.schemas import StructuredQuery


def _base_df() -> pd.DataFrame:
    """Small deterministic DataFrame for analytics tests."""
    return pd.DataFrame(
        {
            "sales": [100, 200, 300, 400],
            "region": ["East", "West", "East", "West"],
            "smoker": ["yes", "no", "yes", "no"],
            "event_date": pd.to_datetime(
                ["2024-01-05", "2024-01-20", "2024-02-01", "2024-02-15"]
            ),
        }
    )


def test_summary_mean() -> None:
    query = StructuredQuery(
        task_type="summary_stat",
        metric_column="sales",
        aggregation="mean",
        chart_type="none",
    )
    result = run_summary_stat(_base_df(), query)
    assert result.result_type == "scalar"
    assert result.value == 250
    assert result.error is None


def test_summary_max() -> None:
    query = StructuredQuery(
        task_type="summary_stat",
        metric_column="sales",
        aggregation="max",
        chart_type="none",
    )
    result = run_summary_stat(_base_df(), query)
    assert result.result_type == "scalar"
    assert result.value == 400
    assert result.error is None


def test_grouped_sum() -> None:
    query = StructuredQuery(
        task_type="grouped_aggregation",
        metric_column="sales",
        aggregation="sum",
        groupby_column="region",
        chart_type="bar",
    )
    result = run_grouped_aggregation(_base_df(), query)
    assert result.result_type == "table"
    assert isinstance(result.table, list)
    assert result.table == [{"region": "West", "value": 600}, {"region": "East", "value": 400}]
    assert result.error is None


def test_filtered_aggregation() -> None:
    query = StructuredQuery(
        task_type="filtered_aggregation",
        metric_column="sales",
        aggregation="mean",
        filters=[{"column": "smoker", "operator": "==", "value": "yes"}],
        chart_type="none",
    )
    result = run_filtered_aggregation(_base_df(), query)
    assert result.result_type == "scalar"
    assert result.value == 200
    assert result.error is None


def test_time_series_monthly_aggregation() -> None:
    query = StructuredQuery(
        task_type="time_series",
        metric_column="sales",
        aggregation="sum",
        time_column="event_date",
        time_granularity="month",
        chart_type="line",
    )
    result = run_time_series(_base_df(), query)
    assert result.result_type == "timeseries"
    assert isinstance(result.table, list)
    assert len(result.table) == 2
    assert result.table[0]["value"] == 300
    assert result.table[1]["value"] == 700
    assert result.error is None


def test_execute_structured_query_dispatch() -> None:
    query = StructuredQuery(
        task_type="summary_stat",
        metric_column="sales",
        aggregation="mean",
        chart_type="none",
    )
    result = execute_structured_query(_base_df(), query)
    assert result.result_type == "scalar"
    assert result.value == 250


def test_success_result_has_consistent_shape() -> None:
    query = StructuredQuery(
        task_type="summary_stat",
        metric_column="sales",
        aggregation="mean",
        chart_type="none",
    )
    result = run_summary_stat(_base_df(), query)
    payload = result.model_dump()
    assert set(payload.keys()) == {"result_type", "value", "table", "chart_data", "message", "error"}


def test_execution_error_handling_path() -> None:
    # Deliberately bypass validator to trigger execution-path error handling.
    bad_query = StructuredQuery.model_construct(
        task_type="summary_stat",
        metric_column="missing_col",
        aggregation="mean",
        chart_type="none",
        filters=[],
    )
    result = run_summary_stat(_base_df(), bad_query)
    assert result.result_type == "error"
    assert result.error == "execution_error"
    assert result.message is not None
