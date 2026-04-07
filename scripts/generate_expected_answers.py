"""Generate expected benchmark outputs using MVP structured-query execution.

This script:
1) loads benchmark rows from data/benchmarks/benchmark_questions.csv
2) loads each row's dataset from data/raw/<dataset_name>.csv
3) converts each row into a StructuredQuery
4) calls execute_structured_query
5) writes reproducible outputs with question_id traceability
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.analytics import execute_structured_query
from app.constants import ERR_EXECUTION, ERR_SCHEMA_VALIDATION
from app.schemas import StructuredQuery
from app.utils import build_error_result

BENCHMARK_PATH = ROOT / "data" / "benchmarks" / "benchmark_questions.csv"
RAW_DATA_DIR = ROOT / "data" / "raw"
OUTPUT_PATH = ROOT / "outputs" / "eval_runs" / "expected_answers.jsonl"


def _parse_filters(raw_filters: str | float | None) -> list[dict[str, Any]]:
    """Parse JSON-encoded filters from benchmark CSV."""
    if raw_filters is None or (isinstance(raw_filters, float) and pd.isna(raw_filters)):
        return []
    text = str(raw_filters).strip()
    if not text:
        return []
    return json.loads(text)


def _maybe_none(value: Any) -> Any:
    """Convert NaN-like values from pandas rows into None."""
    if pd.isna(value):
        return None
    return value


def _query_from_row(row: pd.Series) -> StructuredQuery:
    """Build StructuredQuery from one benchmark CSV row."""
    payload: dict[str, Any] = {
        "task_type": row["task_type"],
        "metric_column": _maybe_none(row["metric_column"]),
        "aggregation": _maybe_none(row["aggregation"]),
        "groupby_column": _maybe_none(row["groupby_column"]),
        "filters": _parse_filters(_maybe_none(row["filters"])),
        "time_column": _maybe_none(row["time_column"]),
        "time_granularity": _maybe_none(row["time_granularity"]),
        "chart_type": _maybe_none(row["expected_chart_type"]) or "none",
    }
    return StructuredQuery(**payload)


def _sanitize_result_for_json(result: dict[str, Any]) -> dict[str, Any]:
    """Remove non-serializable chart objects and normalize payload.

    If a matplotlib figure is present, close it during batch generation to
    prevent accumulation of open figures in long runs.
    """
    chart_data = result.get("chart_data")
    if isinstance(chart_data, dict) and "figure" in chart_data:
        figure_obj = chart_data.get("figure")
        if figure_obj is not None:
            plt.close(figure_obj)
        chart_data = {k: v for k, v in chart_data.items() if k != "figure"}
    result["chart_data"] = chart_data
    return result


def _load_dataset(dataset_name: str) -> pd.DataFrame:
    """Load dataset CSV from data/raw using dataset_name convention."""
    dataset_path = RAW_DATA_DIR / f"{dataset_name}.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found for dataset_name='{dataset_name}': {dataset_path}")
    return pd.read_csv(dataset_path)


def _prepare_dataframe_for_row(df: pd.DataFrame, row: pd.Series) -> pd.DataFrame:
    """Apply row-specific deterministic preprocessing for execution.

    For time_series rows, convert the declared time column to datetime so
    resampling receives a DatetimeIndex-compatible column.
    """
    prepared = df.copy()
    task_type = str(row["task_type"])
    if task_type != "time_series":
        return prepared

    time_col = _maybe_none(row["time_column"])
    if not time_col:
        return prepared

    time_format = _maybe_none(row.get("time_column_format"))
    if time_format in {None, "", "iso_date"}:
        prepared[time_col] = pd.to_datetime(prepared[time_col], errors="coerce")
    else:
        prepared[time_col] = pd.to_datetime(prepared[time_col], errors="coerce")
    return prepared


def main() -> None:
    """Generate expected answers JSONL for benchmark rows."""
    benchmark_df = pd.read_csv(BENCHMARK_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for _, row in benchmark_df.iterrows():
        question_id = str(row["question_id"])
        dataset_name = str(row["dataset_name"])
        question_text = str(row["question_text"])
        structured_query_payload: dict[str, Any] | None = None

        try:
            df = _prepare_dataframe_for_row(_load_dataset(dataset_name), row)
            query = _query_from_row(row)
            structured_query_payload = query.model_dump()
            result = execute_structured_query(df, query)
        except Exception as exc:  # pragma: no cover - defensive path
            # Keep failure rows reproducible and traceable for evaluation diagnostics.
            err_code = ERR_SCHEMA_VALIDATION if "validation" in str(exc).lower() else ERR_EXECUTION
            result = build_error_result(message=str(exc), error_code=err_code)

        result_payload = _sanitize_result_for_json(result.model_dump())
        records.append(
            {
                "question_id": question_id,
                "dataset_name": dataset_name,
                "question_text": question_text,
                "structured_query": structured_query_payload,
                "expected_result": result_payload,
            }
        )

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=True, default=str) + "\n")

    print(f"Wrote {len(records)} expected outputs to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
