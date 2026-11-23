"""Streamlit entry point for the Kenya Data Explorer Dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics import (
    PRESET_SQL_QUERIES,
    SQLQueryError,
    compute_correlation,
    compute_correlation_matrix,
    compute_county_rankings,
    compute_kpis,
    run_readonly_sql,
)
from src.charts import (
    make_correlation_heatmap,
    make_county_comparison_bar,
    make_kenya_county_map,
    make_metric_trend_line,
    make_rainfall_maize_scatter,
)
from src.data_loader import (
    METRIC_META,
    DataValidationError,
    enrich_with_geo,
    filter_data,
    load_data,
)

st.set_page_config(
    page_title="Kenya Data Explorer Dashboard",
    page_icon="🇰🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .hero-subtitle {
        color: #4B5563;
        font-size: 0.98rem;
        margin-top: -0.4rem;
        margin-bottom: 1rem;
    }
    [data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 0.85rem 1rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_default_dataset() -> pd.DataFrame:
    """Load and cache the bundled Kenya dashboard dataset."""
    return load_data()


def render_sidebar(df: pd.DataFrame) -> tuple[list[str], tuple[int, int], str, pd.DataFrame]:
    """Render sidebar controls and return active filter selections and active dataframe."""
    with st.sidebar:
        st.header("Dashboard Controls")

        uploaded_file = st.file_uploader(
            "Upload custom CSV (optional)",
            type=["csv"],
            help="Upload a CSV matching the 7-column schema (see data/DATA_DICTIONARY.md).",
        )
        active_df = df
        if uploaded_file is not None:
            try:
                active_df = load_data(uploaded_file)
                st.success(f"Loaded {len(active_df):,} rows from uploaded CSV.")
            except (DataValidationError, ValueError) as exc:
                st.error(f"Invalid CSV: {exc}")
                active_df = df

        all_counties = sorted(active_df["county"].unique().tolist())
        min_year = int(active_df["year"].min())
        max_year = int(active_df["year"].max())

        st.caption(
            f"**Dataset:** {len(active_df):,} rows · {len(all_counties)} counties · "
            f"{min_year}–{max_year}"
        )

        selected_counties = st.multiselect(
            "Counties",
            options=all_counties,
            default=all_counties,
            help="Choose one or more Kenyan counties to compare. Clear all to see the empty state.",
        )

        if min_year < max_year:
            year_range = st.slider(
                "Year range",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
            )
        else:
            year_range = (min_year, max_year)
            st.caption(f"Year: {min_year}")

        metric_keys = [
            "maize_yield_tonnes_per_ha",
            "kcse_mean_score",
            "house_price_ksh",
            "mpesa_agents",
            "rainfall_mm",
        ]
        selected_metric = st.selectbox(
            "Primary indicator",
            options=metric_keys,
            format_func=lambda key: METRIC_META[key].label,
            help="Controls the trend chart, county ranking bar chart, and Kenya map.",
        )

        st.divider()
        st.caption(
            "**Author:** Lucky Vincent ([@lordlucky-254](https://github.com/lordlucky-254))  \n"
            "Karatina University · Data / AI"
        )

    return selected_counties, year_range, selected_metric, active_df


def render_kpis(filtered: pd.DataFrame) -> None:
    """Render the top KPI metric strip with year-over-year deltas."""
    kpis = compute_kpis(filtered)
    delta_suffix = (
        f" vs {kpis.previous_year}" if kpis.previous_year is not None else ""
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        label="Avg Maize Yield (t/ha)",
        value=f"{kpis.avg_maize_yield:.2f}" if kpis.avg_maize_yield is not None else "—",
        delta=(
            f"{kpis.delta_maize_yield:+.2f} t/ha{delta_suffix}"
            if kpis.delta_maize_yield is not None
            else None
        ),
        help="Mean maize yield across selected counties and years. Delta compares the latest two years.",
    )
    c2.metric(
        label="Avg KCSE Mean Score",
        value=f"{kpis.avg_kcse_score:.2f}" if kpis.avg_kcse_score is not None else "—",
        delta=(
            f"{kpis.delta_kcse_score:+.2f} pts{delta_suffix}"
            if kpis.delta_kcse_score is not None
            else None
        ),
        help="Average KCSE mean grade score across selected counties and years.",
    )
    c3.metric(
        label="Avg House Price (KES)",
        value=(
            f"KES {kpis.avg_house_price:,.0f}"
            if kpis.avg_house_price is not None
            else "—"
        ),
        delta=(
            f"{kpis.delta_house_price_pct:+.1f}%{delta_suffix}"
            if kpis.delta_house_price_pct is not None
            else None
        ),
        help="Mean housing valuation across selected counties and years.",
    )
    c4.metric(
        label=f"M-Pesa Agents ({kpis.latest_year})" if kpis.latest_year else "M-Pesa Agents",
        value=(
            f"{kpis.latest_mpesa_agents:,}"
            if kpis.latest_mpesa_agents is not None
            else "—"
        ),
        delta=(
            f"{kpis.delta_mpesa_pct:+.1f}%{delta_suffix}"
            if kpis.delta_mpesa_pct is not None
            else None
        ),
        help="Total active M-Pesa agents in the latest year of the selected range (avoids double-counting across years).",
    )


def render_overview_tab(filtered: pd.DataFrame, metric: str) -> None:
    """Render scatter plot, time-series trend, and county ranking bar chart."""
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(make_rainfall_maize_scatter(filtered))
        corr = compute_correlation(filtered, "rainfall_mm", "maize_yield_tonnes_per_ha")
        if corr.r is not None and corr.r_squared is not None:
            st.info(
                f"**Rainfall vs Maize Yield:** {corr.strength_label} correlation "
                f"(**r = {corr.r:.2f}**, **R² = {corr.r_squared:.2f}**, n = {corr.sample_size}). "
                "Rainfall explains part of yield variation, but soil quality, seeds, and agronomy also matter."
            )
    with col2:
        st.plotly_chart(make_metric_trend_line(filtered, metric))
        st.caption(METRIC_META[metric].description)

    st.divider()
    st.plotly_chart(make_county_comparison_bar(filtered, metric))


def render_map_tab(filtered: pd.DataFrame, metric: str) -> None:
    """Render interactive Kenya county map and regional breakdown table."""
    geo_df = enrich_with_geo(filtered)
    mapped_count = geo_df["latitude"].notna().sum()

    if mapped_count == 0:
        st.warning("None of the selected counties have geographic coordinates configured.")
        return

    st.plotly_chart(make_kenya_county_map(filtered, metric))

    regional = (
        geo_df.groupby("region", as_index=False)
        .agg(
            counties=("county", "nunique"),
            avg_rainfall_mm=("rainfall_mm", "mean"),
            avg_maize_yield=("maize_yield_tonnes_per_ha", "mean"),
            avg_kcse_score=("kcse_mean_score", "mean"),
            avg_house_price_ksh=("house_price_ksh", "mean"),
            avg_mpesa_agents=("mpesa_agents", "mean"),
        )
        .sort_values("avg_maize_yield", ascending=False)
    )
    st.subheader("Regional Summary")
    st.dataframe(
        regional,
        hide_index=True,
        column_config={
            "region": st.column_config.TextColumn("Region"),
            "counties": st.column_config.NumberColumn("Counties", format="%d"),
            "avg_rainfall_mm": st.column_config.NumberColumn("Avg Rainfall (mm)", format="%.0f"),
            "avg_maize_yield": st.column_config.NumberColumn("Avg Maize (t/ha)", format="%.2f"),
            "avg_kcse_score": st.column_config.NumberColumn("Avg KCSE", format="%.2f"),
            "avg_house_price_ksh": st.column_config.NumberColumn("Avg House Price (KES)", format="KES %,.0f"),
            "avg_mpesa_agents": st.column_config.NumberColumn("Avg M-Pesa Agents", format="%,.0f"),
        },
    )


def render_insights_tab(filtered: pd.DataFrame, metric: str) -> None:
    """Render correlation matrix heatmap and automated executive findings."""
    col1, col2 = st.columns([1.25, 1])
    with col1:
        corr_matrix = compute_correlation_matrix(filtered)
        st.plotly_chart(make_correlation_heatmap(corr_matrix))

    with col2:
        st.subheader("Key Automated Insights")
        rankings = compute_county_rankings(filtered, metric)
        meta = METRIC_META[metric]

        if not rankings.empty:
            top_row = rankings.iloc[0]
            bottom_row = rankings.iloc[-1]
            st.markdown(
                f"- **Top performer ({meta.short_label}):** **{top_row['county']}** "
                f"averaging **{meta.fmt.format(top_row['average'])} {meta.unit}**."
            )
            if len(rankings) > 1:
                st.markdown(
                    f"- **Lowest average ({meta.short_label}):** **{bottom_row['county']}** "
                    f"averaging **{meta.fmt.format(bottom_row['average'])} {meta.unit}**."
                )

        rain_corr = compute_correlation(filtered, "rainfall_mm", "maize_yield_tonnes_per_ha")
        if rain_corr.r is not None:
            st.markdown(
                f"- **Agri-climate link:** Rainfall and maize yield show a "
                f"**{rain_corr.strength_label.lower()}** linear relationship (`r = {rain_corr.r:.2f}`)."
            )

        mpesa_house = compute_correlation(filtered, "mpesa_agents", "house_price_ksh")
        if mpesa_house.r is not None:
            st.markdown(
                f"- **Economic proxy check:** M-Pesa agent density vs. house prices has "
                f"`r = {mpesa_house.r:.2f}` ({mpesa_house.strength_label.lower()})."
            )

        st.divider()
        st.caption(
            "**Data Storytelling Reminder:** Correlation highlights patterns worth investigating, "
            "not proof of causation. Always validate findings with domain context and official KNBS data."
        )


def render_data_sql_tab(filtered: pd.DataFrame, full_df: pd.DataFrame) -> None:
    """Render formatted data table, CSV export, and safe read-only SQL explorer."""
    st.subheader("Filtered Dataset")
    st.dataframe(
        filtered,
        hide_index=True,
        column_config={
            "county": st.column_config.TextColumn("County"),
            "year": st.column_config.NumberColumn("Year", format="%d"),
            "rainfall_mm": st.column_config.NumberColumn("Rainfall (mm)", format="%,.0f"),
            "maize_yield_tonnes_per_ha": st.column_config.NumberColumn(
                "Maize Yield (t/ha)", format="%.2f"
            ),
            "kcse_mean_score": st.column_config.NumberColumn("KCSE Mean Score", format="%.2f"),
            "house_price_ksh": st.column_config.NumberColumn(
                "House Price (KES)", format="KES %,.0f"
            ),
            "mpesa_agents": st.column_config.NumberColumn("M-Pesa Agents", format="%,d"),
        },
    )

    st.download_button(
        label="Download Filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="kenya_dashboard_filtered.csv",
        mime="text/csv",
        type="primary",
    )

    st.divider()
    st.subheader("SQL Explorer (Read-Only SQLite)")
    st.caption(
        "Query the active table `kenya_data` using standard SQLite `SELECT` or `WITH` queries."
    )

    scope = st.radio(
        "Query scope",
        options=["Filtered selection", "Full dataset"],
        horizontal=True,
    )
    query_target = filtered if scope == "Filtered selection" else full_df

    preset_name = st.selectbox(
        "Load a preset query",
        options=list(PRESET_SQL_QUERIES.keys()),
    )
    sql_query = st.text_area(
        "SQL Query",
        value=PRESET_SQL_QUERIES[preset_name],
        height=140,
    )

    if st.button("Run SQL Query"):
        try:
            sql_result = run_readonly_sql(query_target, sql_query)
            st.success(f"Returned {len(sql_result):,} row(s).")
            st.dataframe(sql_result, hide_index=True)
            st.download_button(
                label="Download SQL Result CSV",
                data=sql_result.to_csv(index=False).encode("utf-8"),
                file_name="kenya_sql_result.csv",
                mime="text/csv",
            )
        except SQLQueryError as exc:
            st.error(str(exc))


def main() -> None:
    """Run the Streamlit application."""
    st.title("🇰🇪 Kenya Data Explorer Dashboard")
    st.markdown(
        '<p class="hero-subtitle">'
        "Interactive county-level explorer for Rainfall vs. Maize Yield, KCSE Scores, "
        "House Prices, and M-Pesa Agent Activity across Kenya."
        "</p>",
        unsafe_allow_html=True,
    )

    try:
        base_df = load_default_dataset()
    except (FileNotFoundError, DataValidationError) as exc:
        st.error(f"Could not load default dataset: {exc}")
        st.stop()

    selected_counties, year_range, selected_metric, active_df = render_sidebar(base_df)
    filtered = filter_data(active_df, selected_counties, year_range)

    if filtered.empty:
        st.warning(
            "No records match your current filters. Select at least one county in the sidebar."
        )
        st.stop()

    render_kpis(filtered)
    st.write("")

    tab_overview, tab_map, tab_insights, tab_data = st.tabs(
        [
            "📊 Overview & Trends",
            "🗺️ Kenya County Map",
            "🔎 Correlations & Insights",
            "🗄️ Data & SQL Explorer",
        ]
    )

    with tab_overview:
        render_overview_tab(filtered, selected_metric)
    with tab_map:
        render_map_tab(filtered, selected_metric)
    with tab_insights:
        render_insights_tab(filtered, selected_metric)
    with tab_data:
        render_data_sql_tab(filtered, active_df)

    st.divider()
    st.caption(
        "Dataset note: Bundled data is a synthetic demonstration dataset modeled on realistic Kenyan ranges. "
        "Replace `data/kenya_dashboard.csv` or upload a CSV in the sidebar to analyze official KNBS / World Bank data."
    )

    with st.expander("About this dashboard & methodology"):
        st.markdown(
            """
            **What this is:** An interactive explorer for county-level Kenyan indicators —
            rainfall, maize yield, KCSE mean scores, house prices, and M-Pesa agent activity.

            **How to read it:**
            - **KPIs** show period averages, with the latest year compared to the previous year.
              M-Pesa agents are reported as the *latest-year total* (not summed across years,
              which would double-count outlets).
            - **Rainfall vs. Maize Yield** includes an OLS trendline with Pearson `r` and `R²`.
              Correlation is not causation — soil, seed variety, and agronomy also drive yields.
            - **SQL Explorer** is strictly read-only (`SELECT` / `WITH` only) and runs in an
              in-memory SQLite database, so queries can never modify the source data.

            **Built with:** Python · Pandas · Streamlit · Plotly · SQLite ·
            [Source on GitHub](https://github.com/lordlucky-254/kenya-data-explorer-dashboard)
            """
        )


if __name__ == "__main__":
    main()
