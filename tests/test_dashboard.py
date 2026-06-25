"""Tests for dashboard pipeline helpers and feature store."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from services.pipeline import AnalyticsBundle, purchase_recommendation  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

from tellco_user_analytics.analysis.satisfaction import RegressionResult  # noqa: E402
from tellco_user_analytics.db.feature_store import (  # noqa: E402
    FEATURE_STORE_SCHEMA,
    FEATURE_STORE_SQL,
)


def test_feature_store_sql_exists_and_defines_schema():
    assert FEATURE_STORE_SQL.is_file()
    sql = FEATURE_STORE_SQL.read_text(encoding="utf-8")
    assert FEATURE_STORE_SCHEMA in sql
    assert "user_engagement" in sql
    assert "user_experience" in sql
    assert "user_satisfaction" in sql


def test_purchase_recommendation_buy_signal():
    n = 20
    eng = pd.DataFrame(
        {
            "customer_id": range(n),
            "session_count": [5] * n,
            "total_duration_ms": [1000] * n,
            "total_traffic_bytes": [5000] * n,
            "cluster": [0] * n,
        }
    )
    exp = pd.DataFrame(
        {
            "customer_id": range(n),
            "avg_tcp_retrans_bytes": [1.0] * n,
            "avg_rtt_ms": [10.0] * n,
            "avg_throughput_kbps": [5000.0] * n,
            "handset_type": ["A"] * n,
            "cluster": [0] * n,
        }
    )
    sat = pd.DataFrame(
        {
            "customer_id": range(n),
            "engagement_score": [8000.0] * n,
            "experience_score": [8000.0] * n,
            "satisfaction_score": [8000.0] * n,
        }
    )

    class DummyCluster:
        def __init__(self, data: pd.DataFrame):
            self.data = data

    bundle = AnalyticsBundle(
        sessions=pd.DataFrame({"Handset Type": ["A"] * 5}),
        exp_sessions=pd.DataFrame(),
        engagement=eng,
        engagement_clusters=DummyCluster(eng),  # type: ignore[arg-type]
        experience=exp,
        experience_clusters=DummyCluster(exp),  # type: ignore[arg-type]
        satisfaction=sat,
        satisfaction_clustered=sat.assign(satisfaction_cluster=0),
        regression=RegressionResult(
            model=Pipeline([("regressor", LinearRegression())]),
            metrics={"r2": 0.9, "rmse": 1.0},
            artifact_path=Path("artifacts/models/test.joblib"),
        ),
    )

    rec = purchase_recommendation(bundle)
    assert rec["verdict"] == "BUY"
