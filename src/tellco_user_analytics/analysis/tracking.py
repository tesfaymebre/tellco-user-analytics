"""Experiment tracking with JSON logs and MLflow (Task 5.7)."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn


def _git_revision() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from *start* until pyproject.toml is found."""
    current = (start or Path.cwd()).resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").exists():
            return path
    return current


def get_artifacts_dir() -> Path:
    """Project-root artifacts directory (works when cwd is notebooks/)."""
    override = os.getenv("TELLCO_ARTIFACTS_DIR")
    if override:
        return Path(override).resolve()
    return find_project_root() / "artifacts"


@dataclass
class ExperimentRun:
    """Metadata captured for each model training run."""

    run_id: str
    source: str
    model_name: str
    parameters: dict[str, Any]
    metrics: dict[str, float]
    artifacts: list[str] = field(default_factory=list)
    code_version: str = field(default_factory=_git_revision)
    started_at: str = ""
    ended_at: str = ""
    mlflow_run_id: str | None = None
    mlflow_experiment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrackingResult:
    """Paths and ids returned after logging a run."""

    json_path: Path
    mlflow_run_id: str | None = None
    mlflow_experiment: str | None = None
    mlflow_tracking_uri: str | None = None


class ExperimentTracker:
    """
    Persist run metadata as JSON and log to MLflow.

    MLflow tracking URI defaults to ``<project_root>/mlruns``.
    """

    def __init__(
        self,
        root: str | Path | None = None,
        mlflow_tracking_uri: str | Path | None = None,
        experiment_name: str = "tellco-satisfaction",
    ):
        project_root = find_project_root()
        self.root = Path(root) if root else get_artifacts_dir() / "runs"
        self.root.mkdir(parents=True, exist_ok=True)

        default_db = project_root / "mlflow.db"
        uri = mlflow_tracking_uri or os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{default_db}")
        self.mlflow_tracking_uri = str(uri)
        self.experiment_name = experiment_name

        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment(self.experiment_name)

        self._mlflow_active = False

    def start_run(self, source: str, model_name: str, parameters: dict[str, Any]) -> ExperimentRun:
        now = datetime.now(timezone.utc).isoformat()
        run_id = now.replace(":", "-").replace(".", "-")

        mlflow.start_run(run_name=run_id, tags={"source": source, "model_name": model_name})
        self._mlflow_active = True
        mlflow.set_tag("code_version", _git_revision())
        mlflow.log_params(_flatten_params(parameters))

        return ExperimentRun(
            run_id=run_id,
            source=source,
            model_name=model_name,
            parameters=parameters,
            metrics={},
            started_at=now,
            mlflow_experiment=self.experiment_name,
        )

    def end_run(
        self,
        run: ExperimentRun,
        metrics: dict[str, float],
        artifacts: list[str],
        model: Any | None = None,
    ) -> TrackingResult:
        run.metrics = metrics
        run.artifacts = artifacts
        run.ended_at = datetime.now(timezone.utc).isoformat()

        if self._mlflow_active:
            for key, value in metrics.items():
                mlflow.log_metric(key, value)
            for artifact_path in artifacts:
                path = Path(artifact_path)
                if path.is_file():
                    mlflow.log_artifact(str(path))
            if model is not None:
                mlflow.sklearn.log_model(model, artifact_path="model")
            active = mlflow.active_run()
            if active is not None:
                run.mlflow_run_id = active.info.run_id
            mlflow.end_run()
            self._mlflow_active = False

        json_path = self.root / f"{run.run_id}.json"
        json_path.write_text(json.dumps(run.to_dict(), indent=2))

        return TrackingResult(
            json_path=json_path,
            mlflow_run_id=run.mlflow_run_id,
            mlflow_experiment=self.experiment_name,
            mlflow_tracking_uri=self.mlflow_tracking_uri,
        )


def _flatten_params(parameters: dict[str, Any]) -> dict[str, str | int | float]:
    """MLflow params must be scalars — join list values."""
    flat: dict[str, str | int | float] = {}
    for key, value in parameters.items():
        if isinstance(value, (str, int, float)):
            flat[key] = value
        else:
            flat[key] = str(value)
    return flat
