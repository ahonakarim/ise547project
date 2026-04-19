"""Tests for column name normalization."""

from __future__ import annotations

import pandas as pd
import pytest

from app.column_normalization import normalize_column_name, rename_dataframe_columns


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("VendorID", "vendor_id"),
        ("Customer ID", "customer_id"),
        ("InvoiceDate", "invoice_date"),
        ("tpep_pickup_datetime", "tpep_pickup_datetime"),
        ("  RatecodeID ", "ratecode_id"),
        ("PULocationID", "pu_location_id"),
        ("StockCode", "stock_code"),
        ("cbd_congestion_fee", "cbd_congestion_fee"),
    ],
)
def test_normalize_column_name(raw: str, expected: str) -> None:
    assert normalize_column_name(raw) == expected


def test_rename_collision_suffix() -> None:
    df = pd.DataFrame([[1, 2]], columns=["Vendor ID", "Vendor_ID"])
    out = rename_dataframe_columns(df)
    assert list(out.columns) == ["vendor_id", "vendor_id_2"]
