"""Load xDR records from PostgreSQL into pandas DataFrames."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from tellco_user_analytics.data.columns import (
    APPLICATIONS,
    BEARER_ID,
    DURATION_MS,
    HANDSET_MANUFACTURER,
    HANDSET_TYPE,
    TOTAL_DL,
    TOTAL_UL,
    USER_ID,
)
from tellco_user_analytics.db.connection import get_engine

TABLE_NAME = "public.xdr_data"


def _quoted(columns: list[str]) -> str:
    """Build a comma-separated list of double-quoted SQL identifiers."""
    return ", ".join(f'"{col}"' for col in columns)


def load_xdr_sessions(engine: Engine | None = None) -> pd.DataFrame:
    """
    Load session-level xDR data needed for User Overview analysis.

    Returns one row per xDR session with user, handset, duration,
    total traffic, and per-application byte volumes.
    """
    engine = engine or get_engine()

    app_columns: list[str] = []
    for dl_col, ul_col in APPLICATIONS.values():
        app_columns.extend([dl_col, ul_col])

    columns = [
        BEARER_ID,
        USER_ID,
        DURATION_MS,
        HANDSET_MANUFACTURER,
        HANDSET_TYPE,
        TOTAL_DL,
        TOTAL_UL,
        *app_columns,
    ]

    query = text(f"SELECT {_quoted(columns)} FROM {TABLE_NAME}")
    return pd.read_sql(query, engine)
