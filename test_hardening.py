"""Regression tests for v1.1.0 hardening: empty charts and malformed rows."""

from __future__ import annotations

import io

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.charts import (
    make_correlation_heatmap,
    make_county_comparison_bar,
    make_kenya_county_map,
    make_metric_trend_line,
    make_rainfall_maize_scatter,
)
from src.data_loader import REQUIRED_COLUMNS, DataValidationError, load_data


def test_chart_builders_handle_empty_dataframe() -> None:
    empty = pd.DataFrame(columns=list(REQUIRED_COLUMNS))
    assert isinstance(make_rainfall_maize_scatter(empty), go.Figure)
    assert isinstance(make_metric_trend_line(empty, "kcse_mean_score"), go.Figure)
    assert isinstance(make_county_comparison_bar(empty, "kcse_mean_score"), go.Figure)
    assert isinstance(make_kenya_county_map(empty, "kcse_mean_score"), go.Figure)
    assert isinstance(make_correlation_heatmap(pd.DataFrame()), go.Figure)


def test_load_data_drops_malformed_rows() -> None:
    header = ",".join(REQUIRED_COLUMNS)
    csv_text = (
        header + "\n"
        "Nairobi,2024,1000,2.5,6.0,120000,5000\n"
        ",2024,1000,2.5,6.0,120000,5000\n"
        "Nyeri,not-a-year,1000,2.5,6.0,120000,5000\n"
        "Nyeri,2024,,2.5,6.0,120000,5000\n"
    )
    df = load_data(io.StringIO(csv_text))
    assert len(df) == 1
    assert df.iloc[0]["county"] == "Nairobi"


def test_load_data_all_malformed_raises() -> None:
    header = ",".join(REQUIRED_COLUMNS)
    csv_text = header + "\n,2024,1000,2.5,6.0,120000,5000\n"
    with pytest.raises(DataValidationError, match="no valid rows"):
        load_data(io.StringIO(csv_text))
