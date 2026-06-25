"""Tests for experience analysis (Task 4)."""

import pandas as pd

from tellco_user_analytics.analysis.experience import (
    aggregate_experience,
    cluster_labels_from_stats,
    describe_experience_clusters,
    fit_experience_clusters,
    throughput_by_handset,
    top_bottom_frequent,
)
from tellco_user_analytics.data.columns import (
    HANDSET_TYPE,
    RTT_DL,
    RTT_UL,
    TCP_RETRANS_DL,
    TCP_RETRANS_UL,
    THROUGHPUT_DL,
    THROUGHPUT_UL,
    USER_ID,
)


def _experience_sessions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                USER_ID: 100,
                HANDSET_TYPE: "Phone A",
                TCP_RETRANS_DL: 100,
                TCP_RETRANS_UL: 50,
                RTT_DL: 40,
                RTT_UL: 20,
                THROUGHPUT_DL: 1000,
                THROUGHPUT_UL: 800,
            },
            {
                USER_ID: 100,
                HANDSET_TYPE: "Phone A",
                TCP_RETRANS_DL: 200,
                TCP_RETRANS_UL: 100,
                RTT_DL: 60,
                RTT_UL: 40,
                THROUGHPUT_DL: 1200,
                THROUGHPUT_UL: 1000,
            },
            {
                USER_ID: 200,
                HANDSET_TYPE: "Phone B",
                TCP_RETRANS_DL: 5000,
                TCP_RETRANS_UL: 4000,
                RTT_DL: 200,
                RTT_UL: 180,
                THROUGHPUT_DL: 100,
                THROUGHPUT_UL: 80,
            },
        ]
    )


def test_aggregate_experience_per_customer():
    agg, _ = aggregate_experience(_experience_sessions(), clean=False)
    assert len(agg) == 2
    user100 = agg.loc[agg["customer_id"] == 100].iloc[0]
    assert user100["handset_type"] == "Phone A"
    assert user100["avg_tcp_retrans_bytes"] == 225.0
    assert user100["avg_rtt_ms"] == 40.0


def test_top_bottom_frequent_keys():
    agg, _ = aggregate_experience(_experience_sessions(), clean=False)
    result = top_bottom_frequent(agg, "avg_throughput_kbps", n=2)
    assert set(result.keys()) == {"top", "bottom", "most_frequent"}
    assert len(result["top"]) <= 2


def test_throughput_by_handset():
    agg, _ = aggregate_experience(_experience_sessions(), clean=False)
    summary = throughput_by_handset(agg)
    assert "mean" in summary.columns
    assert len(summary) == 2


def test_experience_kmeans_three_clusters():
    agg, _ = aggregate_experience(_experience_sessions(), clean=False)
    result = fit_experience_clusters(agg, k=2)
    assert "cluster" in result.data.columns
    stats = describe_experience_clusters(result.data)
    labels = cluster_labels_from_stats(stats)
    assert len(labels) == 2
