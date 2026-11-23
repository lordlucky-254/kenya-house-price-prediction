# Contributing to Kenya Data Explorer Dashboard

Thank you for your interest in improving this project! Contributions of all kinds — real Kenyan datasets, new visualizations, bug fixes, tests, and documentation — are welcome.

## Local Development Setup

```bash
git clone https://github.com/lordlucky-254/kenya-data-explorer-dashboard.git
cd kenya-data-explorer-dashboard

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
```

## Running the App

```bash
streamlit run src/app.py
```

Open `http://localhost:8501` in your browser.

## Code Quality & Testing

Before opening a pull request, make sure linting and tests pass:

```bash
ruff check src tests
pytest
```

## Project Layout & Where Code Goes

| Concern | File |
| :--- | :--- |
| CSV loading, schema validation, geo lookup | `src/data_loader.py` |
| KPIs, correlations, rankings, SQL explorer | `src/analytics.py` |
| Plotly figure builders | `src/charts.py` |
| Streamlit UI only (no business logic) | `src/app.py` |
| Tests | `tests/test_*.py` |

Keep business logic out of `src/app.py` so it can be unit-tested independently of Streamlit UI state.

## Pull Request Guidelines

1. Create a focused branch (e.g., `feat/knbs-real-data` or `fix/map-tooltip`).
2. Add or update unit tests under `tests/` for any behavioural changes.
3. Update `data/DATA_DICTIONARY.md` and `README.md` if you add columns or features.
4. Add a `CHANGELOG.md` entry under the next release heading.
5. Never commit secrets, credentials, `.env` files, or personal scratch notes.
6. Push with `git` (see `PUSH_TO_GITHUB.md`) — **do not** use GitHub's web "Add files via upload", which flattens folder structure and breaks the app.

## Reporting Issues

Use the issue templates in `.github/ISSUE_TEMPLATE/`. Include steps to reproduce, expected vs. actual behaviour, and your Python/Streamlit versions.
