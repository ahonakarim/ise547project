"""Load tabular datasets used by benchmarks, evaluation, and the app.

Resolution order for each logical ``dataset_name``:

1. If ``data/processed/<dataset_name>_cleaned.csv`` exists, load it (normalized
   columns aligned with benchmarks).
2. Else if ``data/raw/<dataset_name>.csv`` exists, load it.
3. Else, if the dataset has optional source environment variables set (see
   ``scripts/materialize_real_datasets.py`` and ``.env.example``), load from
   that source with safe row caps for large files.
"""

from __future__ import annotations

import os
import zipfile
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

_DEFAULT_YELLOW_MAX = 100_000
_DEFAULT_RETAIL_MAX = 120_000

_INNER_RETAIL_CSV = "online_retail_II.csv"


def _load_yellow_parquet_sample(path: Path, max_rows: int) -> pd.DataFrame:
    """Read up to ``max_rows`` rows from the start of a Parquet file (row-group order)."""
    pf = pq.ParquetFile(path)
    chunks: list[pa.Table] = []
    n = 0
    for rg in range(pf.num_row_groups):
        table = pf.read_row_group(rg)
        if n + table.num_rows <= max_rows:
            chunks.append(table)
            n += table.num_rows
        else:
            take = max_rows - n
            if take > 0:
                chunks.append(table.slice(0, take))
            break
    if not chunks:
        return pd.DataFrame()
    return pa.concat_tables(chunks).to_pandas()


def _load_retail_zip_sample(path: Path, max_rows: int) -> pd.DataFrame:
    """Read the first ``max_rows`` lines from ``online_retail_II.csv`` inside the zip."""
    with zipfile.ZipFile(path) as zf:
        with zf.open(_INNER_RETAIL_CSV) as fh:
            return pd.read_csv(
                fh,
                nrows=max_rows,
                parse_dates=["InvoiceDate"],
                dayfirst=True,
                low_memory=False,
            )


def _yellow_max_rows() -> int:
    raw = os.getenv("YELLOW_TRIPDATA_MAX_ROWS", str(_DEFAULT_YELLOW_MAX))
    return max(1, int(raw))


def _retail_max_rows() -> int:
    raw = os.getenv("ONLINE_RETAIL_MAX_ROWS", str(_DEFAULT_RETAIL_MAX))
    return max(1, int(raw))


@lru_cache(maxsize=16)
def load_dataset(dataset_name: str) -> pd.DataFrame:
    """Return a DataFrame for ``dataset_name`` (new load per process; cached in-memory).

    Callers that mutate columns (for example parsing datetimes) should copy
    the frame first.
    """
    name = dataset_name.strip()
    cleaned = PROCESSED_DIR / f"{name}_cleaned.csv"
    if cleaned.is_file():
        return pd.read_csv(cleaned, low_memory=False)
    canonical = RAW_DIR / f"{name}.csv"
    if canonical.exists():
        return pd.read_csv(canonical, low_memory=False)

    if name == "yellow_tripdata_2026_01":
        src = os.getenv("YELLOW_TRIPDATA_PARQUET", "").strip()
        if src and Path(src).is_file():
            return _load_yellow_parquet_sample(Path(src), _yellow_max_rows())
        raise FileNotFoundError(
            f"Dataset '{name}': missing {canonical}. "
            f"Materialize CSV (see scripts/materialize_real_datasets.py) or set "
            f"YELLOW_TRIPDATA_PARQUET to the .parquet file."
        )

    if name == "online_retail_ii":
        src = os.getenv("ONLINE_RETAIL_II_ZIP", "").strip()
        if src and Path(src).is_file():
            return _load_retail_zip_sample(Path(src), _retail_max_rows())
        raise FileNotFoundError(
            f"Dataset '{name}': missing {canonical}. "
            f"Materialize CSV or set ONLINE_RETAIL_II_ZIP to the .zip path."
        )

    if name == "insurance":
        src = os.getenv("INSURANCE_SOURCE_CSV", "").strip()
        if src and Path(src).is_file():
            return pd.read_csv(Path(src), low_memory=False)
        raise FileNotFoundError(
            f"Dataset '{name}': missing {canonical}. "
            f"Copy insurance.csv to data/raw/ or set INSURANCE_SOURCE_CSV."
        )

    raise FileNotFoundError(
        f"No dataset file for '{name}' at {canonical}. "
        f"Run scripts/materialize_real_datasets.py or add data/raw/{name}.csv."
    )


def clear_dataset_cache() -> None:
    """Drop in-process cache (useful in tests)."""
    load_dataset.cache_clear()
