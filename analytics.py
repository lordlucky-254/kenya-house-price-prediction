"""Analytical computations, KPIs, correlations, rankings, and safe SQL explorer."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.data_loader import METRIC_META, NUMERIC_COLUMNS

FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
    re.IGNORECASE,
)

PRESET_SQL_QUERIES: dict[str, str] = {
    "Top counties by average maize yield": (
        "SELECT county,\n"
        "       ROUND(AVG(maize_yield_tonnes_per_ha), 2) AS avg_maize_yield,\n"
        "       ROUND(AVG(rainfall_mm), 0) AS avg_rainfall_mm\n"
        "FROM kenya_data\n"
        "GROUP BY county\n"
        "ORDER BY avg_maize_yield DESC;"
    ),
    "Latest year snapshot across counties": (
        "SELECT county, year, rainfall_mm, maize_yield_tonnes_per_ha,\n"
        "       kcse_mean_score, house_price_ksh, mpesa_agents\n"
        "FROM kenya_data\n"
        "WHERE year = (SELECT MAX(year) FROM kenya_data)\n"
        "ORDER BY mpesa_agents DESC;"
    ),
    "High rainfall (>1400 mm) vs lower rainfall yield comparison": (
        "SELECT CASE WHEN rainfall_mm >= 1400 THEN 'High Rainfall (>=1400mm)'\n"
        "            ELSE 'Moderate/Low Rainfall (<1400mm)' END AS rainfall_band,\n"
        "       COUNT(*) AS observations,\n"
        "       ROUND(AVG(maize_yield_tonnes_per_ha), 2) AS avg_maize_yield,\n"
        "       ROUND(AVG(kcse_mean_score), 2) AS avg_kcse_score\n"
        "FROM kenya_data\n"
        "GROUP BY rainfall_band;"
    ),
    "Annual national averages over time": (
        "SELECT year,\n"
        "       ROUND(AVG(rainfall_mm), 0) AS avg_rainfall_mm,\n"
        "       ROUND(AVG(maize_yield_tonnes_per_ha), 2) AS avg_maize_yield,\n"
        "       ROUND(AVG(kcse_mean_score), 2) AS avg_kcse,\n"
        "       ROUND(AVG(house_price_ksh), 0) AS avg_house_price,\n"
        "       SUM(mpesa_agents) AS total_mpesa_agents\n"
        "FROM kenya_data\n"
        "GROUP BY year\n"
        "ORDER BY year;"
    ),
}


@dataclass(frozen=True)
class KPISummary:
    """Computed headline KPIs and year-over-year deltas for the filtered dataset."""

    avg_maize_yield: float | None
    delta_maize_yield: float | None
    avg_kcse_score: float | None
    delta_kcse_score: float | None
    avg_house_price: float | None
    delta_house_price_pct: float | None
    latest_mpesa_agents: int | None
    delta_mpesa_pct: float | None
    latest_year: int | None
    previous_year: int | None
    row_count: int
    county_count: int


@dataclass(frozen=True)
class CorrelationResult:
    """Pearson correlation and simple OLS regression summary."""

    r: float | None
    r_squared: float | None
    slope: float | None
    intercept: float | None
    strength_label: str
    sample_size: int


def compute_kpis(df: pd.DataFrame) -> KPISummary:
    """Compute headline metrics and latest-year vs prior-year deltas."""
    if df.empty:
        return KPISummary(
            avg_maize_yield=None,
            delta_maize_yield=None,
            avg_kcse_score=None,
            delta_kcse_score=None,
            avg_house_price=None,
            delta_house_price_pct=None,
            latest_mpesa_agents=None,
            delta_mpesa_pct=None,
            latest_year=None,
            previous_year=None,
            row_count=0,
            county_count=0,
        )

    years = sorted(df["year"].unique().tolist())
    latest_year = int(years[-1])
    previous_year = int(years[-2]) if len(years) >= 2 else None

    latest_df = df[df["year"] == latest_year]
    prev_df = df[df["year"] == previous_year] if previous_year is not None else None

    latest_mpesa = int(latest_df["mpesa_agents"].sum())

    delta_maize: float | None = None
    delta_kcse: float | None = None
    delta_house_pct: float | None = None
    delta_mpesa_pct: float | None = None

    if prev_df is not None and not prev_df.empty:
        delta_maize = float(
            latest_df["maize_yield_tonnes_per_ha"].mean()
            - prev_df["maize_yield_tonnes_per_ha"].mean()
        )
        delta_kcse = float(
            latest_df["kcse_mean_score"].mean() - prev_df["kcse_mean_score"].mean()
        )

        prev_house = float(prev_df["house_price_ksh"].mean())
        if prev_house > 0:
            delta_house_pct = (
                (float(latest_df["house_price_ksh"].mean()) - prev_house)
                / prev_house
                * 100.0
            )

        prev_mpesa = float(prev_df["mpesa_agents"].sum())
        if prev_mpesa > 0:
            delta_mpesa_pct = (latest_mpesa - prev_mpesa) / prev_mpesa * 100.0

    return KPISummary(
        avg_maize_yield=float(df["maize_yield_tonnes_per_ha"].mean()),
        delta_maize_yield=delta_maize,
        avg_kcse_score=float(df["kcse_mean_score"].mean()),
        delta_kcse_score=delta_kcse,
        avg_house_price=float(df["house_price_ksh"].mean()),
        delta_house_price_pct=delta_house_pct,
        latest_mpesa_agents=latest_mpesa,
        delta_mpesa_pct=delta_mpesa_pct,
        latest_year=latest_year,
        previous_year=previous_year,
        row_count=len(df),
        county_count=int(df["county"].nunique()),
    )


def _describe_correlation(r: float) -> str:
    abs_r = abs(r)
    direction = "positive" if r >= 0 else "negative"
    if abs_r >= 0.70:
        return f"Strong {direction}"
    if abs_r >= 0.40:
        return f"Moderate {direction}"
    if abs_r >= 0.20:
        return f"Weak {direction}"
    return "Very weak / negligible"


def compute_correlation(
    df: pd.DataFrame, x_col: str, y_col: str
) -> CorrelationResult:
    """Compute Pearson r and linear trendline coefficients for two numeric columns."""
    valid = df[[x_col, y_col]].dropna()
    n = len(valid)
    if n < 2:
        return CorrelationResult(
            r=None,
            r_squared=None,
            slope=None,
            intercept=None,
            strength_label="Insufficient data",
            sample_size=n,
        )

    x = valid[x_col].to_numpy(dtype=float)
    y = valid[y_col].to_numpy(dtype=float)

    if np.std(x) == 0 or np.std(y) == 0:
        return CorrelationResult(
            r=None,
            r_squared=None,
            slope=None,
            intercept=None,
            strength_label="Constant series",
            sample_size=n,
        )

    r = float(np.corrcoef(x, y)[0, 1])
    slope, intercept = np.polyfit(x, y, 1)
    return CorrelationResult(
        r=r,
        r_squared=r * r,
        slope=float(slope),
        intercept=float(intercept),
        strength_label=_describe_correlation(r),
        sample_size=n,
    )


def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Compute a labeled Pearson correlation matrix across dashboard numeric indicators."""
    cols = [col for col in NUMERIC_COLUMNS if col in df.columns]
    corr = df[cols].astype(float).corr()
    rename_map = {col: METRIC_META[col].short_label for col in cols}
    return corr.rename(index=rename_map, columns=rename_map)


def compute_county_rankings(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Rank counties by mean value of a metric, with min, max, and latest year."""
    if df.empty or metric not in df.columns:
        return pd.DataFrame(
            columns=["county", "average", "minimum", "maximum", "latest_value"]
        )

    latest_year = int(df["year"].max())
    summary = (
        df.groupby("county", as_index=False)[metric]
        .agg(average="mean", minimum="min", maximum="max")
    )
    latest_vals = (
        df.loc[df["year"] == latest_year, ["county", metric]]
        .rename(columns={metric: "latest_value"})
    )
    merged = summary.merge(latest_vals, on="county", how="left")
    return merged.sort_values("average", ascending=False).reset_index(drop=True)


class SQLQueryError(ValueError):
    """Raised when an invalid or non-read-only SQL query is submitted."""


def _readonly_authorizer(
    action: int,
    _arg1: str | None,
    _arg2: str | None,
    _db_name: str | None,
    _trigger_name: str | None,
) -> int:
    allowed_actions = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
    }
    return sqlite3.SQLITE_OK if action in allowed_actions else sqlite3.SQLITE_DENY


def run_readonly_sql(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Execute a read-only SQL SELECT/CTE query against an in-memory SQLite table."""
    stripped = query.strip()
    if not stripped:
        raise SQLQueryError("Please enter a SQL query.")

    upper_start = stripped.lstrip("(").upper()
    if not (upper_start.startswith("SELECT") or upper_start.startswith("WITH")):
        raise SQLQueryError("Only read-only SELECT or WITH queries are permitted.")

    if FORBIDDEN_SQL_PATTERN.search(stripped):
        raise SQLQueryError(
            "Query contains a disallowed keyword. Only read-only SELECT queries are allowed."
        )

    statements = [stmt.strip() for stmt in stripped.split(";") if stmt.strip()]
    if len(statements) > 1:
        raise SQLQueryError("Please run a single SQL statement at a time.")

    with sqlite3.connect(":memory:") as conn:
        df.to_sql("kenya_data", conn, index=False, if_exists="replace")
        conn.set_authorizer(_readonly_authorizer)
        try:
            return pd.read_sql_query(statements[0], conn)
        except Exception as exc:
            raise SQLQueryError(f"SQL execution error: {exc}") from exc
