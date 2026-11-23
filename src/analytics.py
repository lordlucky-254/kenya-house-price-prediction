"""Analytical computations and safe read-only SQL explorer."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as np
import pandas as pd

from src.data_loader import METRIC_META, NUMERIC_COLUMNS

FORBIDDEN_SQL_PATTERN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA|VACUUM)\b", re.IGNORECASE)

@dataclass(frozen=True)
class KPISummary:
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
    r: float | None
    r_squared: float | None
    slope: float | None
    intercept: float | None
    strength_label: str
    sample_size: int


PRESET_SQL_QUERIES: dict[str, str] = {
    "Top counties by average maize yield": "SELECT county, ROUND(AVG(maize_yield_tonnes_per_ha), 2) AS avg_maize_yield FROM kenya_data GROUP BY county ORDER BY avg_maize_yield DESC;",
    "Latest year snapshot": "SELECT county, year, house_price_ksh, mpesa_agents FROM kenya_data WHERE year = (SELECT MAX(year) FROM kenya_data) ORDER BY house_price_ksh DESC;",
}


def compute_kpis(df: pd.DataFrame) -> KPISummary:
    if df.empty:
        return KPISummary(None, None, None, None, None, None, None, None, None, None, 0, 0)
    years = sorted(df["year"].unique().tolist())
    latest_year = int(years[-1])
    previous_year = int(years[-2]) if len(years) >= 2 else None
    latest_df = df[df["year"] == latest_year]
    prev_df = df[df["year"] == previous_year] if previous_year is not None else None

    delta_maize = delta_kcse = delta_house_pct = delta_mpesa_pct = None
    latest_mpesa = int(latest_df["mpesa_agents"].sum())
    if prev_df is not None and not prev_df.empty:
        delta_maize = float(latest_df["maize_yield_tonnes_per_ha"].mean() - prev_df["maize_yield_tonnes_per_ha"].mean())
        delta_kcse = float(latest_df["kcse_mean_score"].mean() - prev_df["kcse_mean_score"].mean())
        prev_house = float(prev_df["house_price_ksh"].mean())
        if prev_house > 0:
            delta_house_pct = (float(latest_df["house_price_ksh"].mean()) - prev_house) / prev_house * 100
        prev_mpesa = float(prev_df["mpesa_agents"].sum())
        if prev_mpesa > 0:
            delta_mpesa_pct = (latest_mpesa - prev_mpesa) / prev_mpesa * 100

    return KPISummary(
        float(df["maize_yield_tonnes_per_ha"].mean()), delta_maize,
        float(df["kcse_mean_score"].mean()), delta_kcse,
        float(df["house_price_ksh"].mean()), delta_house_pct,
        latest_mpesa, delta_mpesa_pct, latest_year, previous_year,
        len(df), int(df["county"].nunique()),
    )


def _describe_correlation(r: float) -> str:
    abs_r = abs(r)
    if abs_r >= 0.70:
        strength = "Strong"
    elif abs_r >= 0.40:
        strength = "Moderate"
    elif abs_r >= 0.20:
        strength = "Weak"
    else:
        return "Very weak / negligible"
    return f"{strength} {'positive' if r >= 0 else 'negative'}"


def compute_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> CorrelationResult:
    valid = df[[x_col, y_col]].dropna()
    if len(valid) < 2:
        return CorrelationResult(None, None, None, None, "Insufficient data", len(valid))
    x = valid[x_col].to_numpy(dtype=float)
    y = valid[y_col].to_numpy(dtype=float)
    if np.std(x) == 0 or np.std(y) == 0:
        return CorrelationResult(None, None, None, None, "Constant series", len(valid))
    r = float(np.corrcoef(x, y)[0, 1])
    slope, intercept = np.polyfit(x, y, 1)
    return CorrelationResult(r, r * r, float(slope), float(intercept), _describe_correlation(r), len(valid))


def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    cols = [col for col in NUMERIC_COLUMNS if col in df.columns]
    corr = df[cols].astype(float).corr()
    rename_map = {col: METRIC_META[col].short_label for col in cols}
    return corr.rename(index=rename_map, columns=rename_map)


def compute_county_rankings(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    if df.empty or metric not in df.columns:
        return pd.DataFrame(columns=["county", "average", "minimum", "maximum", "latest_value"])
    latest_year = int(df["year"].max())
    summary = df.groupby("county", as_index=False)[metric].agg(average="mean", minimum="min", maximum="max")
    latest_vals = df.loc[df["year"] == latest_year, ["county", metric]].rename(columns={metric: "latest_value"})
    merged = summary.merge(latest_vals, on="county", how="left")
    return merged.sort_values("average", ascending=False).reset_index(drop=True)


class SQLQueryError(ValueError):
    """Raised when an invalid or non-read-only SQL query is submitted."""


def _readonly_authorizer(action: int, *_args) -> int:
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
    return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY


def run_readonly_sql(df: pd.DataFrame, query: str) -> pd.DataFrame:
    stripped = query.strip()
    upper_start = stripped.lstrip("(").upper()
    if not stripped:
        raise SQLQueryError("Please enter a SQL query.")
    if not (upper_start.startswith("SELECT") or upper_start.startswith("WITH")):
        raise SQLQueryError("Only read-only SELECT or WITH queries are permitted.")
    if FORBIDDEN_SQL_PATTERN.search(stripped):
        raise SQLQueryError("Query contains a disallowed keyword. Only read-only SELECT queries are allowed.")
    statements = [stmt.strip() for stmt in stripped.split(";") if stmt.strip()]
    if len(statements) != 1:
        raise SQLQueryError("Please run a single SQL statement at a time.")
    with sqlite3.connect(":memory:") as conn:
        df.to_sql("kenya_data", conn, index=False, if_exists="replace")
        conn.set_authorizer(_readonly_authorizer)
        try:
            return pd.read_sql_query(statements[0], conn)
        except Exception as exc:
            raise SQLQueryError(f"SQL execution error: {exc}") from exc
