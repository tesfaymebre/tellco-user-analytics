# TellCo User Analytics

Telecom user analytics for the **10 Academy Week 1** challenge — modular Python package, Jupyter notebooks, Streamlit dashboard, and CI/CD deployment.

**Author:** Tesfamariam Asfaw  
**Repository:** [github.com/tesfaymebre/tellco-user-analytics](https://github.com/tesfaymebre/tellco-user-analytics)

## What this project does

Analyses ~150k telecom xDR sessions to answer: **Should TellCo be acquired?**

| Task | Deliverable |
|------|-------------|
| Task 1 | [Streamlit source code review](docs/reports/task1_streamlit_source_review.md) |
| Task 2 | User overview, handsets, EDA, PCA |
| Task 3 | Engagement clustering (k-means, k=3) |
| Task 4 | Network experience / QoS clustering (k=3) |
| Task 5 | Satisfaction scoring, regression, MySQL export, MLflow |
| Dashboard | Multipage Streamlit app with custom CSS/JS |
| DevOps | pytest, ruff, GitHub Actions, Dockerfile |

## Quick start

```bash
make setup          # venv, deps, .env, PostgreSQL + data load
make test           # 26 unit tests
make dashboard      # Streamlit → http://127.0.0.1:8501
make mlflow-ui      # MLflow  → http://127.0.0.1:5000
```

Place `telecom.sql` in the project root before `make setup`. See the [Setup Guide](docs/setup.md).

## Documentation

Full documentation lives in [`docs/`](docs/README.md):

| Guide | Topics |
|-------|--------|
| [Setup](docs/setup.md) | Install, env vars, troubleshooting |
| [Architecture](docs/architecture.md) | Repo layout, data flow, modules |
| [Analysis Tasks](docs/analysis-tasks.md) | Tasks 2–5 methodology and findings |
| [Dashboard](docs/dashboard.md) | Streamlit pages, UI, caching |
| [Database](docs/database.md) | PostgreSQL, MySQL, feature store |
| [Deployment](docs/deployment.md) | Docker, CI/CD, Streamlit Cloud |
| [MLflow](docs/mlflow.md) | Experiment tracking |
| [Testing](docs/testing.md) | pytest, ruff, CI |

## Project structure

```
src/tellco_user_analytics/   ← pip-installable analysis package
app/                         ← Streamlit dashboard (separate)
notebooks/                   ← Jupyter notebooks (Tasks 2–5)
tests/                       ← pytest suite
scripts/                     ← DB loader + feature store SQL
docs/                        ← documentation
```

## Key results

- **106,856** unique customers
- Top manufacturers: Apple, Samsung, Huawei
- Gaming ≈ **0.97** correlation with total data
- Engagement elbow: **k = 3**; Cluster 0 = highest engagement
- Experience: Cluster 2 = poorest QoS; Oppo A37F = lowest throughput
- Satisfaction: distance-based scores + LinearRegression (R² logged in MLflow)

## Makefile commands

```bash
make help              # list all targets
make ci                # lint + format + test
make db-up / db-load   # PostgreSQL
make mysql-up          # MySQL
make dashboard-docker  # full Docker stack
make docker-build      # build dashboard image
make feature-store-init
make notebook
```

## Branches

| Branch | Content |
|--------|---------|
| `main` | Stable baseline |
| `task-3/user-engagement` | Task 3 |
| `task-4/user-experience` | Task 4 |
| `task-5/user-satisfaction` | Task 5 + dashboard |
| `docs/project-documentation` | Documentation |

## License

10 Academy Week 1 challenge submission.
