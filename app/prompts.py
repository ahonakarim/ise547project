"""Prompt templates for structured query extraction (MVP scope)."""

from __future__ import annotations

import json

from app.constants import AGGREGATIONS, CHART_TYPES, FILTER_OPERATORS, TASK_TYPES, TIME_GRANULARITIES


def _schema_block() -> str:
    """Return a compact schema contract block shared across variants."""
    return (
        "Return ONLY valid JSON (no markdown, no explanation) with this schema:\n"
        "{\n"
        '  "task_type": string,\n'
        '  "metric_column": string | null,\n'
        '  "aggregation": string | null,\n'
        '  "groupby_column": string | null,\n'
        '  "filters": [{"column": string, "operator": string, "value": any}] ,\n'
        '  "time_column": string | null,\n'
        '  "time_granularity": string | null,\n'
        '  "chart_type": string,\n'
        '  "chart_title": string | null\n'
        "}\n"
        f"Allowed task_type: {list(TASK_TYPES)}\n"
        f"Allowed aggregation: {list(AGGREGATIONS)}\n"
        f"Allowed filters.operator: {list(FILTER_OPERATORS)}\n"
        f"Allowed time_granularity: {list(TIME_GRANULARITIES)}\n"
        f"Allowed chart_type: {list(CHART_TYPES)}\n"
    )


def _few_shot_examples() -> str:
    """Return concise in-scope few-shot examples."""
    ex1 = {
        "task_type": "summary_stat",
        "metric_column": "sales",
        "aggregation": "mean",
        "groupby_column": None,
        "filters": [],
        "time_column": None,
        "time_granularity": None,
        "chart_type": "none",
        "chart_title": None,
    }
    ex2 = {
        "task_type": "grouped_aggregation",
        "metric_column": "charges",
        "aggregation": "mean",
        "groupby_column": "smoker",
        "filters": [],
        "time_column": None,
        "time_granularity": None,
        "chart_type": "bar",
        "chart_title": None,
    }
    ex3 = {
        "task_type": "time_series",
        "metric_column": "order_value",
        "aggregation": "sum",
        "groupby_column": None,
        "filters": [],
        "time_column": "order_date",
        "time_granularity": "month",
        "chart_type": "line",
        "chart_title": None,
    }
    return (
        "Example 1\n"
        "Question: What is the average sales amount?\n"
        f"JSON: {json.dumps(ex1)}\n\n"
        "Example 2\n"
        "Question: Show average charges by smoker status.\n"
        f"JSON: {json.dumps(ex2)}\n\n"
        "Example 3\n"
        "Question: Show monthly order value trend.\n"
        f"JSON: {json.dumps(ex3)}\n"
    )


def build_prompt(
    *,
    question: str,
    schema_context: str,
    prompt_variant: str,
) -> str:
    """Build a full prompt for one of the 4 MVP variants."""
    variant = prompt_variant.strip().lower()
    base = (
        "You are an intent parser for CSV analytics.\n"
        "Convert the user's question into a structured query within MVP scope only.\n"
        "MVP scope task types: summary_stat, grouped_aggregation, filtered_aggregation, time_series.\n"
        f"Dataset schema context:\n{schema_context}\n\n"
    )

    schema = _schema_block()
    user = f"User question: {question}\n"

    if variant == "minimal":
        return base + user + "\n" + schema

    if variant == "schema_aware":
        return (
            base
            + "Use column names exactly as provided in schema context.\n"
            + "Do not invent columns, operators, or task types.\n"
            + user
            + "\n"
            + schema
        )

    if variant == "few_shot":
        return base + _few_shot_examples() + "\n" + user + "\n" + schema

    if variant == "strict_anti_hallucination":
        return (
            base
            + "Strict rules:\n"
            + "- Never invent columns.\n"
            + "- If uncertain, prefer an in-scope best guess using existing columns.\n"
            + "- Keep output parseable JSON only.\n"
            + "- Do not output markdown.\n"
            + user
            + "\n"
            + schema
        )

    raise ValueError(f"Unsupported prompt variant: {prompt_variant}")
