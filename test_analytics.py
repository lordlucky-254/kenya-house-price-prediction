"""Unit tests for KPI computation, correlations, rankings, and SQL explorer."""

from __future__ import annotations

import pytest

from src.analytics import (
    PRESET_SQL_QUERIES,
    SQLQueryError,
    compute_correlation,
    compute_correlation_matrix,
    compute_county_rankings,
    compute_kpis,
    run_readonly_sql,
)
from src.data_loader import filter_data, load_data


def test_compute_kpis_full_dataset() -> None:
    df = load_data()
    kpis = compute_kpis(df)

    assert kpis.row_count == 80
    assert kpis.county_count == 10
    assert kpis.latest_year == 2025
    assert kpis.previous_year == 2024
    assert kpis.avg_maize_yield is not None and kpis.avg_maize_yield > 0
    assert kpis.delta_maize_yield is not None
    # Latest-year M-Pesa agents should equal 2025 sum, not all-years sum
    expected_2025_mpesa = int(df.loc[df["year"] == 2025, "mpesa_agents"].sum())
    assert kpis.latest_mpesa_agents == expected_2025_mpesa


def test_compute_kpis_empty_dataframe() -> None:
    df = load_data().iloc[0:0]
    kpis = compute_kpis(df)
    assert kpis.row_count == 0
    assert kpis.avg_maize_yield is None
    assert kpis.latest_mpesa_agents is None


def test_compute_kpis_single_year_has_no_deltas() -> None:
    df = filter_data(load_data(), ["Nairobi", "Nyeri"], (2025, 2025))
    kpis = compute_kpis(df)
    assert kpis.latest_year == 2025
    assert kpis.previous_year is None
    assert kpis.delta_maize_yield is None
    assert kpis.delta_mpesa_pct is None


def test_compute_correlation_rainfall_maize() -> None:
    df = load_data()
    corr = compute_correlation(df, "rainfall_mm", "maize_yield_tonnes_per_ha")
    assert corr.r is not None
    assert corr.r > 0.5
    assert corr.r_squared is not None
    assert corr.slope is not None and corr.slope > 0
    assert corr.sample_size == 80


def test_compute_correlation_matrix_shape_and_diagonal() -> None:
    df = load_data()
    matrix = compute_correlation_matrix(df)
    assert matrix.shape == (5, 5)
    for label in matrix.columns:
        assert matrix.loc[label, label] == pytest.approx(1.0)


def test_compute_county_rankings_sorted_descending() -> None:
    df = load_data()
    ranked = compute_county_rankings(df, "maize_yield_tonnes_per_ha")
    assert len(ranked) == 10
    assert ranked["average"].is_monotonic_decreasing


def test_preset_sql_queries_all_succeed() -> None:
    df = load_data()
    for name, query in PRESET_SQL_QUERIES.items():
        result = run_readonly_sql(df, query)
        assert not result.empty, f"Preset query '{name}' returned no rows"


def test_sql_explorer_supports_with_cte() -> None:
    df = load_data()
    cte_query = (
        "WITH latest AS (SELECT * FROM kenya_data WHERE year = 2025) "
        "SELECT county, mpesa_agents FROM latest ORDER BY mpesa_agents DESC LIMIT 3"
    )
    result = run_readonly_sql(df, cte_query)
    assert len(result) == 3


@pytest.mark.parametrize(
    "unsafe_query",
    [
        "",
        "DROP TABLE kenya_data;",
        "DELETE FROM kenya_data WHERE year = 2018;",
        "INSERT INTO kenya_data (county, year) VALUES ('Test', 2026);",
        "UPDATE kenya_data SET rainfall_mm = 0;",
        "SELECT * FROM kenya_data; DROP TABLE kenya_data;",
        "PRAGMA table_info(kenya_data);",
    ],
)
def test_sql_explorer_blocks_unsafe_queries(unsafe_query: str) -> None:
    df = load_data()
    with pytest.raises(SQLQueryError):
        run_readonly_sql(df, unsafe_query)
