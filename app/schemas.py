"""Pydantic schemas for CSV Analyst Assistant.

The schema surface is intentionally constrained to the documented scope:
- supported task types only
- structured, validated intent objects
- consistent backend/evaluation result contracts
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.constants import (
    AGGREGATIONS,
    CHART_TYPES,
    FILTER_OPERATORS,
    MAX_FILTERS,
    RESULT_TYPES,
    TASK_TYPES,
    TIME_GRANULARITIES,
)

TaskType = Literal["summary_stat", "grouped_aggregation", "filtered_aggregation", "time_series"]
Aggregation = Literal["count", "sum", "mean", "median", "min", "max"]
FilterOperator = Literal[
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "contains",
]
TimeGranularity = Literal["day", "week", "month"]
ChartType = Literal["none", "table", "bar", "line"]
ResultType = Literal["scalar", "table", "timeseries", "error"]


class FilterCondition(BaseModel):
    """Single structured filter condition."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(..., min_length=1)
    operator: FilterOperator
    value: Any | None = None

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        if value not in FILTER_OPERATORS:
            raise ValueError(f"Unsupported filter operator: {value}")
        return value

    @model_validator(mode="after")
    def validate_value_requirements(self) -> "FilterCondition":
        if self.value is None:
            raise ValueError("Filter value is required for this operator.")
        return self


class StructuredQuery(BaseModel):
    """Canonical intent schema produced by LLM parsing."""

    model_config = ConfigDict(extra="forbid")

    task_type: TaskType
    metric_column: str | None = None
    aggregation: Aggregation | None = None
    groupby_column: str | None = None
    filters: list[FilterCondition] = Field(default_factory=list)
    time_column: str | None = None
    time_granularity: TimeGranularity | None = None
    chart_type: ChartType = "none"
    chart_title: str | None = None

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, value: str) -> str:
        if value not in TASK_TYPES:
            raise ValueError(f"Unsupported task type: {value}")
        return value

    @field_validator("aggregation")
    @classmethod
    def validate_aggregation(cls, value: str | None) -> str | None:
        if value is not None and value not in AGGREGATIONS:
            raise ValueError(f"Unsupported aggregation: {value}")
        return value

    @field_validator("time_granularity")
    @classmethod
    def validate_time_granularity(cls, value: str | None) -> str | None:
        if value is not None and value not in TIME_GRANULARITIES:
            raise ValueError(f"Unsupported time granularity: {value}")
        return value

    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, value: str) -> str:
        if value not in CHART_TYPES:
            raise ValueError(f"Unsupported chart type: {value}")
        return value

    @field_validator("filters")
    @classmethod
    def validate_max_filters(cls, value: list[FilterCondition]) -> list[FilterCondition]:
        if len(value) > MAX_FILTERS:
            raise ValueError(f"Too many filters. Max allowed: {MAX_FILTERS}")
        return value

    @model_validator(mode="after")
    def validate_task_requirements(self) -> "StructuredQuery":
        if self.task_type in {"summary_stat", "grouped_aggregation", "filtered_aggregation", "time_series"}:
            if not self.metric_column:
                raise ValueError("metric_column is required for this task type.")
            if not self.aggregation:
                raise ValueError("aggregation is required for this task type.")

        if self.task_type == "grouped_aggregation" and not self.groupby_column:
            raise ValueError("groupby_column is required for grouped_aggregation.")

        if self.task_type == "filtered_aggregation" and not self.filters:
            raise ValueError("At least one filter is required for filtered_aggregation.")

        if self.task_type == "time_series":
            if not self.time_column:
                raise ValueError("time_column is required for time_series.")
            if not self.time_granularity:
                raise ValueError("time_granularity is required for time_series.")

        # Keep charting in a conservative supported set by task type.
        allowed_by_task: dict[str, set[str]] = {
            "summary_stat": {"none", "table"},
            "grouped_aggregation": {"none", "table", "bar"},
            "filtered_aggregation": {"none", "table", "bar"},
            "time_series": {"none", "table", "line"},
        }
        if self.chart_type not in allowed_by_task[self.task_type]:
            raise ValueError(
                f"chart_type='{self.chart_type}' is not supported for task_type='{self.task_type}'."
            )

        return self


class BackendResult(BaseModel):
    """Normalized backend response contract used by frontend and evaluation."""

    model_config = ConfigDict(extra="forbid")

    result_type: ResultType
    value: float | int | str | None = None
    table: list[dict[str, Any]] | None = None
    chart_data: dict[str, Any] | None = None
    message: str | None = None
    error: str | None = None

    @field_validator("result_type")
    @classmethod
    def validate_result_type(cls, value: str) -> str:
        if value not in RESULT_TYPES:
            raise ValueError(f"Unsupported result type: {value}")
        return value


class BenchmarkQuestion(BaseModel):
    """Row schema for benchmark dataset entries used in evaluation.

    This maps directly to docs-defined benchmark fields and supports
    interpretation + end-to-end evaluation pipelines.
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(..., min_length=1)
    dataset_name: str = Field(..., min_length=1)
    question_text: str = Field(..., min_length=1)
    task_type: TaskType
    metric_column: str | None = None
    aggregation: Aggregation | None = None
    groupby_column: str | None = None
    filters: list[FilterCondition] = Field(default_factory=list)
    time_column: str | None = None
    time_granularity: TimeGranularity | None = None
    expected_chart_type: ChartType = "none"
    expected_scalar_answer: float | int | str | None = None
    expected_table: list[dict[str, Any]] | None = None
