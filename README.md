# TellCo User Analytics

Telecom user analytics for the 10 Academy Week 1 challenge — modular Python package, Jupyter notebooks, and Streamlit dashboard.

## Quick start

```bash
make setup          # venv, deps, .env, PostgreSQL + data load
make test           # run unit tests
make dashboard      # Streamlit UI → http://127.0.0.1:8501
```

## Dashboard (Streamlit)

The dashboard lives in `app/` — separate from the analysis package in `src/`:

```
app/
  Home.py              # landing page
  pages/               # multipage routes (Tasks 2–5 + insights)
  components/          # layout + Plotly charts
  services/            # cached analytics pipeline
  static/              # custom CSS + JS
```

```bash
make dashboard                    # local dev
make docker-build                 # build image
make dashboard-docker             # full stack via docker compose
```

## Feature store

PostgreSQL schema: `scripts/feature_store.sql` → schema `feature_store` with tables for engagement, experience, and satisfaction features.

```bash
make feature-store-init
```

MySQL export (Task 5.6): table `user_satisfaction_scores` via `tellco_user_analytics.db.mysql_export`.

## Deployment

- **Dockerfile** — production Streamlit image (`tellco-dashboard`)
- **CI** — `.github/workflows/ci.yml` (pytest + ruff)
- **CD** — `.github/workflows/deploy.yml` (Docker build + push to GHCR on `main`)

### Streamlit Cloud

1. Connect this repo at [share.streamlit.io](https://share.streamlit.io)
2. Main file: `app/Home.py`
3. Add secrets for `DB_*` and `MYSQL_*` env vars (or use hosted PostgreSQL/MySQL)

## MLflow

```bash
make mlflow-ui   # http://127.0.0.1:5000
```
