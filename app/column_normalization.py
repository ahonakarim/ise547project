"""Normalize column names for tabular datasets (snake_case, lowercase, safe chars)."""

from __future__ import annotations

import re
from typing import Iterable

_NON_ALNUM = re.compile(r"[^a-z0-9_]+")
_MULTI_UNDERSCORE = re.compile(r"_+")


def normalize_column_name(name: str) -> str:
    """Convert a column label to lowercase snake_case with only ``[a-z0-9_]``.

    Steps: trim whitespace, replace spaces with underscores, split CamelCase,
    lowercase, replace any non-alphanumeric run with a single underscore, collapse
    repeated underscores, strip edge underscores. Empty results become
    ``unnamed_column``.
    """
    s = str(name).strip()
    if not s:
        return "unnamed_column"
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = s.lower()
    s = _NON_ALNUM.sub("_", s)
    s = _MULTI_UNDERSCORE.sub("_", s).strip("_")
    return s or "unnamed_column"


def normalize_column_names(names: Iterable[str]) -> list[str]:
    """Normalize a sequence of column names, deduplicating collisions with numeric suffixes."""
    out: list[str] = []
    counts: dict[str, int] = {}
    for raw in names:
        base = normalize_column_name(raw)
        if base not in counts:
            counts[base] = 1
            out.append(base)
        else:
            counts[base] += 1
            out.append(f"{base}_{counts[base]}")
    return out


def rename_dataframe_columns(df):  # type: ignore[no-untyped-def]
    """Return a copy of ``df`` with normalized, unique, lowercase snake_case columns."""
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas.DataFrame")
    new_cols = normalize_column_names(df.columns)
    out = df.copy()
    out.columns = new_cols
    return out
