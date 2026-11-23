# Pushing This Repo to GitHub (Read This First)

> ⚠️ **Do NOT use GitHub's web "Add files via upload" button for this project.**
> That is what broke the previous version: GitHub flattens uploaded files into
> the repo root, so `src/app.py` and `data/kenya_dashboard.csv` ended up in the
> wrong place and the app crashed on startup with `FileNotFoundError`.
> Always push with `git` from your terminal, as below — it preserves folders.

## Option A — Replace the existing repo (recommended)

```bash
# 1. Clone the existing repo
git clone https://github.com/lordlucky-254/kenya-data-explorer-dashboard.git
cd kenya-data-explorer-dashboard

# 2. Delete the old flat files (they now live in src/, data/, tests/, ...)
git rm -r --cached .            # unstage everything, keep working tree
rm -rf ./* ./.github ./.streamlit 2>/dev/null; ls -la   # clear old files

# 3. Copy the NEW project files into this folder
#    (unzip the downloaded kenya-data-explorer-dashboard.zip and copy its
#     CONTENTS — not the folder itself — into this directory)
cp -R /path/to/unzipped/* .

# 4. Verify the structure matches the README
find . -path ./.git -prune -o -type f -print | sort
#    You must see:  src/app.py   data/kenya_dashboard.csv   tests/test_*.py
#                   .github/workflows/ci.yml   .streamlit/config.toml

# 5. Test before pushing
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check src tests
pytest
streamlit run src/app.py        # open http://localhost:8501

# 6. Commit and push
git add -A
git status                      # sanity-check: no REPO_SETUP.md, no .venv, no __pycache__
git commit -m "Restore src/data/tests structure, add CI, harden validation, docs"
git push origin main
```

## Option B — Fresh repo

```bash
unzip kenya-data-explorer-dashboard.zip
cd kenya-data-explorer-dashboard
git init -b main
git add -A
git commit -m "Kenya Data Explorer Dashboard v1.1.0"
git remote add origin https://github.com/lordlucky-254/kenya-data-explorer-dashboard.git
git push -u origin main
```

## After pushing (2 minutes on GitHub.com)

1. **Repo → ⚙️ Settings (gear icon) → About:** add topics
   `python`, `pandas`, `streamlit`, `plotly`, `data-visualization`, `kenya`, `dashboard`.
2. **Deploy live (free):** go to [share.streamlit.io](https://share.streamlit.io),
   select this repo, set **Main file path** to `src/app.py`, click **Deploy**.
3. Paste the live app URL into the repo's **Website** field and the top of `README.md`.
4. Confirm the green ✅ on the **Actions** tab (CI runs Ruff + Pytest on Python 3.11 & 3.12).
