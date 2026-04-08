"""Central constants for CSV Analyst Assistant backend.

This module defines allowed task types, operations, chart options, and
shared defaults so schema validation, execution, and evaluation stay aligned.
"""

from __future__ import annotations

from typing import Final

# Supported scope (source of truth from docs/)
TASK_TYPES: Final[tuple[str, ...]] = (
    "summary_stat",
    "grouped_aggregation",
    "filtered_aggregation",
    "time_series",
)

AGGREGATIONS: Final[tuple[str, ...]] = (
    "count",
    "sum",
    "mean",
    "median",
    "min",
    "max",
)

FILTER_OPERATORS: Final[tuple[str, ...]] = (
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "contains",
)

TIME_GRANULARITIES: Final[tuple[str, ...]] = ("day", "week", "month")

CHART_TYPES: Final[tuple[str, ...]] = ("none", "table", "bar", "line")

# Prompt ids remain snake_case in code.
# Mapping to docs labels:
# - minimal -> "minimal"
# - schema_aware -> "schema-aware"
# - few_shot -> "few-shot"
# - strict_anti_hallucination -> "strict anti-hallucination"
PROMPT_VARIANTS: Final[tuple[str, ...]] = (
    "minimal",
    "schema_aware",
    "few_shot",
    "strict_anti_hallucination",
)

RESULT_TYPES: Final[tuple[str, ...]] = (
    "scalar",
    "table",
    "timeseries",
    "error",
)

DEFAULT_TOP_K: Final[int] = 10
DEFAULT_PREVIEW_ROWS: Final[int] = 20
MAX_FILTERS: Final[int] = 8

# Standard result keys (consistent output contract)
RESULT_KEYS: Final[tuple[str, ...]] = (
    "result_type",
    "value",
    "table",
    "chart_data",
    "message",
    "error",
)
CHART_VALUE_COLUMN: Final[str] = "value"

# Validation error codes for frontend + evaluation logs
ERR_INVALID_TASK_TYPE: Final[str] = "invalid_task_type"
ERR_MISSING_REQUIRED_FIELD: Final[str] = "missing_required_field"
ERR_INVALID_AGGREGATION: Final[str] = "invalid_aggregation"
ERR_INVALID_FILTER: Final[str] = "invalid_filter"
ERR_INVALID_TIME_CONFIG: Final[str] = "invalid_time_config"
ERR_INVALID_CHART_TYPE: Final[str] = "invalid_chart_type"
ERR_SCHEMA_VALIDATION: Final[str] = "schema_validation_error"
ERR_EXECUTION: Final[str] = "execution_error"
