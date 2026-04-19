"""Read ``data/raw/*.csv``, normalize columns, coerce primary time, write ``data/processed/*_cleaned.csv``.

Does not modify files under ``data/raw/``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dataset_processing import (  # noqa: E402
    PROCESSED_DIR,
    process_dataframe,
    save_processed_csv,
    write_schema_manifest,
)

# Optional explicit primary time column (raw or normalized name — normalized after rename).
_DEFAULT_TIME_OVERRIDES: dict[str, str | None] = {
    "insurance": None,
    "yellow_tripdata_2026_01": "tpep_pickup_datetime",
    "online_retail_ii": "InvoiceDate",
}


def _stem(dataset_id: str) -> str:
    return dataset_id.replace(".csv", "").strip()


def process_one(
    raw_csv: Path,
    dataset_id: str,
    time_override: str | None,
) -> dict[str, Any]:
    if not raw_csv.is_file():
        raise FileNotFoundError(raw_csv)
    df = pd.read_csv(raw_csv, low_memory=False)
    cleaned, time_col, schema = process_dataframe(df, primary_time_override=time_override)
    out_path = PROCESSED_DIR / f"{_stem(dataset_id)}_cleaned.csv"
    save_processed_csv(cleaned, out_path)
    return {
        "dataset_id": _stem(dataset_id),
        "source_csv": str(raw_csv.relative_to(ROOT)),
        "output_csv": str(out_path.relative_to(ROOT)),
        "row_count": int(len(cleaned)),
        "primary_time_column": time_col,
        "schema": schema,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize columns and write data/processed/*_cleaned.csv")
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=["insurance", "yellow_tripdata_2026_01", "online_retail_ii"],
        help="Dataset ids matching data/raw/<id>.csv",
    )
    args = parser.parse_args()

    manifest: dict[str, Any] = {"datasets": {}}
    for ds in args.datasets:
        stem = _stem(ds)
        raw_path = ROOT / "data" / "raw" / f"{stem}.csv"
        override = _DEFAULT_TIME_OVERRIDES.get(stem)
        info = process_one(raw_path, stem, override)
        manifest["datasets"][stem] = info

    path = write_schema_manifest(manifest)
    print(f"Wrote manifest to {path}")
    for stem, info in manifest["datasets"].items():
        print(f"\n=== {stem} ===")
        print("primary_time_column:", info["primary_time_column"])
        print("rows:", info["row_count"])
        for col in info["schema"]:
            print(f"  {col['column']}: {col['dtype']}")


if __name__ == "__main__":
    main()
