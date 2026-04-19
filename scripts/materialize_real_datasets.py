"""Materialize the three course datasets into ``data/raw/*.csv`` for the MVP pipeline.

Reads from local paths (defaults: user Downloads on macOS), applies deterministic
row caps for large sources, and writes canonical CSV names expected by benchmarks:

- ``insurance.csv`` — full file (small).
- ``yellow_tripdata_2026_01.csv`` — first N rows from Parquet (N configurable).
- ``online_retail_ii.csv`` — first N rows from ``online_retail_II.csv`` inside the zip.

Example::

    python scripts/materialize_real_datasets.py \\
      --insurance ~/Downloads/insurance.csv \\
      --yellow-parquet ~/Downloads/yellow_tripdata_2026-01.parquet \\
      --retail-zip ~/Downloads/online_retail_II.csv.zip
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dataset_loader import (  # noqa: E402
    _load_retail_zip_sample,
    _load_yellow_parquet_sample,
)


def _default_downloads() -> Path:
    return Path.home() / "Downloads"


def main() -> None:
    dl = _default_downloads()
    p = argparse.ArgumentParser(description="Write data/raw CSVs for insurance, yellow taxi, retail.")
    p.add_argument("--insurance", type=Path, default=dl / "insurance.csv")
    p.add_argument("--yellow-parquet", type=Path, default=dl / "yellow_tripdata_2026-01.parquet")
    p.add_argument("--retail-zip", type=Path, default=dl / "online_retail_II.csv.zip")
    p.add_argument("--yellow-max-rows", type=int, default=100_000)
    p.add_argument("--retail-max-rows", type=int, default=120_000)
    args = p.parse_args()

    raw = ROOT / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    if not args.insurance.is_file():
        raise SystemExit(f"Insurance CSV not found: {args.insurance}")

    ins = pd.read_csv(args.insurance)
    ins.to_csv(raw / "insurance.csv", index=False)
    print(f"Wrote insurance.csv ({len(ins)} rows)")

    if not args.yellow_parquet.is_file():
        raise SystemExit(f"Yellow Parquet not found: {args.yellow_parquet}")

    y = _load_yellow_parquet_sample(args.yellow_parquet, args.yellow_max_rows)
    y.to_csv(raw / "yellow_tripdata_2026_01.csv", index=False)
    print(f"Wrote yellow_tripdata_2026_01.csv ({len(y)} rows)")

    if not args.retail_zip.is_file():
        raise SystemExit(f"Retail zip not found: {args.retail_zip}")

    r = _load_retail_zip_sample(args.retail_zip, args.retail_max_rows)
    r.to_csv(raw / "online_retail_ii.csv", index=False)
    print(f"Wrote online_retail_ii.csv ({len(r)} rows)")


if __name__ == "__main__":
    main()
