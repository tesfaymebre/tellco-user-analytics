# Architecture

## Design principles

The project mirrors the modular layout recommended in the Task 1 Streamlit review:

- **`src/tellco_user_analytics/`** — reusable analysis package (pip-installable)
- **`notebooks/`** — orchestration and visualisation only
- **`app/`** — Streamlit dashboard (imports the package, no duplicated logic)
- **`tests/`** — pytest suite for the package and dashboard helpers

Business logic never lives in notebooks or Streamlit pages directly.

## Repository layout

```
tellco-user-analytics/
├── src/tellco_user_analytics/     # Core Python package
│   ├── analysis/                  # Task 2–5 business logic
│   ├── data/                      # Loaders + column constants
│   ├── db/                        # PostgreSQL, MySQL, feature store
│   └── config.py                  # Environment-based configuration
├── app/                           # Streamlit dashboard (separate app)
│   ├── Home.py
│   ├── pages/                     # Multipage routes
│   ├── components/                # Layout + Plotly charts
│   ├── services/                  # Cached analytics pipeline
│   └── static/                    # CSS + JS
├── notebooks/                     # Jupyter notebooks (Tasks 2–5)
├── tests/                         # pytest (26 tests)
├── scripts/
│   ├── load_database.sh           # Docker PG bootstrap
│   └── feature_store.sql          # PostgreSQL feature store DDL
├── docs/                          # Project documentation
├── .github/workflows/
│   ├── ci.yml                     # pytest + ruff
│   └── deploy.yml                 # Docker build + GHCR push
├── docker-compose.yml             # postgres, mysql, dashboard
├── Dockerfile                     # Streamlit production image
├── Makefile                       # Dev commands
└── pyproject.toml                 # Package metadata + dependencies
```

## Data flow

```
telecom.sql
    │
    ▼
PostgreSQL (public.xdr_data)          ← raw session-level xDR
    │
    ├── load_xdr_sessions()
    ├── load_xdr_experience_sessions()
    │
    ▼
Analysis modules (aggregate → cluster → score)
    │
    ├── engagement.py      → per-user engagement + k-means (k=3)
    ├── experience.py      → per-user QoS + k-means (k=3)
    └── satisfaction.py    → combined scores + regression
    │
    ├── PostgreSQL feature_store.*   ← curated features (dashboard + training)
    ├── MySQL user_satisfaction_scores ← Task 5.6 export
    ├── artifacts/models/            ← joblib regression model
    └── mlflow.db                    ← experiment tracking
    │
    ▼
Streamlit dashboard (app/) + notebooks (notebooks/)
```

## Package modules

### `data/`

| Module | Key exports |
|--------|-------------|
| `columns.py` | Canonical column names (`USER_ID`, `APPLICATIONS`, etc.) |
| `loader.py` | `load_xdr_sessions()`, `load_xdr_experience_sessions()` |

### `analysis/`

| Module | Task | Responsibility |
|--------|------|----------------|
| `handsets.py` | 2 | Top handsets, manufacturers, marketing summary |
| `user_overview.py` | 2 | Per-user session aggregation |
| `preprocessing.py` | 2, 4 | Missing value + IQR outlier treatment |
| `eda.py` | 2 | Variable overview, deciles, correlation, PCA |
| `engagement.py` | 3 | Engagement metrics, k-means, elbow method |
| `experience.py` | 4 | QoS metrics, handset breakdowns, k-means |
| `satisfaction.py` | 5 | Scores, regression, satisfaction clustering |
| `tracking.py` | 5 | JSON + MLflow experiment logging |

### `db/`

| Module | Purpose |
|--------|---------|
| `connection.py` | PostgreSQL SQLAlchemy engine |
| `mysql_export.py` | Satisfaction scores → MySQL |
| `feature_store.py` | PostgreSQL feature store sync |

## Dashboard architecture

```
app/Home.py
    └── services/cache.py          @st.cache_data wrappers
            └── services/pipeline.py  orchestrates package calls
                    └── tellco_user_analytics.*

app/pages/*.py                     one page per task + business insights
app/components/layout.py           CSS/JS injection, KPI cards
app/components/charts.py           Plotly chart builders
app/static/styles.css              dark glass UI theme
```

Streamlit multipage routing: files in `app/pages/` appear automatically in the sidebar.

## CI/CD pipeline

```
Push / PR
    │
    ├── ci.yml
    │     ├── test (Python 3.10, 3.11) → pytest
    │     └── lint → ruff check + format
    │
    └── deploy.yml (main branch)
          ├── docker build + health check
          └── push to ghcr.io/<repo>/tellco-dashboard
```

## Git branching strategy

Features were developed on task branches and merged toward `main`:

- `task-3/user-engagement`
- `task-4/user-experience`
- `task-5/user-satisfaction` (includes dashboard)
- `docs/project-documentation` (this documentation)
