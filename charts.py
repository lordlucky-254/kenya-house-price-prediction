"""Plotly visualization builders with consistent Kenya Data Explorer styling."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.analytics import compute_correlation, compute_county_rankings
from src.data_loader import METRIC_META, enrich_with_geo

COLOR_PALETTE: list[str] = [
    "#0F766E",  # Deep teal
    "#D97706",  # Warm amber
    "#2563EB",  # Royal blue
    "#DC2626",  # Kenyan red accent
    "#15803D",  # Savanna green
    "#7C3AED",  # Violet
    "#0891B2",  # Cyan
    "#EA580C",  # Terracotta
    "#4F46E5",  # Indigo
    "#64748B",  # Slate
]

COMMON_LAYOUT: dict = {
    "template": "plotly_white",
    "font": {"family": "Inter, system-ui, -apple-system, sans-serif", "size": 13},
    "margin": {"l": 20, "r": 20, "t": 48, "b": 24},
    "hoverlabel": {"bgcolor": "#FFFFFF", "font_size": 12},
}


def _empty_figure(title: str, height: int = 440) -> go.Figure:
    """Return a labelled empty figure so charts never crash on empty data."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data to display for the current selection.",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": "#64748B"},
    )
    fig.update_layout(**COMMON_LAYOUT, title=title, height=height)
    return fig


def make_rainfall_maize_scatter(df: pd.DataFrame) -> go.Figure:
    """Create a scatter plot of Rainfall vs Maize Yield with an OLS trendline."""
    if df.empty:
        return _empty_figure("Rainfall vs Maize Yield (bubble size = M-Pesa Agents)")
    fig = px.scatter(
        df,
        x="rainfall_mm",
        y="maize_yield_tonnes_per_ha",
        color="county",
        size="mpesa_agents",
        size_max=22,
        hover_name="county",
        hover_data={
            "year": True,
            "rainfall_mm": ":,.0f",
            "maize_yield_tonnes_per_ha": ":.2f",
            "mpesa_agents": ":,",
            "county": False,
        },
        color_discrete_sequence=COLOR_PALETTE,
        labels={
            "rainfall_mm": METRIC_META["rainfall_mm"].label,
            "maize_yield_tonnes_per_ha": METRIC_META["maize_yield_tonnes_per_ha"].label,
            "county": "County",
            "mpesa_agents": "M-Pesa Agents",
            "year": "Year",
        },
    )

    corr = compute_correlation(df, "rainfall_mm", "maize_yield_tonnes_per_ha")
    if corr.slope is not None and corr.intercept is not None and corr.r is not None:
        x_vals = np.linspace(
            float(df["rainfall_mm"].min()), float(df["rainfall_mm"].max()), 50
        )
        y_vals = corr.slope * x_vals + corr.intercept
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name=f"OLS Trendline (r = {corr.r:.2f})",
                line={"color": "#111827", "width": 2, "dash": "dash"},
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        **COMMON_LAYOUT,
        title="Rainfall vs Maize Yield (bubble size = M-Pesa Agents)",
        legend_title_text="County",
        height=440,
    )
    return fig


def make_metric_trend_line(df: pd.DataFrame, metric: str) -> go.Figure:
    """Create a multi-county time-series line chart for the selected indicator."""
    meta = METRIC_META[metric]
    if df.empty:
        return _empty_figure(f"{meta.label} Over Time by County")
    fig = px.line(
        df.sort_values(["county", "year"]),
        x="year",
        y=metric,
        color="county",
        markers=True,
        color_discrete_sequence=COLOR_PALETTE,
        labels={
            "year": "Year",
            metric: meta.label,
            "county": "County",
        },
    )
    fig.update_xaxes(dtick=1)
    fig.update_traces(line={"width": 2.4}, marker={"size": 7})
    fig.update_layout(
        **COMMON_LAYOUT,
        title=f"{meta.label} Over Time by County",
        legend_title_text="County",
        height=440,
    )
    return fig


def make_county_comparison_bar(df: pd.DataFrame, metric: str) -> go.Figure:
    """Create a sorted horizontal bar chart ranking counties by period average."""
    meta = METRIC_META[metric]
    if df.empty:
        return _empty_figure(f"County Ranking — Average {meta.label}")
    ranked = compute_county_rankings(df, metric).sort_values("average", ascending=True)

    fig = px.bar(
        ranked,
        x="average",
        y="county",
        orientation="h",
        text=ranked["average"].map(lambda val: meta.fmt.format(val)),
        color="average",
        color_continuous_scale=["#CCFBF1", "#0F766E"],
        labels={"average": f"Average {meta.label}", "county": "County"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        **COMMON_LAYOUT,
        title=f"County Ranking — Average {meta.label}",
        height=max(340, 42 * len(ranked) + 90),
    )
    return fig


def make_kenya_county_map(df: pd.DataFrame, metric: str) -> go.Figure:
    """Create an interactive geographic bubble map of Kenyan counties."""
    meta = METRIC_META[metric]
    if df.empty:
        return _empty_figure(f"Kenya County Overview — Average {meta.label}", height=520)
    geo_df = enrich_with_geo(df).dropna(subset=["latitude", "longitude"])
    if geo_df.empty:
        return _empty_figure(f"Kenya County Overview — Average {meta.label}", height=520)

    agg = (
        geo_df.groupby(["county", "region", "latitude", "longitude"], as_index=False)
        .agg(
            metric_avg=(metric, "mean"),
            avg_rainfall=("rainfall_mm", "mean"),
            avg_maize=("maize_yield_tonnes_per_ha", "mean"),
            avg_kcse=("kcse_mean_score", "mean"),
            avg_house=("house_price_ksh", "mean"),
            avg_mpesa=("mpesa_agents", "mean"),
        )
    )

    fig = px.scatter_map(
        agg,
        lat="latitude",
        lon="longitude",
        size="metric_avg",
        color="metric_avg",
        hover_name="county",
        hover_data={
            "region": True,
            "metric_avg": ":.2f",
            "avg_rainfall": ":,.0f",
            "avg_maize": ":.2f",
            "avg_kcse": ":.2f",
            "avg_house": ":,.0f",
            "avg_mpesa": ":,.0f",
            "latitude": False,
            "longitude": False,
        },
        color_continuous_scale="Tealgrn",
        size_max=34,
        zoom=5.3,
        center={"lat": -0.65, "lon": 36.8},
        map_style="carto-positron",
        labels={
            "metric_avg": meta.label,
            "region": "Region",
            "avg_rainfall": "Avg Rainfall (mm)",
            "avg_maize": "Avg Maize Yield (t/ha)",
            "avg_kcse": "Avg KCSE Score",
            "avg_house": "Avg House Price (KES)",
            "avg_mpesa": "Avg M-Pesa Agents",
        },
    )
    fig.update_layout(
        **COMMON_LAYOUT,
        title=f"Kenya County Overview — Average {meta.label}",
        height=520,
    )
    return fig


def make_correlation_heatmap(corr_df: pd.DataFrame) -> go.Figure:
    """Create an annotated correlation matrix heatmap across all indicators."""
    if corr_df is None or corr_df.empty:
        return _empty_figure("Indicator Correlation Matrix (Pearson r)")
    fig = px.imshow(
        corr_df,
        text_auto=".2f",
        zmin=-1.0,
        zmax=1.0,
        color_continuous_scale="RdBu",
        aspect="auto",
    )
    fig.update_layout(
        **COMMON_LAYOUT,
        title="Indicator Correlation Matrix (Pearson r)",
        height=440,
    )
    return fig
