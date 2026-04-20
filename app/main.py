"""Streamlit frontend for the CSV Analyst Assistant."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests  # noqa: F401 — kept for parity with project tooling / future HTTP hooks
import streamlit as st

from app.analytics import execute_structured_query
from app.constants import DEFAULT_PREVIEW_ROWS, PROMPT_VARIANTS
from app.llm_router import LLMRouterConfig, parse_question_to_structured_query
from app.schemas import StructuredQuery
from app.validator import validate_structured_query

REPO_ROOT = Path(__file__).resolve().parents[1]

SUPPORTED_DATASETS: list[str] = [
    "online_retail_ii",
    "yellow_tripdata_2026_01",
    "insurance",
]

EXAMPLE_QUESTIONS: list[str] = [
    "What is the average value of sales?",
    "Show total revenue by region.",
    "What is the average charge for smokers?",
    "Show monthly trends of revenue over time.",
    "What is the average charges?",
    "What is the total quantity by country?",
    "What is the average fare_amount where trip_distance > 5?",
    "What is the weekly total fare_amount over time?",
]

# Primary time column per dataset (snake_case, aligned with processed CSVs); None when absent.
_DATASET_META: dict[str, dict[str, Any]] = {
    "online_retail_ii": {"time_column": "invoice_date"},
    "yellow_tripdata_2026_01": {"time_column": "tpep_pickup_datetime"},
    "insurance": {"time_column": None},
}


def _init_state() -> None:
    if "selected_dataset" not in st.session_state:
        st.session_state["selected_dataset"] = SUPPORTED_DATASETS[0]
    if "question_input" not in st.session_state:
        st.session_state["question_input"] = ""


def _render_error(message: str) -> None:
    st.error(message)


def _render_examples() -> None:
    st.subheader("Example questions")
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        if st.button(q, key=f"example_{i}"):
            st.session_state["question_input"] = q
            st.rerun()


def _load_uploaded_csv() -> pd.DataFrame | None:
    """Load selected dataset from processed path, then raw path."""
    dataset_name = st.selectbox("Choose a dataset", SUPPORTED_DATASETS)
    st.session_state["selected_dataset"] = dataset_name

    processed_path = REPO_ROOT / "data" / "processed" / f"{dataset_name}.csv"
    processed_cleaned_path = REPO_ROOT / "data" / "processed" / f"{dataset_name}_cleaned.csv"
    raw_path = REPO_ROOT / "data" / "raw" / f"{dataset_name}.csv"
    candidates = [processed_path, processed_cleaned_path, raw_path]

    chosen_path = next((path for path in candidates if path.exists()), None)
    if chosen_path is None:
        _render_error(f"Dataset file not found for '{dataset_name}'.")
        return None

    try:
        st.caption(f"Source: `{chosen_path.relative_to(REPO_ROOT)}`")
        df = pd.read_csv(chosen_path, low_memory=False)
        time_col = _DATASET_META[dataset_name]["time_column"]
        if time_col and time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        return df
    except Exception:
        _render_error("Could not read the selected dataset file.")
        return None


def _prepare_dataframe_for_query(df: pd.DataFrame, query: StructuredQuery) -> pd.DataFrame:
    """Align dataframe dtypes with the parsed query (time column for ``time_series``)."""
    prepared = df.copy()
    if query.task_type == "time_series" and query.time_column and query.time_column in prepared.columns:
        prepared[query.time_column] = pd.to_datetime(prepared[query.time_column], errors="coerce")
    return prepared


def _llm_router_config_override(model_name: str | None) -> LLMRouterConfig | None:
    if not model_name:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    api_key = os.getenv("OPENAI_API_KEY", "")
    timeout_seconds = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
    return LLMRouterConfig(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        timeout_seconds=timeout_seconds,
    )


def _render_results(result: Any, structured_query: Any) -> None:
    st.markdown("**Structured query**")
    if structured_query is not None:
        st.json(structured_query.model_dump(mode="json") if hasattr(structured_query, "model_dump") else structured_query)
    else:
        st.info("No structured query parsed.")

    st.markdown("**Result**")
    if result is None:
        st.info("No execution result.")
        return

    if getattr(result, "result_type", None) == "error" or getattr(result, "error", None):
        st.error(result.message or result.error or "Execution error")
        return

    rt = getattr(result, "result_type", None)
    if rt == "scalar":
        st.metric("Value", result.value)
    elif rt in ("table", "timeseries") and result.table:
        st.dataframe(pd.DataFrame(result.table), use_container_width=True)
    else:
        st.write(result.model_dump() if hasattr(result, "model_dump") else result)

    if result.chart_data and isinstance(result.chart_data, dict):
        st.markdown("**Chart**")
        figure = result.chart_data.get("figure")
        if figure is not None:
            st.pyplot(figure, use_container_width=True)
            plt.close(figure)
        else:
            st.info("Chart output is missing from the backend response.")


def main() -> None:
    _init_state()

    st.title("CSV Analyst Assistant")
    st.caption("Select a dataset and ask a question in natural language.")
    st.divider()

    st.header("1) Select Dataset")
    df = _load_uploaded_csv()
    if df is None:
        st.info("Select a dataset to begin.")
        return
    if df.empty:
        st.warning("The selected dataset is empty.")
        return

    st.subheader("Dataset Overview")
    st.dataframe(df.head(DEFAULT_PREVIEW_ROWS), use_container_width=True)
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")

    st.divider()
    st.header("2) Ask a question")
    _render_examples()

    prompt_variant = st.selectbox("Prompt variant", list(PROMPT_VARIANTS), index=list(PROMPT_VARIANTS).index("schema_aware"))
    model_name = st.text_input("Model override (optional)", value=os.getenv("OPENAI_MODEL", ""), placeholder="Leave empty for .env default")

    question = st.text_area("Your question", key="question_input", height=100)
    run = st.button("Run query", type="primary")

    if not run:
        return

    if not question.strip():
        _render_error("Please enter a question.")
        return

    dataset_name = st.session_state.get("selected_dataset", SUPPORTED_DATASETS[0])
    config = _llm_router_config_override(model_name.strip() or None)

    structured: StructuredQuery | None = None
    try:
        structured = parse_question_to_structured_query(
            question=question.strip(),
            df=df,
            prompt_variant=prompt_variant,
            config=config,
        )
    except Exception as exc:
        _render_error(f"LLM routing failed: {exc}")
        return

    prepared = _prepare_dataframe_for_query(df, structured)
    valid, validation_errors = validate_structured_query(structured, prepared)
    if not valid:
        st.warning("Validation failed: " + "; ".join(validation_errors))
        _render_results(None, structured)
        return

    try:
        backend_result = execute_structured_query(prepared, structured)
    except Exception as exc:
        _render_error(f"Execution failed: {exc}")
        return

    _render_results(backend_result, structured)


if __name__ == "__main__":
    main()
