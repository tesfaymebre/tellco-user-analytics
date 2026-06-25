"""PostgreSQL feature store — curated tables for dashboard and training."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from tellco_user_analytics.db.connection import get_engine

FEATURE_STORE_SCHEMA = "feature_store"
FEATURE_STORE_SQL = Path(__file__).resolve().parents[3] / "scripts" / "feature_store.sql"


def init_feature_store(engine: Engine | None = None) -> None:
    """Create feature_store schema and tables if they do not exist."""
    engine = engine or get_engine()
    sql = FEATURE_STORE_SQL.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))


def _replace_table(
    engine: Engine,
    table: str,
    df: pd.DataFrame,
    columns: list[str],
) -> int:
    payload = df[columns].copy()
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {FEATURE_STORE_SCHEMA}.{table}"))
        payload.to_sql(
            table,
            conn,
            schema=FEATURE_STORE_SCHEMA,
            if_exists="append",
            index=False,
        )
    return len(payload)


def sync_engagement_features(
    engagement_df: pd.DataFrame,
    cluster_labels: pd.Series | None = None,
    engine: Engine | None = None,
) -> int:
    """Upsert engagement features into the feature store."""
    engine = engine or get_engine()
    init_feature_store(engine)

    payload = engagement_df[
        ["customer_id", "session_count", "total_duration_ms", "total_traffic_bytes"]
    ].copy()
    if cluster_labels is not None:
        payload["engagement_cluster"] = cluster_labels.values
    else:
        payload["engagement_cluster"] = None

    return _replace_table(
        engine,
        "user_engagement",
        payload,
        list(payload.columns),
    )


def sync_experience_features(
    experience_df: pd.DataFrame,
    cluster_labels: pd.Series | None = None,
    engine: Engine | None = None,
) -> int:
    """Upsert experience features into the feature store."""
    engine = engine or get_engine()
    init_feature_store(engine)

    payload = experience_df[
        [
            "customer_id",
            "avg_tcp_retrans_bytes",
            "avg_rtt_ms",
            "avg_throughput_kbps",
            "handset_type",
        ]
    ].copy()
    if cluster_labels is not None:
        payload["experience_cluster"] = cluster_labels.values
    else:
        payload["experience_cluster"] = None

    return _replace_table(
        engine,
        "user_experience",
        payload,
        list(payload.columns),
    )


def sync_satisfaction_features(
    satisfaction_df: pd.DataFrame,
    engine: Engine | None = None,
) -> int:
    """Upsert satisfaction scores into the feature store."""
    engine = engine or get_engine()
    init_feature_store(engine)

    columns = [
        "customer_id",
        "engagement_score",
        "experience_score",
        "satisfaction_score",
    ]
    payload = satisfaction_df[columns].copy()
    if "satisfaction_cluster" in satisfaction_df.columns:
        payload["satisfaction_cluster"] = satisfaction_df["satisfaction_cluster"]
    else:
        payload["satisfaction_cluster"] = None

    return _replace_table(
        engine,
        "user_satisfaction",
        payload,
        list(payload.columns),
    )


def read_feature_table(table: str, engine: Engine | None = None) -> pd.DataFrame:
    """Load a feature store table into a DataFrame."""
    engine = engine or get_engine()
    query = text(f"SELECT * FROM {FEATURE_STORE_SCHEMA}.{table}")
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
