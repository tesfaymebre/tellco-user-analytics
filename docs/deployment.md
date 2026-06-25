# Deployment

## Docker

### Dockerfile

Builds a production Streamlit image:

```bash
make docker-build     # tags tellco-dashboard:latest
```

Image contents:

- Python 3.11-slim
- Package installed as `tellco-user-analytics[dashboard]`
- Exposes port **8501**
- Health check: `/_stcore/health`

### Docker Compose full stack

```bash
make db-load              # load data from host (one-time)
make dashboard-docker     # postgres + mysql + dashboard
```

Services in `docker-compose.yml`:

| Service | Port | Image |
|---------|------|-------|
| postgres | 5433→5432 | postgres:14 |
| mysql | 3307→3306 | mysql:8.0 |
| dashboard | 8501→8501 | built from Dockerfile |

> **Note:** `telecom.sql` is gitignored (~57 MB). Load it on the host before starting the dashboard container, or mount it into PostgreSQL init.

### Manual run

```bash
docker run -p 8501:8501 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=5433 \
  -e DB_NAME=tellco \
  -e DB_USER=postgres \
  -e DB_PASSWORD=tellco_dev \
  tellco-dashboard:latest
```

## GitHub Actions CI

File: `.github/workflows/ci.yml`

**Triggers:** push to `main` / `task-*`, PRs to `main`

| Job | Steps |
|-----|-------|
| `test` | Python 3.10 + 3.11 → `pip install -e ".[dev]"` → `pytest` |
| `lint` | ruff check + format on `src`, `tests`, `app` |

Run locally:

```bash
make ci    # lint + format-check + test
```

## GitHub Actions CD

File: `.github/workflows/deploy.yml`

**Triggers:** push to `main` / `task-*`, manual dispatch

| Job | Action |
|-----|--------|
| `docker-build` | Build image, run health check |
| `docker-push` | Push to `ghcr.io/<repo>/tellco-dashboard:latest` (main only) |

Pull from GHCR:

```bash
docker pull ghcr.io/tesfaymebre/tellco-user-analytics/tellco-dashboard:latest
```

## Streamlit Cloud

Recommended for challenge submission (free hosting + live URL).

### Steps

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select repository and branch
4. **Main file path:** `app/Home.py`
5. **Requirements:** `requirements.txt` (includes streamlit)

### Secrets (Settings → Secrets)

Add as TOML or individual keys:

```toml
DB_HOST = "your-postgres-host"
DB_PORT = "5432"
DB_NAME = "tellco"
DB_USER = "postgres"
DB_PASSWORD = "your-password"

MYSQL_HOST = "your-mysql-host"
MYSQL_PORT = "3306"
MYSQL_DB = "tellco_analytics"
MYSQL_USER = "root"
MYSQL_PASSWORD = "your-password"
```

> Streamlit Cloud does not include PostgreSQL. Options:
> - Use a free hosted PostgreSQL (Neon, Supabase, ElephantSQL)
> - Pre-compute features and serve from MySQL only
> - Deploy the full Docker stack on Railway / Render instead

### Alternative hosts

| Platform | Best for |
|----------|----------|
| [Streamlit Cloud](https://streamlit.io/cloud) | Easiest Streamlit deploy |
| [Railway](https://railway.app) | Docker Compose + databases |
| [Render](https://render.com) | Docker web service |
| [Heroku](https://heroku.com) | Container deploy (paid tier) |

## Submission checklist

- [ ] GitHub repo link with all code
- [ ] Dashboard screenshots (all 6 pages)
- [ ] Live deployed URL (Streamlit Cloud or Docker host)
- [ ] Task 1 report: `docs/reports/task1_streamlit_source_review.md`
- [ ] Feature store schema: `scripts/feature_store.sql`
- [ ] Dockerfile present and builds successfully
- [ ] CI/CD workflows in `.github/workflows/`
