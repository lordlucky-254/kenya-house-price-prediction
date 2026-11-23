# 🇰🇪 Kenya Data Explorer Dashboard

[![CI](https://github.com/lordlucky-254/kenya-data-explorer-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/lordlucky-254/kenya-data-explorer-dashboard/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-6.0%2B-3F4F75.svg)](https://plotly.com/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-0F766E.svg)](LICENSE)

> **Interactive county-level data dashboard for Kenya** — exploring Rainfall vs. Maize Yield, KCSE Mean Scores, House Prices, and M-Pesa Agent Activity. Built to turn raw county metrics into clear, actionable insights.

**Author:** Lucky Vincent ([@lordlucky-254](https://github.com/lordlucky-254)) · Karatina University · Data / AI
**Tech Stack:** Python • Pandas • NumPy • Streamlit • Plotly • SQLite • Pytest • Ruff

---

## Features

- **Dynamic KPI Strip with YoY Deltas** — Tracks average maize yield, KCSE mean score, average house price (KES), and latest-year M-Pesa agent counts (avoiding multi-year double counting).
- **Overview & Trend Analysis** — Interactive Rainfall vs. Maize Yield bubble chart with live **OLS trendline** and Pearson correlation (`r`, `R²`), multi-county time-series trends, and sorted county rankings.
- **Interactive Kenya County Map** — Geographic bubble map across 10 Kenyan counties paired with a regional summary table.
- **Correlations & Automated Insights** — Full 5×5 Pearson correlation heatmap and automated plain-English key findings highlighting top/bottom performers and correlation vs. causation reminders.
- **Data Table, Custom CSV Upload & Read-Only SQL Explorer** — Filter and export CSVs, upload your own KNBS/World Bank CSV (with schema validation), or run custom `SELECT`/`WITH` SQL queries directly in-browser via in-memory SQLite.

## Quickstart

### 1. Clone and set up a virtual environment

```bash
git clone https://github.com/lordlucky-254/kenya-data-explorer-dashboard.git
cd kenya-data-explorer-dashboard

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Launch the dashboard

```bash
streamlit run src/app.py
```

Open `http://localhost:8501` in your browser.

## Project Structure

```text
kenya-data-explorer-dashboard/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       └── ci.yml                 # Automated Ruff lint + Pytest CI (Python 3.11 & 3.12)
├── .streamlit/
│   └── config.toml                # Dashboard theme & server settings
├── data/
│   ├── kenya_dashboard.csv        # 80 rows (10 counties × 8 years, 2018–2025)
│   └── DATA_DICTIONARY.md         # Full schema, units & official data sources
├── src/
│   ├── __init__.py
│   ├── app.py                     # Streamlit UI entry point
│   ├── data_loader.py             # CSV loading, schema validation & geo lookup
│   ├── analytics.py               # KPIs, correlations, rankings & safe SQL engine
│   └── charts.py                  # Reusable Plotly figure builders
├── tests/
│   ├── test_analytics.py
│   ├── test_app_smoke.py
│   ├── test_charts.py
│   └── test_data_loader.py
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── PUSH_TO_GITHUB.md              # How to push this repo correctly (preserves folders)
├── README.md
├── SECURITY.md
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Dataset

`data/kenya_dashboard.csv` contains **80 county-year observations** (10 Kenyan counties × 8 years, `2018–2025`), synthetic but modeled on realistic Kenyan ranges.

| Column | Unit | Description |
| :--- | :--- | :--- |
| `county` | — | County name (Nairobi, Kiambu, Mombasa, Kisumu, Nakuru, Kericho, Uasin Gishu, Machakos, Kakamega, Nyeri) |
| `year` | Calendar year | Observation year (`2018–2025`) |
| `rainfall_mm` | mm | Annual total rainfall |
| `maize_yield_tonnes_per_ha` | t/ha | Average maize yield per hectare |
| `kcse_mean_score` | pts (1–12) | County KCSE mean grade score |
| `house_price_ksh` | KES | Representative housing valuation |
| `mpesa_agents` | count | Active M-Pesa agent outlets |

See [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md) for full details and instructions on swapping in real **KNBS**, **World Bank**, **KMD**, or **KNEC** datasets.

> ⚠️ The bundled dataset is synthetic for demonstration. Do not use it for policy, lending, or commercial decisions — replace it with verified official data first.

## Development & Testing

Install dev tools and run the linter and unit test suite:

```bash
pip install -r requirements-dev.txt
ruff check src tests
pytest
```

Expected: **all tests pass** (data validation, KPIs, correlations, SQL safety, chart builders, and Streamlit `AppTest` smoke tests).

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub — see [`PUSH_TO_GITHUB.md`](PUSH_TO_GITHUB.md) for the exact commands.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select `lordlucky-254/kenya-data-explorer-dashboard`, branch `main`, and set **Main file path** to `src/app.py`.
4. Click **Deploy** — dependencies install automatically from `requirements.txt`.
5. Paste the live app URL into this README and your GitHub repo's **Website** field.

## Troubleshooting

| Problem | Fix |
| :--- | :--- |
| `FileNotFoundError: data/kenya_dashboard.csv` | You are not in the repo root, or files were uploaded flat via GitHub web UI. Clone with `git clone` and run `streamlit run src/app.py` from the repo root — see `PUSH_TO_GITHUB.md`. |
| `ModuleNotFoundError: No module named 'src'` | Run from the repo root (`streamlit run src/app.py`), not from inside `src/`. |
| Tests fail with `ModuleNotFoundError` | Run `pytest` from the repo root; `pyproject.toml` sets `pythonpath = ["."]`. |
| Empty dashboard / warning about filters | Select at least one county in the sidebar. |

## What I Learned

- **Data storytelling:** Designing KPIs, filters, and visual hierarchy that answer clear questions rather than dumping raw plots.
- **Software engineering for analytics:** Separating data validation, analytical logic, chart builders, and UI code so everything is testable and maintainable.
- **Statistical discipline:** Recognizing that correlation (e.g., rainfall vs. maize yield) does not prove causation, and avoiding common KPI traps such as summing stock metrics across years.

## Roadmap

- [x] Fix repository structure (`src/` + `data/`) and modularize codebase
- [x] Add interactive Kenya county map & regional summary
- [x] Add read-only SQL Explorer & filtered CSV download
- [x] Add automated `pytest` test suite & GitHub Actions CI
- [ ] Integrate live official KNBS / World Bank Open Data API connectors
- [ ] Expand coverage to all 47 Kenyan counties

## License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE) for details.
