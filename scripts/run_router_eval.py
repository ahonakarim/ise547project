"""Run router-level evaluation against benchmark gold structured fields."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dataset_loader import load_dataset
from app.llm_router import LLMRouterConfig, parse_question_to_structured_query

DEFAULT_BENCHMARK_PATH = ROOT / "data" / "benchmarks" / "benchmark_questions.csv"
DEFAULT_OUTPUT_PATH = ROOT / "outputs" / "eval_runs" / "router_eval_results.csv"


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
    df = load_dataset(dataset_name).copy()
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


def _exact_match_from_applicable(
    gold_task: str,
    *,
    task_type_correct: bool,
    metric_column_correct: bool,
    aggregation_correct: bool,
    chart_type_correct: bool,
    groupby_column_correct: Any,
    filter_correct: Any,
    time_column_correct: Any,
    time_granularity_correct: Any,
) -> bool:
    """True iff every field that applies to ``gold_task`` matches."""
    parts: list[bool] = [
        task_type_correct,
        metric_column_correct,
        aggregation_correct,
        chart_type_correct,
    ]
    if gold_task == "grouped_aggregation":
        parts.append(groupby_column_correct)
    if gold_task == "filtered_aggregation":
        parts.append(filter_correct)
    if gold_task == "time_series":
        parts.append(time_column_correct)
        parts.append(time_granularity_correct)
    return all(parts)


def run_eval(
    model_name: str,
    prompt_variant: str,
    limit: int | None,
    benchmark_path: Path | None = None,
    sleep_seconds: float = 3.0,
) -> pd.DataFrame:
    bench_path = benchmark_path or DEFAULT_BENCHMARK_PATH
    bench = pd.read_csv(bench_path)
    if limit is not None:
        bench = bench.head(limit)

    config = _router_config_with_model(model_name)
    rows: list[dict[str, Any]] = []

    for _, row in bench.iterrows():
        question_id = str(row["question_id"])
        dataset_name = str(row["dataset_name"])
        question_text = str(row["question_text"])
        gold_task = str(row["task_type"])

        parse_success = False
        error_message = ""
        task_type_correct = False
        metric_column_correct = False
        aggregation_correct = False
        groupby_column_correct: bool | Any = pd.NA
        filter_correct: bool | Any = pd.NA
        time_column_correct: bool | Any = pd.NA
        time_granularity_correct: bool | Any = pd.NA
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
            chart_type_correct = pred.chart_type == gold_chart

            if gold_task == "grouped_aggregation":
                groupby_column_correct = pred.groupby_column == gold_group
            else:
                groupby_column_correct = pd.NA

            if gold_task == "filtered_aggregation":
                filter_correct = pred_filters == gold_filters
            else:
                filter_correct = pd.NA

            if gold_task == "time_series":
                time_column_correct = pred.time_column == gold_time_col
                time_granularity_correct = pred.time_granularity == gold_time_gran
            else:
                time_column_correct = pd.NA
                time_granularity_correct = pd.NA

            exact_match = _exact_match_from_applicable(
                gold_task,
                task_type_correct=task_type_correct,
                metric_column_correct=metric_column_correct,
                aggregation_correct=aggregation_correct,
                chart_type_correct=chart_type_correct,
                groupby_column_correct=groupby_column_correct,
                filter_correct=filter_correct,
                time_column_correct=time_column_correct,
                time_granularity_correct=time_granularity_correct,
            )
        except Exception as exc:  # pragma: no cover - runtime/API dependent
            error_message = str(exc)
            task_type_correct = False
            metric_column_correct = False
            aggregation_correct = False
            chart_type_correct = False
            exact_match = False
            if gold_task == "grouped_aggregation":
                groupby_column_correct = False
            else:
                groupby_column_correct = pd.NA
            if gold_task == "filtered_aggregation":
                filter_correct = False
            else:
                filter_correct = pd.NA
            if gold_task == "time_series":
                time_column_correct = False
                time_granularity_correct = False
            else:
                time_column_correct = pd.NA
                time_granularity_correct = pd.NA

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
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

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
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=None,
        help="Benchmark CSV (default: data/benchmarks/benchmark_questions.csv).",
    )
    parser.add_argument(
        "--sleep_seconds",
        type=float,
        default=3.0,
        help="Seconds to sleep between benchmark rows (after each API call) for rate-limit safety.",
    )
    parser.add_argument(
        "--output_path",
        type=Path,
        default=None,
        help="Optional CSV path for results (default: outputs/eval_runs/router_eval_results.csv).",
    )
    args = parser.parse_args()

    results_df = run_eval(
        model_name=args.model,
        prompt_variant=args.prompt_variant,
        limit=args.limit,
        benchmark_path=args.benchmark,
        sleep_seconds=args.sleep_seconds,
    )
    output_path = args.output_path or DEFAULT_OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"Wrote {len(results_df)} rows to {output_path}")


if __name__ == "__main__":
    main()
