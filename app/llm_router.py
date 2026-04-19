"""LLM router for MVP structured query parsing via OpenAI-compatible API."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import requests

from app.constants import PROMPT_VARIANTS
from app.prompts import build_prompt
from app.schemas import StructuredQuery

@dataclass(frozen=True)
class LLMRouterConfig:
    """Runtime configuration for OpenAI-compatible chat completions."""

    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 45


def _env_config() -> LLMRouterConfig:
    """Load router configuration from environment variables."""
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    timeout_seconds = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
    return LLMRouterConfig(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )


def build_schema_context(df: pd.DataFrame) -> str:
    """Build concise schema context from dataframe columns and dtypes."""
    lines: list[str] = ["Columns:"]
    for col in df.columns:
        lines.append(f"- {col}: {str(df[col].dtype)}")
    return "\n".join(lines)


def _extract_json_object(text: str) -> dict[str, Any]:
    """Extract first JSON object from model text output."""
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Fallback: extract outermost {...} block.
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model output did not contain a JSON object.")
    candidate = stripped[start : end + 1]
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("Parsed model output is not a JSON object.")
    return parsed


def _raise_for_non_ok_chat_completion(response: requests.Response) -> None:
    """Raise ValueError with HTTP status, raw body, and JSON body when parseable."""
    status = response.status_code
    text = response.text
    parsed_json: Any | None = None
    try:
        parsed_json = response.json()
    except ValueError:
        pass
    parts = [f"HTTP {status}", f"response.text={text!r}"]
    if parsed_json is not None:
        parts.append(f"response.json={parsed_json!r}")
    raise ValueError("OpenAI-compatible chat completions error: " + "; ".join(parts))


def _chat_completion(prompt: str, config: LLMRouterConfig) -> str:
    """Call OpenAI-compatible chat completion endpoint and return text content."""
    if not config.api_key:
        raise ValueError("OPENAI_API_KEY is required for LLM routing.")

    url = f"{config.base_url}/chat/completions"
    headers = {
    "Authorization": f"Bearer {config.api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-OpenRouter-Title": "CSV Analyst Assistant",
    }
    payload = {
        "model": config.model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "Return structured JSON only."},
            {"role": "user", "content": prompt},
        ],
    }

    retries = int(os.getenv("OPENAI_RETRY_ATTEMPTS", "3"))
    backoff_seconds = float(os.getenv("OPENAI_RETRY_BACKOFF_SECONDS", "1.5"))

    response: requests.Response | None = None
    for attempt in range(retries + 1):
        response = requests.post(url, headers=headers, json=payload, timeout=config.timeout_seconds)
        if response.status_code not in {429, 500, 502, 503, 504}:
            break
        if attempt >= retries:
            break
        sleep_for = backoff_seconds * (2**attempt)
        time.sleep(sleep_for)

    if response is None:
        raise ValueError("No response returned from LLM provider.")
    if not response.ok:
        _raise_for_non_ok_chat_completion(response)
    data = response.json()

    choices = data.get("choices") or []
    if not choices:
        raise ValueError("LLM response missing choices.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM response content is empty or malformed.")
    return content


def parse_question_to_structured_query(
    *,
    question: str,
    df: pd.DataFrame,
    prompt_variant: str = "schema_aware",
    config: LLMRouterConfig | None = None,
) -> StructuredQuery:
    """Parse natural-language question into a validated StructuredQuery.

    Flow:
    1) build dataframe schema context
    2) build prompt for selected variant
    3) call OpenAI-compatible API
    4) safely parse JSON
    5) validate via StructuredQuery model
    """
    if prompt_variant not in PROMPT_VARIANTS:
        raise ValueError(f"Unsupported prompt variant: {prompt_variant}")

    schema_context = build_schema_context(df)
    prompt = build_prompt(question=question, schema_context=schema_context, prompt_variant=prompt_variant)
    active_config = config or _env_config()

    raw_text = _chat_completion(prompt, active_config)
    parsed = _extract_json_object(raw_text)
    try:
        return StructuredQuery(**parsed)
    except Exception as exc:
        raise ValueError(f"Failed to validate StructuredQuery from model output: {exc}") from exc
