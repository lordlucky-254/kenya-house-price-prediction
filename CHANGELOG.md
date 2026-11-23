# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-23

### Fixed
- **Critical:** Restored the correct folder structure (`src/`, `data/`, `tests/`, `.github/`, `.streamlit/`). A previous GitHub web-upload flattened all files into the repo root, so `streamlit run src/app.py` crashed with `FileNotFoundError`. The repo now matches the README exactly.
- Removed the internal scratch file `REPO_SETUP.md` from the public repository.
- Hardened `validate_dataframe()` to drop rows with blank counties or missing/non-numeric values in any required column, and to reject implausible years — malformed uploads now fail with a clear message instead of crashing downstream.
- Chart builders now return a labelled empty figure instead of crashing when given empty data.

### Added
- GitHub Actions CI (`.github/workflows/ci.yml`) running Ruff + Pytest on Python 3.11 & 3.12.
- `.streamlit/config.toml` theme, GitHub issue/PR templates, `SECURITY.md`, and `PUSH_TO_GITHUB.md` (correct git-push instructions that preserve folder structure).
- Sidebar dataset summary (rows · counties · year span) and an in-app "About & methodology" expander.
- All counties are now selected by default (previously only the first five).

### Changed
- Bumped version to `1.1.0`; added `[build-system]` to `pyproject.toml`.

## [1.0.0] - 2026-11-23

### Added
- Modular architecture separating data loading (`src/data_loader.py`), analytics & SQL (`src/analytics.py`), visualizations (`src/charts.py`), and Streamlit UI (`src/app.py`).
- Interactive **Kenya County Map** with regional summary breakdown.
- **Correlations & Insights** tab with Pearson correlation matrix heatmap, OLS trendline on Rainfall vs. Maize Yield, and automated key findings.
- **Read-Only SQL Explorer** (in-memory SQLite) with preset queries and CSV export.
- Sidebar **Custom CSV Upload** with automatic schema validation.
- Unit test suite (`tests/`) covering data validation, KPIs, correlations, chart generation, and SQL query safety.
- Project governance and documentation: `LICENSE` (MIT), `CONTRIBUTING.md`, `data/DATA_DICTIONARY.md`, `pyproject.toml`, and GitHub issue templates.

### Fixed
- Corrected M-Pesa Agents KPI to report latest-year total with year-over-year delta instead of double-counting agents across multiple years.
- Added graceful empty-state handling when no counties are selected.
