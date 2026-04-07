"""MVP chart helpers returning matplotlib figure objects for Streamlit."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


def make_bar_chart(table_df: pd.DataFrame, x_col: str, y_col: str, title: str = "") -> Figure:
    """Create a simple bar chart figure from tabular data."""
    fig, ax = plt.subplots()
    ax.bar(table_df[x_col], table_df[y_col])
    if title:
        ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    fig.tight_layout()
    return fig


def make_line_chart(table_df: pd.DataFrame, x_col: str, y_col: str, title: str = "") -> Figure:
    """Create a simple line chart figure from tabular data."""
    fig, ax = plt.subplots()
    ax.plot(table_df[x_col], table_df[y_col])
    if title:
        ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    fig.tight_layout()
    return fig


def make_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, title: str = "") -> Figure:
    """Create a simple scatter plot figure from DataFrame columns."""
    fig, ax = plt.subplots()
    ax.scatter(df[x_col], df[y_col])
    if title:
        ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    fig.tight_layout()
    return fig
