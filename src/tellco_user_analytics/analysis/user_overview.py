"""Per-user aggregation for Task 2.1 — application behaviour overview."""

from __future__ import annotations

import pandas as pd

from tellco_user_analytics.data.columns import (
    APPLICATIONS,
    BEARER_ID,
    DURATION_MS,
    TOTAL_DL,
    TOTAL_UL,
    USER_ID,
)


def aggregate_user_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate xDR session data to one row per customer (MSISDN).

    Computes:
    - number of xDR sessions
    - total session duration (ms)
    - total download / upload bytes
    - total bytes (DL + UL) per application
    """
    user_df = df.copy()

    # Per-application total bytes (DL + UL) at session level
    for app_name, (dl_col, ul_col) in APPLICATIONS.items():
        user_df[app_name] = user_df[dl_col].fillna(0) + user_df[ul_col].fillna(0)

    agg_spec: dict[str, str] = {
        BEARER_ID: "count",
        DURATION_MS: "sum",
        TOTAL_DL: "sum",
        TOTAL_UL: "sum",
    }
    for app_name in APPLICATIONS:
        agg_spec[app_name] = "sum"

    aggregated = user_df.groupby(USER_ID, as_index=False).agg(agg_spec)
    aggregated = aggregated.rename(
        columns={
            BEARER_ID: "session_count",
            DURATION_MS: "total_duration_ms",
            TOTAL_DL: "total_dl_bytes",
            TOTAL_UL: "total_ul_bytes",
        }
    )
    aggregated["total_data_bytes"] = aggregated["total_dl_bytes"] + aggregated["total_ul_bytes"]
    return aggregated
