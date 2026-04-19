"""Utility helpers for backend validation and result normalization."""

from __future__ import annotations

import warnings
from typing import Any

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_string_dtype,
)

from app.schemas import BackendResult


def is_numeric_series(series: pd.Series) -> bool:
    """Return True when a series has numeric dtype."""
    return bool(is_numeric_dtype(series))


def is_datetime_series(series: pd.Series) -> bool:
    """Return True when a series is datetime64 or parseable ISO-like timestamps (CSV round-trips)."""
    if is_datetime64_any_dtype(series):
        return True
    if is_numeric_dtype(series) or is_bool_dtype(series):
        return False
    if is_string_dtype(series) or series.dtype == object:
        sample = series.dropna().head(512)
        if len(sample) == 0:
            return False
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(sample, errors="coerce", utc=False)
        return float(parsed.notna().mean()) >= 0.90
    return False


def build_error_result(message: str, error_code: str = "validation_error") -> BackendResult:
    """Build a normalized error result object."""
    return BackendResult(
        result_type="error",
        value=None,
        table=None,
        chart_data=None,
        message=message,
        error=error_code,
    )


def normalize_result(payload: dict[str, Any]) -> BackendResult:
    """Normalize any backend payload into the canonical BackendResult schema."""
    defaults: dict[str, Any] = {
        "result_type": payload.get("result_type", "table"),
        "value": payload.get("value"),
        "table": payload.get("table"),
        "chart_data": payload.get("chart_data"),
        "message": payload.get("message"),
        "error": payload.get("error"),
    }
    return BackendResult(**defaults)
