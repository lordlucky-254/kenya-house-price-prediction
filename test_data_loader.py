"""Unit tests for data loading, schema validation, filtering, and geo enrichment."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import (
    DEFAULT_DATA_PATH,
    REQUIRED_COLUMNS,
    DataValidationError,
    enrich_with_geo,
    filter_data,
    load_data,
)


def test_default_dataset_loads_and_matches_schema() -> None:
    df = load_data(DEFAULT_DATA_PATH)
    assert len(df) == 80
    assert df["county"].nunique() == 10
    assert df["year"].min() == 2018
    assert df["year"].max() == 2025
    for col in REQUIRED_COLUMNS:
        assert col in df.columns


def test_load_data_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_data(Path("data/does_not_exist.csv"))


def test_load_data_missing_columns_raises() -> None:
    bad_csv = io.StringIO("county,year,rainfall_mm\nNairobi,2024,1000\n")
    with pytest.raises(DataValidationError, match="missing required column"):
        load_data(bad_csv)


def test_load_data_empty_csv_raises() -> None:
    empty_csv = io.StringIO(",".join(REQUIRED_COLUMNS) + "\n")
    with pytest.raises(DataValidationError, match="no valid rows"):
        load_data(empty_csv)


def test_filter_data_counties_and_years() -> None:
    df = load_data()
    filtered = filter_data(df, ["Nairobi", "Nyeri"], (2020, 2023))
    assert set(filtered["county"].unique()) == {"Nairobi", "Nyeri"}
    assert filtered["year"].min() == 2020
    assert filtered["year"].max() == 2023
    assert len(filtered) == 8


def test_filter_data_empty_counties_returns_empty_dataframe() -> None:
    df = load_data()
    filtered = filter_data(df, [], (2018, 2025))
    assert filtered.empty
    assert list(filtered.columns) == list(df.columns)


def test_enrich_with_geo_populates_coordinates() -> None:
    df = load_data()
    geo_df = enrich_with_geo(df)
    assert geo_df["latitude"].notna().all()
    assert geo_df["longitude"].notna().all()
    assert "Central" in set(geo_df["region"])


def test_enrich_with_geo_handles_unknown_county_gracefully() -> None:
    custom = pd.DataFrame(
        [
            {
                "county": "Turkana",
                "year": 2024,
                "rainfall_mm": 350,
                "maize_yield_tonnes_per_ha": 1.1,
                "kcse_mean_score": 4.9,
                "house_price_ksh": 55000,
                "mpesa_agents": 1200,
            }
        ]
    )
    geo_df = enrich_with_geo(custom)
    assert pd.isna(geo_df.loc[0, "latitude"])
    assert geo_df.loc[0, "region"] == "Other"
