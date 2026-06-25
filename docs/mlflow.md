# MLflow Experiment Tracking

Task 5.7 requires logging model training runs. The project uses **MLflow** alongside local JSON logs.

## Quick start

```bash
make mlflow-ui    # http://127.0.0.1:5000
```

## Configuration

| Setting | Location | Default |
|---------|----------|---------|
| Backend store | `MLFLOW_TRACKING_URI` env var | `sqlite:///mlflow.db` (project root) |
| Experiment name | `ExperimentTracker` | `tellco-satisfaction` |
| Model artefact | `artifacts/models/satisfaction_regressor.joblib` | gitignored |

Override artefacts directory:

```bash
export TELLCO_ARTIFACTS_DIR=/path/to/artifacts
```

## Usage in code

```python
from tellco_user_analytics.analysis.satisfaction import run_tracked_regression

result, tracking = run_tracked_regression(engagement, experience, satisfaction)

print(tracking.json_path)           # local JSON log
print(tracking.mlflow_run_id)         # MLflow run UUID
print(tracking.mlflow_experiment)     # tellco-satisfaction
print(tracking.mlflow_tracking_uri)   # sqlite:///.../mlflow.db
print(result.metrics)                 # {'r2': ..., 'rmse': ...}
print(result.artifact_path)           # joblib model path
```

## What gets logged

Each run records:

| Field | Content |
|-------|---------|
| Parameters | `test_size`, feature list, model name |
| Metrics | R², RMSE |
| Artefacts | JSON run log, joblib model |
| Tags | git revision, source module, timestamp |

## TrackingResult dataclass

```python
@dataclass
class TrackingResult:
    json_path: Path
    mlflow_run_id: str | None
    mlflow_experiment: str | None
    mlflow_tracking_uri: str | None
```

## Notebook usage

In `notebooks/05_user_satisfaction.ipynb`:

```python
reg_result, tracking = run_tracked_regression(engagement, experience, satisfaction)
print("MLflow run id:", tracking.mlflow_run_id)
```

If you see `AttributeError: 'PosixPath' object has no attribute 'json_path'`, restart the Jupyter kernel and re-run the import cell (stale module cache).

## Files (gitignored)

```
mlflow.db          # SQLite tracking backend
mlruns/            # legacy file store (not used with sqlite backend)
artifacts/
  models/satisfaction_regressor.joblib
  runs/<timestamp>.json
```

## Viewing experiments

1. Train a model (notebook cell or dashboard pipeline)
2. Run `make mlflow-ui`
3. Open http://127.0.0.1:5000
4. Select experiment **tellco-satisfaction**
5. Compare runs, view metrics, download model artefact
