"""Streamlit frontend for the CSV Analyst Assistant."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Streamlit Cloud runs `app/main.py`; the repo root must be on sys.path for `from app.*` imports.
REPO_ROOT = Path(__file__).resolve().parent.parent
_root = str(REPO_ROOT)
if _root not in sys.path:
    sys.path.insert(0, _root)

import matplotlib.pyplot as plt
import pandas as pd
import requests  # noqa: F401 — kept for parity with project tooling / future HTTP hooks
import streamlit as st

from app.analytics import execute_structured_query
from app.constants import DEFAULT_PREVIEW_ROWS
from app.dataset_loader import load_dataset
from app.llm_router import parse_question_to_structured_query
from app.schemas import StructuredQuery
from app.validator import validate_structured_query

SUPPORTED_DATASETS: list[str] = [
    "online_retail_ii",
    "yellow_tripdata_2026_01",
    "insurance",
]

_BENCHMARK_QUESTIONS_CSV = REPO_ROOT / "data" / "benchmarks" / "benchmark_questions.csv"
DEFAULT_PROMPT_VARIANT = "few_shot"

# Five benchmark IDs per dataset: summary, grouped, filtered, time-series (where applicable), + one extra variety.
_EXAMPLE_QUESTION_IDS_BY_DATASET: dict[str, tuple[str, ...]] = {
    "online_retail_ii": ("Q001", "Q011", "Q021", "Q031", "Q033"),
    "yellow_tripdata_2026_01": ("Q041", "Q053", "Q065", "Q076", "Q080"),
    "insurance": ("Q086", "Q096", "Q097", "Q106", "Q107"),
}

_MSG_QUESTION_NOT_FOR_DATASET = (
    "**Oops — that doesn’t quite fit this dataset.** "
    "Ask about columns you see in the preview above, or pick an example question for this data."
)

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


@st.cache_data(show_spinner=False)
def _load_benchmark_question_rows() -> pd.DataFrame:
    """All benchmark rows (sorted by numeric question id)."""
    if not _BENCHMARK_QUESTIONS_CSV.is_file():
        return pd.DataFrame(columns=["question_id", "dataset_name", "question_text"])
    df = pd.read_csv(
        _BENCHMARK_QUESTIONS_CSV,
        usecols=["question_id", "dataset_name", "question_text"],
    )
    df["_ord"] = df["question_id"].astype(str).str.replace("Q", "", regex=False).astype(int)
    return df.sort_values("_ord", kind="stable").drop(columns=["_ord"])


def _example_questions_for_dataset(dataset_name: str) -> list[tuple[str, str]]:
    """Up to five (question_id, question_text) pairs: curated benchmark IDs for UI variety."""
    wanted = _EXAMPLE_QUESTION_IDS_BY_DATASET.get(dataset_name)
    if not wanted:
        return []
    df = _load_benchmark_question_rows()
    if df.empty:
        return []
    sub = df[df["dataset_name"] == dataset_name]
    by_id = dict(zip(sub["question_id"].astype(str), sub["question_text"].astype(str)))
    return [(qid, by_id[qid]) for qid in wanted if qid in by_id]


def _render_examples(dataset_name: str) -> None:
    st.subheader("Example questions")
    rows = _example_questions_for_dataset(dataset_name)
    if not rows:
        st.caption(
            f"No benchmark rows for `{dataset_name}` in `{_BENCHMARK_QUESTIONS_CSV.relative_to(REPO_ROOT)}`."
        )
        return
    st.caption(
        f"{len(rows)} curated examples from **{dataset_name}** in `benchmark_questions.csv` "
        "(summary, grouped, filtered" + (", time series" if dataset_name != "insurance" else "") + ")."
    )
    for qid, qtext in rows:
        label = f"{qid}: {qtext}"
        if st.button(label, key=f"example_{dataset_name}_{qid}"):
            st.session_state["question_input"] = qtext
            st.rerun()


def _load_selected_dataset() -> pd.DataFrame | None:
    """Load the selected dataset using the same resolution rules as ``dataset_loader.load_dataset``."""
    dataset_name = st.selectbox("Choose a dataset", SUPPORTED_DATASETS)
    st.session_state["selected_dataset"] = dataset_name

    try:
        df = load_dataset(dataset_name).copy()
    except FileNotFoundError as exc:
        _render_error(str(exc))
        return None
    except Exception:
        _render_error("Could not load the selected dataset.")
        return None

    st.caption(
        "Resolution order: `data/processed/<id>_cleaned.csv` → `data/raw/<id>.csv` → "
        "optional `.env` paths for large sources (see README / `.env.example`)."
    )
    try:
        time_col = _DATASET_META[dataset_name]["time_column"]
        if time_col and time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        return df
    except Exception:
        _render_error("Could not prepare the selected dataset.")
        return None


def _prepare_dataframe_for_query(df: pd.DataFrame, query: StructuredQuery) -> pd.DataFrame:
    """Align dataframe dtypes with the parsed query (time column for ``time_series``)."""
    prepared = df.copy()
    if query.task_type == "time_series" and query.time_column and query.time_column in prepared.columns:
        prepared[query.time_column] = pd.to_datetime(prepared[query.time_column], errors="coerce")
    return prepared


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
        detail = result.message or result.error or "Execution error"
        st.warning(_MSG_QUESTION_NOT_FOR_DATASET)
        st.error(detail)
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
    df = _load_selected_dataset()
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
    _render_examples(st.session_state.get("selected_dataset", SUPPORTED_DATASETS[0]))

    question = st.text_area("Your question", key="question_input", height=100)
    run = st.button("Run query", type="primary")

    if not run:
        return

    if not question.strip():
        _render_error("Please enter a question.")
        return

    structured: StructuredQuery | None = None
    try:
        structured = parse_question_to_structured_query(
            question=question.strip(),
            df=df,
            prompt_variant=DEFAULT_PROMPT_VARIANT,
        )
    except Exception as exc:
        st.warning(
            "**We couldn’t turn that into a structured query.** "
            "If it’s off-topic for this table, switch datasets or rephrase; otherwise check your LLM API key and network."
        )
        with st.expander("Technical details"):
            st.code(str(exc))
        return

    prepared = _prepare_dataframe_for_query(df, structured)
    valid, validation_errors = validate_structured_query(structured, prepared)
    if not valid:
        st.warning(_MSG_QUESTION_NOT_FOR_DATASET)
        with st.expander("What didn’t match"):
            st.text("; ".join(validation_errors))
        _render_results(None, structured)
        return

    try:
        backend_result = execute_structured_query(prepared, structured)
    except Exception as exc:
        st.warning(_MSG_QUESTION_NOT_FOR_DATASET)
        with st.expander("Technical details"):
            st.code(str(exc))
        return

    _render_results(backend_result, structured)


if __name__ == "__main__":
    main()
