"""Smoke tests for Plotly chart builders."""

from __future__ import annotations

import plotly.graph_objects as go

from src.analytics import compute_correlation_matrix
from src.charts import (
    make_correlation_heatmap,
    make_county_comparison_bar,
    make_kenya_county_map,
    make_metric_trend_line,
    make_rainfall_maize_scatter,
)
from src.data_loader import load_data


def test_all_chart_builders_return_figures() -> None:
    df = load_data()

    scatter_fig = make_rainfall_maize_scatter(df)
    assert isinstance(scatter_fig, go.Figure)
    assert len(scatter_fig.data) >= 2  # county traces + trendline

    line_fig = make_metric_trend_line(df, "kcse_mean_score")
    assert isinstance(line_fig, go.Figure)
    assert len(line_fig.data) == 10

    bar_fig = make_county_comparison_bar(df, "house_price_ksh")
    assert isinstance(bar_fig, go.Figure)
    assert len(bar_fig.data) == 1

    map_fig = make_kenya_county_map(df, "mpesa_agents")
    assert isinstance(map_fig, go.Figure)
    assert len(map_fig.data) == 1

    heatmap_fig = make_correlation_heatmap(compute_correlation_matrix(df))
    assert isinstance(heatmap_fig, go.Figure)
    assert len(heatmap_fig.data) == 1
