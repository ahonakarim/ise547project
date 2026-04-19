"""FastAPI application for the CSV Analyst Assistant backend.

Exposes health, dataset metadata, and POST ``/query`` (NL → structured query → validate → execute).

Local dev (from the repository root; does not auto-start when importing this module)::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import json
import math
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np

import matplotlib.pyplot as plt
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.analytics import execute_structured_query
from app.constants import PROMPT_VARIANTS
from app.llm_router import LLMRouterConfig, parse_question_to_structured_query
from app.schemas import BackendResult, StructuredQuery
from app.validator import validate_structured_query

ROOT = Path(__file__).resolve().parents[1]

SUPPORTED_DATASET_NAMES: tuple[str, ...] = (
    "online_retail_ii",
    "yellow_tripdata_2026_01",
    "insurance",
)

# Primary time column per dataset (snake_case, aligned with processed CSVs); None when absent.
_DATASET_META: dict[str, dict[str, Any]] = {
    "online_retail_ii": {"time_column": "invoice_date"},
    "yellow_tripdata_2026_01": {"time_column": "tpep_pickup_datetime"},
    "insurance": {"time_column": None},
}


def resolve_dataset_csv_path(dataset_name: str) -> Path:
    """Resolve the on-disk CSV path for a supported ``dataset_name``.

    Tries paths in order (first existing file wins):

    1. ``data/processed/<dataset_name>.csv``
    2. ``data/processed/<dataset_name>_cleaned.csv`` (materialized processed layout)
    3. ``data/raw/<dataset_name>.csv``

    Raises:
        ValueError: if ``dataset_name`` is not supported.
        FileNotFoundError: if no candidate file exists.
    """
    if dataset_name not in SUPPORTED_DATASET_NAMES:
        raise ValueError(
            f"dataset_name must be one of {list(SUPPORTED_DATASET_NAMES)}, got {dataset_name!r}"
        )
    candidates = [
        ROOT / "data" / "processed" / f"{dataset_name}.csv",
        ROOT / "data" / "processed" / f"{dataset_name}_cleaned.csv",
        ROOT / "data" / "raw" / f"{dataset_name}.csv",
    ]
    for path in candidates:
        if path.is_file():
            return path
    tried = ", ".join(p.relative_to(ROOT).as_posix() for p in candidates)
    raise FileNotFoundError(f"No CSV found for dataset {dataset_name!r}; tried: {tried}")


def load_dataset_frame(dataset_name: str) -> pd.DataFrame:
    """Load a supported dataset from disk and apply minimal preprocessing.

    Reads the CSV resolved by :func:`resolve_dataset_csv_path`. If the registry
    declares a ``time_column`` for this dataset, that column is parsed with
    ``pandas.to_datetime(..., errors="coerce")`` for deterministic downstream use.

    Raises:
        ValueError: unsupported ``dataset_name``.
        FileNotFoundError: missing CSV file.
    """
    path = resolve_dataset_csv_path(dataset_name)
    df = pd.read_csv(path, low_memory=False)
    time_col = _DATASET_META[dataset_name]["time_column"]
    if time_col and time_col in df.columns:
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    return df


def _llm_router_config_override(model_name: str | None) -> LLMRouterConfig | None:
    """Build router config when ``model_name`` is set; otherwise router uses env defaults."""
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


def _prepare_dataframe_for_query(df: pd.DataFrame, query: StructuredQuery) -> pd.DataFrame:
    """Align dataframe dtypes with the parsed query (time column for ``time_series``)."""
    prepared = df.copy()
    if query.task_type == "time_series" and query.time_column and query.time_column in prepared.columns:
        prepared[query.time_column] = pd.to_datetime(prepared[query.time_column], errors="coerce")
    return prepared


def _sanitize_chart_data_for_json(chart_data: Any) -> dict[str, Any] | None:
    """API-only: normalize ``chart_data`` for JSON (figures → null, close figures)."""

    try:
        from matplotlib.figure import Figure
    except ImportError:  # pragma: no cover
        Figure = ()

    def walk(value: Any) -> Any:
        if isinstance(value, Figure):
            plt.close(value)
            return None
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(item) for item in value]
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, (str, int, float)):
            return value
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            try:
                encoded = jsonable_encoder(value)
            except (TypeError, ValueError):
                return None
            try:
                json.dumps(encoded)
                return encoded
            except (TypeError, ValueError):
                return None

    if chart_data is None:
        return None
    if not isinstance(chart_data, dict):
        return None
    return walk(chart_data)


def _coerce_execution_fields_for_json(value: Any) -> Any:
    """Normalize ``value`` / ``table`` cell values for JSON (NumPy scalars, NaT, datetimes).

    Used only by the API layer; does not change analytics outputs before dump.
    """
    if isinstance(value, dict):
        return {k: _coerce_execution_fields_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_execution_fields_for_json(v) for v in value]
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        out = value.item()
        if isinstance(out, float) and (math.isnan(out) or math.isinf(out)):
            return None
        return out
    if isinstance(value, np.ndarray):
        return _coerce_execution_fields_for_json(value.tolist())
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    try:
        if isinstance(value, (float, int)) and pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def execution_result_dict_json_safe(result: BackendResult | dict[str, Any]) -> dict[str, Any]:
    """Convert execution output to a JSON-safe dict for HTTP responses only.

    Matplotlib figures and other non-JSON values under ``chart_data`` become ``null``.
    ``value``, ``table``, ``message``, and ``error`` keep the same ``BackendResult``
    shape; NumPy/pandas scalars in ``value``/``table`` are coerced to plain JSON
    types without touching :mod:`app.analytics` behavior.
    """
    payload: dict[str, Any] = (
        result.model_dump() if isinstance(result, BackendResult) else dict(result)
    )
    payload["chart_data"] = _sanitize_chart_data_for_json(payload.get("chart_data"))
    for key in ("value", "table"):
        if key in payload:
            payload[key] = _coerce_execution_fields_for_json(payload[key])
    normalized = BackendResult.model_validate(payload)
    return normalized.model_dump(mode="json")


def _dataset_registry_entry(dataset_name: str) -> dict[str, Any]:
    """Build one registry row: stable path string relative to repo root."""
    path = resolve_dataset_csv_path(dataset_name)
    rel = path.relative_to(ROOT)
    meta = _DATASET_META[dataset_name]
    return {
        "name": dataset_name,
        "file_path": rel.as_posix(),
        "time_column": meta["time_column"],
    }


class DatasetItem(BaseModel):
    """One supported dataset with resolved file path and optional time column."""

    name: str = Field(..., description="Logical dataset id used by benchmarks and loaders.")
    file_path: str = Field(
        ...,
        description="CSV path relative to repo root (processed cleaned file if it exists).",
    )
    time_column: str | None = Field(
        None,
        description="Primary datetime column for time_series tasks, if any.",
    )


class DatasetsResponse(BaseModel):
    """Response for GET /datasets."""

    dataset_names: list[str] = Field(..., description="Supported dataset identifiers.")
    datasets: list[DatasetItem] = Field(..., description="Registry entries per dataset.")


class QueryRequest(BaseModel):
    """Request body for POST ``/query``.

    Maps to router input (``dataset_name``, ``question``, ``prompt_variant``,
    optional ``model_name``) and downstream ``StructuredQuery`` validation.
    """

    dataset_name: str = Field(..., description="Logical dataset id (must be in ``SUPPORTED_DATASET_NAMES``).")
    question: str = Field(..., min_length=1, description="Natural-language question about the dataset.")
    prompt_variant: str = Field(
        default="schema_aware",
        description="Router prompt id; must be one of ``app.constants.PROMPT_VARIANTS``.",
    )
    model_name: str | None = Field(
        default=None,
        description="Optional OpenAI-compatible model id; when omitted, router uses environment defaults.",
    )

    @field_validator("dataset_name")
    @classmethod
    def _dataset_must_be_supported(cls, value: str) -> str:
        if value not in SUPPORTED_DATASET_NAMES:
            raise ValueError(f"dataset_name must be one of {list(SUPPORTED_DATASET_NAMES)}, got {value!r}")
        return value

    @field_validator("prompt_variant")
    @classmethod
    def _prompt_variant_must_be_known(cls, value: str) -> str:
        if value not in PROMPT_VARIANTS:
            raise ValueError(f"prompt_variant must be one of {list(PROMPT_VARIANTS)}, got {value!r}")
        return value


class QueryResponse(BaseModel):
    """Unified response after parse → validate → execute (POST ``/query``).

    ``structured_query`` uses ``StructuredQuery.model_dump(mode="json")`` when parsing succeeds.
    ``result`` uses the JSON-safe execution shape from :func:`execution_result_dict_json_safe`.
    ``validation_errors`` lists messages from ``validate_structured_query``.
    """

    dataset_name: str = Field(..., description="Dataset that was queried.")
    question: str = Field(..., description="Original natural-language question.")
    structured_query: dict[str, Any] | None = Field(
        default=None,
        description="Parsed structured intent (``StructuredQuery`` as JSON-compatible dict).",
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Messages from ``validate_structured_query`` when invalid.",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="Execution payload (``BackendResult`` as JSON-compatible dict) when successful.",
    )
    error: str | None = Field(
        default=None,
        description="Pipeline-level error (e.g. LLM failure, missing dataset file).",
    )


class ExecuteStructuredQueryRequest(BaseModel):
    """Demo-safe body: run a pre-built structured query without the LLM."""

    dataset_name: str = Field(..., description="Logical dataset id (must be in ``SUPPORTED_DATASET_NAMES``).")
    structured_query: dict[str, Any] = Field(
        ...,
        description="JSON object validated as ``StructuredQuery``.",
    )

    @field_validator("dataset_name")
    @classmethod
    def _dataset_must_be_supported_exec(cls, value: str) -> str:
        if value not in SUPPORTED_DATASET_NAMES:
            raise ValueError(f"dataset_name must be one of {list(SUPPORTED_DATASET_NAMES)}, got {value!r}")
        return value


class ExecuteStructuredQueryResponse(BaseModel):
    """Response for POST ``/execute_structured_query`` (validate → execute, JSON-safe ``result``)."""

    dataset_name: str = Field(..., description="Dataset that was used.")
    structured_query: dict[str, Any] | None = Field(
        default=None,
        description="Normalized ``StructuredQuery`` after schema validation (JSON mode).",
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Row-level validation from ``validate_structured_query``.",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="JSON-safe ``BackendResult`` when schema + row validation pass and execution succeeds.",
    )
    error: str | None = Field(
        default=None,
        description="Schema parse error or execution failure message.",
    )


app = FastAPI(
    title="CSV Analyst Assistant API",
    version="0.1.0",
    description=(
        "Structured-query analytics backend: health, dataset metadata, "
        "natural-language query execution, and direct structured-query execution."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return a simple OK payload for load balancers and frontend checks."""
    return {"status": "ok"}


@app.get("/datasets", response_model=DatasetsResponse, summary="List supported datasets")
def list_datasets() -> DatasetsResponse:
    """List supported datasets with resolved CSV paths and optional time columns.

    Paths match :func:`resolve_dataset_csv_path` (processed ``.csv`` / ``*_cleaned.csv``, then raw).
    """
    items = [_dataset_registry_entry(name) for name in SUPPORTED_DATASET_NAMES]
    return DatasetsResponse(
        dataset_names=list(SUPPORTED_DATASET_NAMES),
        datasets=[DatasetItem(**item) for item in items],
    )


@app.post("/query", response_model=QueryResponse, summary="Natural language → structured query → execute")
def run_query(request: QueryRequest) -> QueryResponse:
    """Parse a question with the LLM router, validate against the dataset, then run analytics."""
    try:
        df = load_dataset_frame(request.dataset_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    config = _llm_router_config_override(request.model_name)
    try:
        structured = parse_question_to_structured_query(
            question=request.question,
            df=df,
            prompt_variant=request.prompt_variant,
            config=config,
        )
    except Exception as exc:  # pragma: no cover - network/provider dependent
        return QueryResponse(
            dataset_name=request.dataset_name,
            question=request.question,
            structured_query=None,
            validation_errors=[],
            result=None,
            error=str(exc),
        )

    prepared = _prepare_dataframe_for_query(df, structured)
    valid, validation_errors = validate_structured_query(structured, prepared)
    structured_dict = structured.model_dump(mode="json")

    if not valid:
        return QueryResponse(
            dataset_name=request.dataset_name,
            question=request.question,
            structured_query=structured_dict,
            validation_errors=validation_errors,
            result=None,
            error=None,
        )

    try:
        backend_result = execute_structured_query(prepared, structured)
        result_payload = execution_result_dict_json_safe(backend_result)
    except Exception as exc:  # pragma: no cover - defensive
        return QueryResponse(
            dataset_name=request.dataset_name,
            question=request.question,
            structured_query=structured_dict,
            validation_errors=[],
            result=None,
            error=str(exc),
        )

    return QueryResponse(
        dataset_name=request.dataset_name,
        question=request.question,
        structured_query=structured_dict,
        validation_errors=[],
        result=result_payload,
        error=None,
    )


@app.post(
    "/execute_structured_query",
    response_model=ExecuteStructuredQueryResponse,
    summary="Execute a structured query (demo / no LLM)",
)
def run_execute_structured_query(
    request: ExecuteStructuredQueryRequest,
) -> ExecuteStructuredQueryResponse:
    """Load data, parse ``structured_query`` → validate → ``execute_structured_query``; JSON-safe result."""
    try:
        df = load_dataset_frame(request.dataset_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        structured = StructuredQuery.model_validate(request.structured_query)
    except ValidationError as exc:
        parts: list[str] = []
        for err in exc.errors()[:16]:
            loc = ".".join(str(x) for x in err.get("loc", ()))
            msg = err.get("msg", "")
            parts.append(f"{loc}: {msg}" if loc else msg)
        detail = "; ".join(parts)
        return ExecuteStructuredQueryResponse(
            dataset_name=request.dataset_name,
            structured_query=None,
            validation_errors=[],
            result=None,
            error=detail or str(exc),
        )

    prepared = _prepare_dataframe_for_query(df, structured)
    valid, validation_errors = validate_structured_query(structured, prepared)
    structured_dict = structured.model_dump(mode="json")

    if not valid:
        return ExecuteStructuredQueryResponse(
            dataset_name=request.dataset_name,
            structured_query=structured_dict,
            validation_errors=validation_errors,
            result=None,
            error=None,
        )

    try:
        backend_result = execute_structured_query(prepared, structured)
        result_payload = execution_result_dict_json_safe(backend_result)
    except Exception as exc:  # pragma: no cover - defensive
        return ExecuteStructuredQueryResponse(
            dataset_name=request.dataset_name,
            structured_query=structured_dict,
            validation_errors=[],
            result=None,
            error=str(exc),
        )

    return ExecuteStructuredQueryResponse(
        dataset_name=request.dataset_name,
        structured_query=structured_dict,
        validation_errors=[],
        result=result_payload,
        error=None,
    )


if __name__ == "__main__":
    import sys

    print(
        "Run from the repo root with uvicorn (this module does not start the server):\n"
        "  uvicorn app.main:app --reload\n",
        file=sys.stderr,
    )
    sys.exit(1)
