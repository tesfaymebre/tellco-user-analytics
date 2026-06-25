# Testing

## Running tests

```bash
make test           # verbose pytest
make ci             # lint + format-check + test (mirrors GitHub Actions)
```

Current suite: **26 tests** across 8 test files.

## Test files

| File | Coverage |
|------|----------|
| `test_config.py` | Environment config loading |
| `test_user_overview.py` | Session aggregation |
| `test_preprocessing.py` | Missing value + outlier treatment |
| `test_eda.py` | EDA helpers, PCA, deciles |
| `test_engagement.py` | Aggregation, k-means, elbow |
| `test_experience.py` | QoS aggregation, clustering |
| `test_satisfaction.py` | Scoring, regression, clustering |
| `test_dashboard.py` | Feature store SQL, purchase recommendation |

## Linting & formatting

```bash
make lint           # ruff check src tests app
make format         # auto-format + fix
make format-check   # verify without writing
```

Ruff config in `pyproject.toml`:

- Line length: 100
- Target: Python 3.10
- Rules: E, F, I, W

## CI matrix

GitHub Actions runs tests on **Python 3.10** and **3.11** (see `.github/workflows/ci.yml`).

## Writing new tests

Follow existing patterns:

```python
import pandas as pd
from tellco_user_analytics.analysis.engagement import aggregate_engagement

def test_aggregate_engagement_row_count(sample_xdr_df):
    result = aggregate_engagement(sample_xdr_df)
    assert "customer_id" in result.columns
    assert len(result) <= len(sample_xdr_df)
```

Dashboard helpers live under `app/services/` — tests add `app/` to `sys.path` (see `test_dashboard.py`).

## Pre-commit workflow

Before pushing:

```bash
make ci
```

This runs the same checks as the GitHub Actions pipeline.

## Docker build verification

```bash
make docker-build
```

Confirms the Dockerfile installs dependencies and the image builds successfully. Deploy workflow also runs a container health check on CI.
