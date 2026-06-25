"""Tests for user overview aggregation."""

import pandas as pd

from tellco_user_analytics.analysis.user_overview import aggregate_user_sessions
from tellco_user_analytics.data.columns import (
    APPLICATIONS,
    BEARER_ID,
    DURATION_MS,
    TOTAL_DL,
    TOTAL_UL,
    USER_ID,
)


def _sample_session_df() -> pd.DataFrame:
    row = {
        BEARER_ID: 1,
        USER_ID: 100,
        DURATION_MS: 1000,
        TOTAL_DL: 500,
        TOTAL_UL: 200,
    }
    for app, (dl, ul) in APPLICATIONS.items():
        row[dl] = 100
        row[ul] = 50
    return pd.DataFrame([row, {**row, BEARER_ID: 2, DURATION_MS: 2000}])


def test_aggregate_user_sessions_counts_and_sums():
    result = aggregate_user_sessions(_sample_session_df())
    assert len(result) == 1
    assert result.loc[0, "session_count"] == 2
    assert result.loc[0, "total_duration_ms"] == 3000
    assert result.loc[0, "total_data_bytes"] == 1400
