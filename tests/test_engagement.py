"""Tests for engagement analysis (Task 3)."""

import pandas as pd

from tellco_user_analytics.analysis.engagement import (
    ENGAGEMENT_FEATURES,
    aggregate_engagement,
    cluster_summary_stats,
    elbow_analysis,
    fit_engagement_clusters,
    suggest_elbow_k,
    top_applications_by_traffic,
    top_customers_per_metric,
    top_users_per_application,
)
from tellco_user_analytics.data.columns import (
    APPLICATIONS,
    BEARER_ID,
    DURATION_MS,
    TOTAL_DL,
    TOTAL_UL,
    USER_ID,
)


def _session_df() -> pd.DataFrame:
    rows = []
    for user in [100, 100, 200, 300]:
        row = {
            BEARER_ID: len(rows) + 1,
            USER_ID: user,
            DURATION_MS: 1000,
            TOTAL_DL: 500,
            TOTAL_UL: 200,
        }
        for app, (dl, ul) in APPLICATIONS.items():
            row[dl] = 50
            row[ul] = 25
        rows.append(row)
    return pd.DataFrame(rows)


def test_aggregate_engagement_metrics():
    agg = aggregate_engagement(_session_df())
    assert len(agg) == 3
    user100 = agg.loc[agg["customer_id"] == 100].iloc[0]
    assert user100["session_count"] == 2
    assert user100["total_duration_ms"] == 2000
    assert user100["total_traffic_bytes"] == 1400


def test_top_customers_per_metric_returns_three_tables():
    agg = aggregate_engagement(_session_df())
    tops = top_customers_per_metric(agg, n=2)
    assert set(tops.keys()) == set(ENGAGEMENT_FEATURES)
    assert len(tops["session_count"]) == 2


def test_kmeans_produces_three_clusters():
    agg = aggregate_engagement(_session_df())
    result = fit_engagement_clusters(agg, k=3)
    assert len(result.data["cluster"].unique()) <= 3
    summary = cluster_summary_stats(result.data)
    assert "min" in summary.columns.get_level_values(1)


def test_top_users_per_application():
    agg = aggregate_engagement(_session_df())
    tops = top_users_per_application(agg, n=1)
    assert "Gaming" in tops
    assert len(tops["Gaming"]) == 1


def test_elbow_analysis_and_suggestion():
    rng = pd.DataFrame(
        {
            "customer_id": range(30),
            "session_count": range(30),
            "total_duration_ms": [i * 100 for i in range(30)],
            "total_traffic_bytes": [i * 50 for i in range(30)],
        }
    )
    elbow = elbow_analysis(rng, k_range=range(1, 6))
    assert len(elbow) == 5
    k = suggest_elbow_k(elbow)
    assert 2 <= k <= 5


def test_top_applications_by_traffic():
    agg = aggregate_engagement(_session_df())
    # All apps equal in fixture — still returns n apps
    top3 = top_applications_by_traffic(agg, n=3)
    assert len(top3) == 3
