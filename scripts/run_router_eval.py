"""Run router-level evaluation against benchmark gold structured fields."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm_router import LLMRouterConfig, parse_question_to_structured_query

BENCHMARK_PATH = ROOT / "data" / "benchmarks" / "benchmark_questions.csv"
RAW_DATA_DIR = ROOT / "data" / "raw"
OUTPUT_PATH = ROOT / "outputs" / "eval_runs" / "router_eval_results.csv"


def _maybe_none(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def _parse_gold_filters(raw_filters: Any) -> list[dict[str, Any]]:
    if raw_filters is None:
        return []
    text = str(raw_filters).strip()
    if text == "" or text.lower() == "nan":
        return []
    return json.loads(text)


def _normalize_filters(filters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize filters for deterministic comparison."""
    normalized: list[dict[str, Any]] = []
    for f in filters:
        normalized.append(
            {
                "column": f.get("column"),
                "operator": f.get("operator"),
                "value": f.get("value"),
            }
        )
    normalized.sort(key=lambda x: (str(x["column"]), str(x["operator"]), str(x["value"])))
    return normalized


def _load_dataset_for_row(row: pd.Series) -> pd.DataFrame:
    dataset_name = str(row["dataset_name"])
    dataset_path = RAW_DATA_DIR / f"{dataset_name}.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    task_type = str(row["task_type"])
    if task_type == "time_series":
        time_col = _maybe_none(row.get("time_column"))
        if time_col and time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    return df


def _router_config_with_model(model_name: str) -> LLMRouterConfig:
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    api_key = os.getenv("OPENAI_API_KEY", "")
    timeout = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
    return LLMRouterConfig(base_url=base_url, api_key=api_key, model=model_name, timeout_seconds=timeout)


def run_eval(model_name: str, prompt_variant: str, limit: int | None) -> pd.DataFrame:
    bench = pd.read_csv(BENCHMARK_PATH)
    if limit is not None:
        bench = bench.head(limit)

    config = _router_config_with_model(model_name)
    rows: list[dict[str, Any]] = []

    for _, row in bench.iterrows():
        question_id = str(row["question_id"])
        dataset_name = str(row["dataset_name"])
        question_text = str(row["question_text"])

        parse_success = False
        error_message = ""
        task_type_correct = False
        metric_column_correct = False
        aggregation_correct = False
        groupby_column_correct = False
        filter_correct = False
        time_column_correct = False
        time_granularity_correct = False
        chart_type_correct = False
        exact_match = False

        try:
            df = _load_dataset_for_row(row)
            pred = parse_question_to_structured_query(
                question=question_text,
                df=df,
                prompt_variant=prompt_variant,
                config=config,
            )
            parse_success = True

            gold_task = str(row["task_type"])
            gold_metric = _maybe_none(row["metric_column"])
            gold_agg = _maybe_none(row["aggregation"])
            gold_group = _maybe_none(row["groupby_column"])
            gold_time_col = _maybe_none(row["time_column"])
            gold_time_gran = _maybe_none(row["time_granularity"])
            gold_chart = _maybe_none(row["expected_chart_type"])
            gold_filters = _normalize_filters(_parse_gold_filters(_maybe_none(row["filters"])))
            pred_filters = _normalize_filters([f.model_dump() for f in pred.filters])

            task_type_correct = pred.task_type == gold_task
            metric_column_correct = pred.metric_column == gold_metric
            aggregation_correct = pred.aggregation == gold_agg
            groupby_column_correct = pred.groupby_column == gold_group
            filter_correct = pred_filters == gold_filters
            time_column_correct = pred.time_column == gold_time_col
            time_granularity_correct = pred.time_granularity == gold_time_gran
            chart_type_correct = pred.chart_type == gold_chart

            exact_match = all(
                [
                    task_type_correct,
                    metric_column_correct,
                    aggregation_correct,
                    groupby_column_correct,
                    filter_correct,
                    time_column_correct,
                    time_granularity_correct,
                    chart_type_correct,
                ]
            )
        except Exception as exc:  # pragma: no cover - runtime/API dependent
            error_message = str(exc)

        rows.append(
            {
                "question_id": question_id,
                "dataset_name": dataset_name,
                "model_name": model_name,
                "prompt_variant": prompt_variant,
                "parse_success": parse_success,
                "task_type_correct": task_type_correct,
                "metric_column_correct": metric_column_correct,
                "aggregation_correct": aggregation_correct,
                "groupby_column_correct": groupby_column_correct,
                "filter_correct": filter_correct,
                "time_column_correct": time_column_correct,
                "time_granularity_correct": time_granularity_correct,
                "chart_type_correct": chart_type_correct,
                "exact_match": exact_match,
                "error_message": error_message,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run router evaluation against benchmark.")
    parser.add_argument("--model", required=True, help="Model name for OpenAI-compatible API.")
    parser.add_argument(
        "--prompt_variant",
        required=True,
        choices=["minimal", "schema_aware", "few_shot", "strict_anti_hallucination"],
        help="Prompt variant id.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for quick runs.")
    args = parser.parse_args()

    results_df = run_eval(model_name=args.model, prompt_variant=args.prompt_variant, limit=args.limit)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(results_df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
