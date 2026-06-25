"""Export satisfaction scores to MySQL (Task 5.6)."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from tellco_user_analytics.config import MySQLConfig, get_mysql_config

SATISFACTION_TABLE = "user_satisfaction_scores"

CREATE_TABLE_SQL = text(
    f"""
    CREATE TABLE IF NOT EXISTS {SATISFACTION_TABLE} (
        customer_id BIGINT PRIMARY KEY,
        engagement_score DOUBLE,
        experience_score DOUBLE,
        satisfaction_score DOUBLE,
        satisfaction_cluster INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)


def get_mysql_engine(config: MySQLConfig | None = None) -> Engine:
    """Return a SQLAlchemy engine for the MySQL analytics database."""
    config = config or get_mysql_config()
    return create_engine(config.url)


def export_satisfaction_scores(
    df: pd.DataFrame,
    engine: Engine | None = None,
    if_exists: str = "replace",
) -> int:
    """
    Write satisfaction scores to MySQL and return rows exported.

    Expected columns: customer_id, engagement_score, experience_score,
    satisfaction_score, satisfaction_cluster (optional).
    """
    engine = engine or get_mysql_engine()
    export_cols = [
        "customer_id",
        "engagement_score",
        "experience_score",
        "satisfaction_score",
    ]
    if "satisfaction_cluster" in df.columns:
        export_cols.append("satisfaction_cluster")

    payload = df[export_cols].copy()

    with engine.begin() as conn:
        conn.execute(CREATE_TABLE_SQL)
        payload.to_sql(SATISFACTION_TABLE, conn, if_exists=if_exists, index=False)

    return len(payload)


def verify_mysql_export(engine: Engine | None = None, limit: int = 10) -> pd.DataFrame:
    """Return sample rows from the satisfaction export table."""
    engine = engine or get_mysql_engine()
    query = text(f"SELECT * FROM {SATISFACTION_TABLE} LIMIT :limit")
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"limit": limit})
