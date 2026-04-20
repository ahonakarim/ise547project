"""Summarize router evaluation CSV outputs in a terminal-friendly format."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _as_bool(series: pd.Series) -> pd.Series:
    """Coerce mixed bool-like values to True/False with NA preserved."""
    if series.dtype == bool:
        return series
    text = series.astype("string").str.strip().str.lower()
    mapped = text.map(
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
    return mapped


def _print_header(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize router evaluation CSV results.")
    parser.add_argument("--input_path", type=Path, required=True, help="Path to router evaluation CSV.")
    args = parser.parse_args()

    df = pd.read_csv(args.input_path)
    total_rows = len(df)

    print(f"Input file: {args.input_path}")
    print(f"Total rows: {total_rows}")

    parse_success = _as_bool(df["parse_success"]) if "parse_success" in df.columns else pd.Series(dtype="boolean")
    exact_match = _as_bool(df["exact_match"]) if "exact_match" in df.columns else pd.Series(dtype="boolean")

    parse_success_count = int((parse_success == True).sum()) if total_rows else 0
    exact_match_count = int((exact_match == True).sum()) if total_rows else 0
    parse_success_rate = (parse_success_count / total_rows) if total_rows else 0.0
    exact_match_rate = (exact_match_count / total_rows) if total_rows else 0.0

    _print_header("Core Metrics")
    print(f"parse_success: {parse_success_count}/{total_rows} ({parse_success_rate:.2%})")
    print(f"exact_match:   {exact_match_count}/{total_rows} ({exact_match_rate:.2%})")

    _print_header("Error Message Counts")
    if "error_message" not in df.columns:
        print("(missing 'error_message' column)")
    else:
        errors = (
            df["error_message"]
            .astype("string")
            .fillna("")
            .str.strip()
            .replace("", "(empty)")
            .value_counts(dropna=False)
        )
        for msg, count in errors.items():
            print(f"{count:>6}  {msg}")

    _print_header("Failed Field Counts")
    failed_field_cols = [c for c in df.columns if c.endswith("_correct")]
    if not failed_field_cols:
        print("(no *_correct columns found)")
    else:
        for col in failed_field_cols:
            as_bool = _as_bool(df[col])
            failed_count = int((as_bool == False).sum())
            print(f"{col}: {failed_count}")


if __name__ == "__main__":
    main()
