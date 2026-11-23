"""Data loading, schema validation, filtering, and geographic enrichment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "kenya_dashboard.csv"

REQUIRED_COLUMNS = (
    "county", "year", "rainfall_mm", "maize_yield_tonnes_per_ha",
    "kcse_mean_score", "house_price_ksh", "mpesa_agents",
)
NUMERIC_COLUMNS = (
    "rainfall_mm", "maize_yield_tonnes_per_ha", "kcse_mean_score",
    "house_price_ksh", "mpesa_agents",
)


@dataclass(frozen=True)
class MetricMeta:
    column: str
    label: str
    short_label: str
    unit: str
    fmt: str
    description: str


METRIC_META: dict[str, MetricMeta] = {
    "maize_yield_tonnes_per_ha": MetricMeta("maize_yield_tonnes_per_ha", "Maize Yield (t/ha)", "Maize Yield", "t/ha", "{:.2f}", "Average annual maize yield in tonnes per hectare."),
    "kcse_mean_score": MetricMeta("kcse_mean_score", "KCSE Mean Score", "KCSE Score", "pts", "{:.2f}", "County mean grade point score in KCSE exams (1–12 scale)."),
    "house_price_ksh": MetricMeta("house_price_ksh", "House Price (KES)", "House Price", "KES", "{:,.0f}", "Representative housing price metric in Kenyan Shillings."),
    "mpesa_agents": MetricMeta("mpesa_agents", "M-Pesa Agents", "M-Pesa Agents", "agents", "{:,.0f}", "Active mobile money agent outlets operating in the county."),
    "rainfall_mm": MetricMeta("rainfall_mm", "Annual Rainfall (mm)", "Rainfall", "mm", "{:,.0f}", "Total recorded annual precipitation in millimeters."),
}

COUNTY_COORDS: dict[str, dict[str, Any]] = {
    "Nairobi": {"lat": -1.2921, "lon": 36.8219, "region": "Nairobi"},
    "Kiambu": {"lat": -1.1714, "lon": 36.8356, "region": "Central"},
    "Mombasa": {"lat": -4.0435, "lon": 39.6682, "region": "Coast"},
    "Kisumu": {"lat": -0.0917, "lon": 34.7680, "region": "Nyanza"},
    "Nakuru": {"lat": -0.3031, "lon": 36.0800, "region": "Rift Valley"},
    "Kericho": {"lat": -0.3677, "lon": 35.2831, "region": "Rift Valley"},
    "Uasin Gishu": {"lat": 0.5143, "lon": 35.2698, "region": "Rift Valley"},
    "Machakos": {"lat": -1.5177, "lon": 37.2634, "region": "Eastern"},
    "Kakamega": {"lat": 0.2827, "lon": 34.7519, "region": "Western"},
    "Nyeri": {"lat": -0.4167, "lon": 36.9500, "region": "Central"},
}


class DataValidationError(ValueError):
    """Raised when the input dataset fails schema validation."""


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataValidationError(f"Dataset is missing required column(s): {', '.join(missing)}")

    cleaned = df[list(REQUIRED_COLUMNS)].copy()
    cleaned["county"] = cleaned["county"].astype(str).str.strip()
    cleaned.loc[cleaned["county"].isin(["", "nan", "None"]), "county"] = pd.NA
    cleaned["year"] = pd.to_numeric(cleaned["year"], errors="coerce")
    for col in NUMERIC_COLUMNS:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    cleaned = cleaned.dropna(subset=list(REQUIRED_COLUMNS))
    cleaned = cleaned[cleaned["year"].between(1900, 2100)]
    if cleaned.empty:
        raise DataValidationError("Dataset contains no valid rows after cleaning.")

    cleaned["year"] = cleaned["year"].astype(int)
    cleaned["mpesa_agents"] = cleaned["mpesa_agents"].round().astype("Int64")
    return cleaned.sort_values(["county", "year"]).reset_index(drop=True)


def load_data(source: Path | str | IO[Any] = DEFAULT_DATA_PATH) -> pd.DataFrame:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found at '{path}'. Ensure data/kenya_dashboard.csv exists.")
        raw_df = pd.read_csv(path)
    else:
        raw_df = pd.read_csv(source)
    return validate_dataframe(raw_df)


def filter_data(df: pd.DataFrame, counties: list[str] | tuple[str, ...], year_range: tuple[int, int]) -> pd.DataFrame:
    if not counties:
        return df.iloc[0:0].copy()
    start_year, end_year = year_range
    mask = df["county"].isin(counties) & df["year"].between(start_year, end_year)
    return df.loc[mask].copy().reset_index(drop=True)


def enrich_with_geo(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["latitude"] = enriched["county"].map(lambda c: COUNTY_COORDS.get(c, {}).get("lat"))
    enriched["longitude"] = enriched["county"].map(lambda c: COUNTY_COORDS.get(c, {}).get("lon"))
    enriched["region"] = enriched["county"].map(lambda c: COUNTY_COORDS.get(c, {}).get("region", "Other"))
    return enriched
