"""Tests for ``app.dataset_loader``."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.dataset_loader import clear_dataset_cache, load_dataset

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def test_load_dataset_sales_data_when_csv_present() -> None:
    """Synthetic course CSVs remain loadable via canonical path."""
    p = RAW / "sales_data.csv"
    if not p.is_file():
        pytest.skip("data/raw/sales_data.csv not present")
    clear_dataset_cache()
    df = load_dataset("sales_data")
    assert len(df) > 0
    assert "order_date" in df.columns


def test_load_insurance_when_materialized() -> None:
    p = RAW / "insurance.csv"
    if not p.is_file():
        pytest.skip("data/raw/insurance.csv not present (run materialize_real_datasets.py)")
    clear_dataset_cache()
    df = load_dataset("insurance")
    assert set(df.columns) >= {"age", "charges", "smoker", "region"}
    assert len(df) >= 1000
