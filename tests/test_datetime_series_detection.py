"""Tests for datetime-like detection on string timestamps (processed CSV round-trips)."""

from __future__ import annotations

import pandas as pd

from app.utils import is_datetime_series


def test_is_datetime_series_accepts_iso_strings() -> None:
    s = pd.Series(["2026-01-01 00:54:04", "2026-01-02 01:00:00", None])
    assert is_datetime_series(s) is True


def test_is_datetime_series_rejects_plain_integers() -> None:
    s = pd.Series([0, 1, 2, 3, 4])
    assert is_datetime_series(s) is False
