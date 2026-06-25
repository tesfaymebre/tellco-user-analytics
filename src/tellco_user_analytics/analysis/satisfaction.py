"""Customer satisfaction scoring and modelling (Task 5)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from tellco_user_analytics.analysis.engagement import (
    ENGAGEMENT_FEATURES,
    ClusterResult,
    less_engaged_cluster_id,
)
from tellco_user_analytics.analysis.experience import (
    EXPERIENCE_FEATURES,
    ExperienceClusterResult,
    worst_experience_cluster_id,
)
from tellco_user_analytics.analysis.tracking import (
    ExperimentTracker,
    TrackingResult,
    get_artifacts_dir,
)


@dataclass
class RegressionResult:
    model: Pipeline
    metrics: dict[str, float]
    artifact_path: Path


def _cluster_centroid(
    transformed: np.ndarray,
    labels: np.ndarray,
    cluster_id: int,
) -> np.ndarray:
    """Mean position of a cluster in the transformed feature space."""
    mask = labels == cluster_id
    return transformed[mask].mean(axis=0)


def engagement_scores(
    engagement_df: pd.DataFrame,
    cluster_result: ClusterResult,
) -> pd.Series:
    """
    Euclidean distance from each user to the less-engaged cluster centroid.

    Higher score → farther from low-engagement group → more engaged.
    """
    pipeline = cluster_result.pipeline
    features = ENGAGEMENT_FEATURES
    transformed = pipeline.named_steps["normalize"].transform(engagement_df[features])
    labels = cluster_result.labels
    less_engaged = less_engaged_cluster_id(cluster_result.data)
    centroid = _cluster_centroid(transformed, labels, less_engaged)
    distances = euclidean_distances(transformed, centroid.reshape(1, -1)).ravel()
    return pd.Series(distances, index=engagement_df.index, name="engagement_score")


def experience_scores(
    experience_df: pd.DataFrame,
    cluster_result: ExperienceClusterResult,
) -> pd.Series:
    """
    Euclidean distance from each user to the worst-experience cluster centroid.

    Higher score → farther from poor QoS group → better experience.
    """
    pipeline = cluster_result.pipeline
    features = EXPERIENCE_FEATURES
    transformed = pipeline.named_steps["scale"].transform(experience_df[features])
    labels = cluster_result.labels
    worst = worst_experience_cluster_id(cluster_result.data)
    centroid = _cluster_centroid(transformed, labels, worst)
    distances = euclidean_distances(transformed, centroid.reshape(1, -1)).ravel()
    return pd.Series(distances, index=experience_df.index, name="experience_score")


def build_satisfaction_table(
    engagement_df: pd.DataFrame,
    experience_df: pd.DataFrame,
    engagement_cluster_result: ClusterResult,
    experience_cluster_result: ExperienceClusterResult,
) -> pd.DataFrame:
    """Combine engagement & experience scores into a satisfaction table (Task 5.1–5.2)."""
    eng_scores = engagement_scores(engagement_df, engagement_cluster_result)
    exp_scores = experience_scores(experience_df, experience_cluster_result)

    table = pd.DataFrame(
        {
            "customer_id": engagement_df["customer_id"].values,
            "engagement_score": eng_scores.values,
            "experience_score": exp_scores.values,
        }
    )
    table["satisfaction_score"] = (table["engagement_score"] + table["experience_score"]) / 2
    return table


def top_satisfied_customers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N customers by satisfaction score (Task 5.2)."""
    return df.nlargest(n, "satisfaction_score").reset_index(drop=True)[
        ["customer_id", "engagement_score", "experience_score", "satisfaction_score"]
    ]


def train_satisfaction_regressor(
    engagement_df: pd.DataFrame,
    experience_df: pd.DataFrame,
    satisfaction_df: pd.DataFrame,
    artifact_dir: str | Path | None = None,
    random_state: int = 42,
) -> RegressionResult:
    """
    Train a linear regression model to predict satisfaction (Task 5.3).

    Features: raw engagement + experience metrics.
    """
    features = ENGAGEMENT_FEATURES + EXPERIENCE_FEATURES
    merged = engagement_df.merge(
        experience_df[["customer_id", *EXPERIENCE_FEATURES]],
        on="customer_id",
    ).merge(satisfaction_df[["customer_id", "satisfaction_score"]], on="customer_id")

    X = merged[features]
    y = merged["satisfaction_score"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )

    model = Pipeline([("regressor", LinearRegression())])
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    metrics = {
        "r2": float(r2_score(y_test, predictions)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
    }

    artifact_path = Path(artifact_dir) if artifact_dir else get_artifacts_dir() / "models"
    artifact_path.mkdir(parents=True, exist_ok=True)
    model_file = artifact_path / "satisfaction_regressor.joblib"
    joblib.dump(model, model_file)

    return RegressionResult(model=model, metrics=metrics, artifact_path=model_file)


def cluster_satisfaction_scores(
    satisfaction_df: pd.DataFrame,
    k: int = 2,
    random_state: int = 42,
) -> pd.DataFrame:
    """K-means on engagement & experience scores (Task 5.4)."""
    result = satisfaction_df.copy()
    score_features = ["engagement_score", "experience_score"]
    model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    result["satisfaction_cluster"] = model.fit_predict(result[score_features])
    return result


def satisfaction_cluster_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Average satisfaction and experience scores per cluster (Task 5.5)."""
    return (
        df.groupby("satisfaction_cluster")[["satisfaction_score", "experience_score"]]
        .mean()
        .round(4)
    )


def _as_tracking_result(value: TrackingResult | Path) -> TrackingResult:
    """Support older callers that returned only a JSON path."""
    if isinstance(value, TrackingResult):
        return value
    return TrackingResult(json_path=Path(value))


def run_tracked_regression(
    engagement_df: pd.DataFrame,
    experience_df: pd.DataFrame,
    satisfaction_df: pd.DataFrame,
    tracker: ExperimentTracker | None = None,
) -> tuple[RegressionResult, TrackingResult]:
    """Train regressor and persist experiment metadata to JSON + MLflow (Task 5.7)."""
    tracker = tracker or ExperimentTracker()
    run = tracker.start_run(
        source="tellco_user_analytics.analysis.satisfaction",
        model_name="LinearRegression",
        parameters={"test_size": 0.2, "features": ENGAGEMENT_FEATURES + EXPERIENCE_FEATURES},
    )
    result = train_satisfaction_regressor(engagement_df, experience_df, satisfaction_df)
    tracking = _as_tracking_result(
        tracker.end_run(
            run,
            metrics=result.metrics,
            artifacts=[str(result.artifact_path)],
            model=result.model,
        )
    )
    return result, tracking
