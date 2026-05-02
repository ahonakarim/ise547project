"""Compare multiple router-eval CSV runs in one terminal table."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _as_bool(series: pd.Series) -> pd.Series:
    """Coerce mixed bool-like values to bool/NA."""
    if series.dtype == bool:
        return series
    text = series.astype("string").str.strip().str.lower()
    return text.map(
        {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "<na>": pd.NA,
            "nan": pd.NA,
            "none": pd.NA,
            "": pd.NA,
        }
    )


def _pick_single_value(df: pd.DataFrame, column: str, fallback: str) -> str:
    """Pick a representative non-empty value from a column."""
    if column not in df.columns:
        return fallback
    vals = (
        df[column]
        .astype("string")
        .fillna("")
        .str.strip()
    )
    vals = vals[vals != ""]
    if vals.empty:
        return fallback
    return str(vals.mode().iloc[0])


def _most_common_error(df: pd.DataFrame) -> str:
    if "error_message" not in df.columns:
        return "(none)"
    errs = (
        df["error_message"]
        .astype("string")
        .fillna("")
        .str.strip()
    )
    errs = errs[errs != ""]
    if errs.empty:
        return "(none)"
    return str(errs.value_counts().idxmax())


def _most_common_failed_field(df: pd.DataFrame) -> str:
    failed_cols = [c for c in df.columns if c.endswith("_correct")]
    if not failed_cols:
        return "(none)"

    fail_counts: dict[str, int] = {}
    for col in failed_cols:
        as_bool = _as_bool(df[col])
        fail_counts[col] = int((as_bool == False).sum())

    if not fail_counts:
        return "(none)"
    top_field = max(fail_counts, key=lambda k: fail_counts[k])
    if fail_counts[top_field] == 0:
        return "(none)"
    return top_field


def _summarize_run(path: Path) -> dict[str, object]:
    df = pd.read_csv(path)
    total_rows = len(df)

    parse_success = _as_bool(df["parse_success"]) if "parse_success" in df.columns else pd.Series(dtype="boolean")
    exact_match = _as_bool(df["exact_match"]) if "exact_match" in df.columns else pd.Series(dtype="boolean")

    parse_success_count = int((parse_success == True).sum()) if total_rows else 0
    exact_match_count = int((exact_match == True).sum()) if total_rows else 0
    parse_success_rate = (parse_success_count / total_rows) if total_rows else 0.0
    exact_match_rate = (exact_match_count / total_rows) if total_rows else 0.0

    return {
        "model_name": _pick_single_value(df, "model_name", "(unknown)"),
        "prompt_variant": _pick_single_value(df, "prompt_variant", "(unknown)"),
        "total_rows": total_rows,
        "parse_success_count": parse_success_count,
        "parse_success_rate": parse_success_rate,
        "exact_match_count": exact_match_count,
        "exact_match_rate": exact_match_rate,
        "most_common_error": _most_common_error(df),
        "most_common_failed_field": _most_common_failed_field(df),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare multiple router-eval CSV runs.")
    parser.add_argument(
        "--input_paths",
        type=Path,
        nargs="+",
        required=True,
        help="One or more router-eval CSV files.",
    )
    args = parser.parse_args()

    rows = [_summarize_run(path) for path in args.input_paths]
    out = pd.DataFrame(rows)

    if out.empty:
        print("No input rows to compare.")
        return

    out["parse_success_rate"] = out["parse_success_rate"].map(lambda v: f"{v:.2%}")
    out["exact_match_rate"] = out["exact_match_rate"].map(lambda v: f"{v:.2%}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
