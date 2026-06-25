# TellCo User Analytics — Documentation Index

Complete documentation for the 10 Academy Week 1 telecom analytics project.

| Document | Description |
|----------|-------------|
| [Setup Guide](setup.md) | Prerequisites, first-time install, environment variables |
| [Architecture](architecture.md) | Repository layout, design principles, data flow |
| [Analysis Tasks](analysis-tasks.md) | Tasks 2–5: methodology, modules, notebooks, key findings |
| [Dashboard](dashboard.md) | Streamlit app structure, pages, UI customisation |
| [Database & Feature Store](database.md) | PostgreSQL, MySQL, feature store schema |
| [Deployment](deployment.md) | Docker, CI/CD, Streamlit Cloud |
| [MLflow Tracking](mlflow.md) | Experiment logging and model artefacts |
| [Testing](testing.md) | Unit tests, local CI, quality checks |
| [Task 1 Report](reports/task1_streamlit_source_review.md) | Streamlit source code review (submission) |

## Project summary

TellCo User Analytics is a modular Python project that analyses ~150k telecom xDR sessions to support a **buy / hold / sell** acquisition recommendation. The work spans:

1. **Task 1** — Streamlit source code review ([report](reports/task1_streamlit_source_review.md))
2. **Task 2** — User overview, handsets, EDA, PCA
3. **Task 3** — User engagement clustering (k-means, k=3)
4. **Task 4** — Network experience / QoS clustering (k-means, k=3)
5. **Task 5** — Satisfaction scoring, regression, MySQL export, MLflow tracking
6. **Dashboard** — Multipage Streamlit app with custom CSS/JS
7. **DevOps** — pytest, ruff, GitHub Actions CI/CD, Dockerfile

## Quick commands

```bash
make setup       # first-time bootstrap
make test        # 26 unit tests
make ci          # lint + format + test
make dashboard   # http://127.0.0.1:8501
make mlflow-ui   # http://127.0.0.1:5000
```

## Branches

| Branch | Scope |
|--------|-------|
| `main` | Stable baseline |
| `task-3/user-engagement` | Engagement analysis |
| `task-4/user-experience` | Experience / QoS analysis |
| `task-5/user-satisfaction` | Satisfaction + dashboard |
| `docs/project-documentation` | This documentation set |
