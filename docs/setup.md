# Setup Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Runtime |
| Docker & Docker Compose | latest | PostgreSQL + MySQL |
| Git | latest | Version control |
| `telecom.sql` | ~57 MB | xDR dataset (not in repo — load locally) |

Place `telecom.sql` in the project root before running `make db-load`.

## First-time setup

```bash
git clone https://github.com/tesfaymebre/tellco-user-analytics.git
cd tellco-user-analytics
make setup
```

`make setup` runs:

1. `make install-dev` — creates `.venv`, installs `tellco-user-analytics[dev]`
2. `make env` — copies `.env.example` → `.env`
3. `make db-load` — starts PostgreSQL via Docker and loads `telecom.sql`

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Verify the database:

```bash
make db-verify    # expect ~150,001 rows in xdr_data
make test         # expect 26 passed
```

## Environment variables

Copy from `.env.example`:

```env
# PostgreSQL (source data)
DB_HOST=localhost
DB_PORT=5433          # host port mapped in docker-compose
DB_NAME=tellco
DB_USER=postgres
DB_PASSWORD=tellco_dev

# MySQL (satisfaction export — Task 5.6)
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_DB=tellco_analytics
MYSQL_USER=root
MYSQL_PASSWORD=tellco_dev
```

Optional overrides:

| Variable | Default | Purpose |
|----------|---------|---------|
| `TELLCO_ARTIFACTS_DIR` | `<project_root>/artifacts` | Model / run output directory |
| `MLFLOW_TRACKING_URI` | `sqlite:///<project_root>/mlflow.db` | MLflow backend store |

## Installing optional extras

```bash
pip install -e ".[dev]"         # pytest, ruff, jupyter
pip install -e ".[dashboard]"   # streamlit
pip install -e ".[notebooks]"   # jupyter only
```

## Database services

```bash
make db-up          # start PostgreSQL (+ MySQL if configured)
make mysql-up       # start MySQL only
make db-psql        # interactive psql shell
make db-reset       # wipe volumes (destructive)
```

## Notebooks

```bash
make notebook       # launches Jupyter from notebooks/
```

Run notebooks in order:

1. `01_user_overview_handsets.ipynb`
2. `02_user_overview_eda.ipynb`
3. `03_user_engagement.ipynb`
4. `04_user_experience.ipynb`
5. `05_user_satisfaction.ipynb`

Each notebook imports from `tellco_user_analytics` — no inline SQL or duplicated business logic.

## Dashboard

```bash
make dashboard      # Streamlit at http://127.0.0.1:8501
```

Requires PostgreSQL with loaded data. MySQL is optional (needed for satisfaction export page).

## Feature store

```bash
make feature-store-init    # creates PostgreSQL feature_store schema
```

Or apply SQL directly:

```bash
docker compose exec postgres psql -U postgres -d tellco -f /path/to/scripts/feature_store.sql
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Connection refused` on DB | Run `make db-up` and check `.env` port is `5433` |
| `telecom.sql not found` | Download dataset and place in project root |
| Port 5432 in use | docker-compose maps host `5433` → container `5432` |
| Stale notebook imports | Restart kernel or re-run `pip install -e ".[dev]"` |
| Dashboard cache stale | Home page → "Clear cache & reload" |
