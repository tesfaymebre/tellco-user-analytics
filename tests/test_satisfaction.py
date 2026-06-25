"""Tests for satisfaction analysis (Task 5)."""

import numpy as np
import pandas as pd

from tellco_user_analytics.analysis.engagement import (
    fit_engagement_clusters,
)
from tellco_user_analytics.analysis.experience import (
    fit_experience_clusters,
)
from tellco_user_analytics.analysis.satisfaction import (
    build_satisfaction_table,
    cluster_satisfaction_scores,
    engagement_scores,
    experience_scores,
    satisfaction_cluster_summary,
    top_satisfied_customers,
    train_satisfaction_regressor,
)
from tellco_user_analytics.analysis.tracking import ExperimentTracker


def _engagement_df(n: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "customer_id": range(n),
            "session_count": rng.integers(1, 5, n),
            "total_duration_ms": rng.integers(1000, 50000, n),
            "total_traffic_bytes": rng.integers(10000, 5000000, n),
        }
    )


def _experience_df(n: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    return pd.DataFrame(
        {
            "customer_id": range(n),
            "avg_tcp_retrans_bytes": rng.integers(0, 5000, n),
            "avg_rtt_ms": rng.uniform(10, 200, n),
            "avg_throughput_kbps": rng.uniform(100, 5000, n),
            "handset_type": ["Phone A"] * n,
        }
    )


def test_build_satisfaction_table_columns():
    eng = _engagement_df()
    exp = _experience_df()
    eng_clusters = fit_engagement_clusters(eng, k=3)
    exp_clusters = fit_experience_clusters(exp, k=3)
    table = build_satisfaction_table(eng, exp, eng_clusters, exp_clusters)

    assert {"engagement_score", "experience_score", "satisfaction_score"} <= set(table.columns)
    assert table["satisfaction_score"].equals(
        (table["engagement_score"] + table["experience_score"]) / 2
    )


def test_scores_are_non_negative():
    eng = _engagement_df()
    exp = _experience_df()
    eng_clusters = fit_engagement_clusters(eng, k=3)
    exp_clusters = fit_experience_clusters(exp, k=3)

    assert (engagement_scores(eng, eng_clusters) >= 0).all()
    assert (experience_scores(exp, exp_clusters) >= 0).all()


def test_top_satisfied_returns_n_rows():
    eng = _engagement_df()
    exp = _experience_df()
    table = build_satisfaction_table(
        eng,
        exp,
        fit_engagement_clusters(eng, k=3),
        fit_experience_clusters(exp, k=3),
    )
    top = top_satisfied_customers(table, n=5)
    assert len(top) == 5
    assert top["satisfaction_score"].is_monotonic_decreasing


def test_satisfaction_kmeans_two_clusters():
    eng = _engagement_df(40)
    exp = _experience_df(40)
    table = build_satisfaction_table(
        eng,
        exp,
        fit_engagement_clusters(eng, k=3),
        fit_experience_clusters(exp, k=3),
    )
    clustered = cluster_satisfaction_scores(table, k=2)
    summary = satisfaction_cluster_summary(clustered)
    assert len(summary) == 2


def test_regression_trains_and_returns_metrics():
    eng = _engagement_df(50)
    exp = _experience_df(50)
    table = build_satisfaction_table(
        eng,
        exp,
        fit_engagement_clusters(eng, k=3),
        fit_experience_clusters(exp, k=3),
    )
    result = train_satisfaction_regressor(eng, exp, table, artifact_dir="artifacts/test_models")
    assert "r2" in result.metrics
    assert result.artifact_path.exists()


def test_experiment_tracker_writes_json_and_mlflow(tmp_path):
    ml_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    tracker = ExperimentTracker(
        root=tmp_path / "runs",
        mlflow_tracking_uri=ml_uri,
        experiment_name="test-experiment",
    )
    run = tracker.start_run("test", "LinearRegression", {"k": 3})
    result = tracker.end_run(
        run,
        metrics={"r2": 0.9, "rmse": 0.1},
        artifacts=[],
    )
    assert result.json_path.exists()
    assert result.mlflow_run_id is not None
    assert (tmp_path / "mlflow.db").exists()
