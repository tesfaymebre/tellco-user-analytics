"""User experience (network QoS) analysis — Task 4."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from tellco_user_analytics.analysis.preprocessing import treat_missing_and_outliers_mixed
from tellco_user_analytics.data.columns import (
    AVG_RTT_MS,
    AVG_TCP_RETRANS,
    AVG_THROUGHPUT_KBPS,
    EXPERIENCE_FEATURES,
    HANDSET_TYPE,
    RTT_DL,
    RTT_UL,
    TCP_RETRANS_DL,
    TCP_RETRANS_UL,
    THROUGHPUT_DL,
    THROUGHPUT_UL,
    USER_ID,
)

SESSION_EXPERIENCE_DERIVED = [
    "_tcp_retrans",
    "_rtt_ms",
    "_throughput_kbps",
]


def _prepare_session_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Derive per-session combined network metrics from DL/UL columns."""
    work = df.copy()
    work["_tcp_retrans"] = work[TCP_RETRANS_DL].fillna(0) + work[TCP_RETRANS_UL].fillna(0)
    work["_rtt_ms"] = (work[RTT_DL].fillna(0) + work[RTT_UL].fillna(0)) / 2
    work["_throughput_kbps"] = (work[THROUGHPUT_DL].fillna(0) + work[THROUGHPUT_UL].fillna(0)) / 2
    return work


def aggregate_experience(
    df: pd.DataFrame,
    clean: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """
    Aggregate experience metrics per customer (Task 4.1).

    Returns per-user averages for TCP retransmission, RTT, throughput,
    and the modal handset type. Optionally cleans missing/outliers first.
    """
    work = _prepare_session_metrics(df)
    report: pd.DataFrame | None = None

    if clean:
        numeric_session_cols = SESSION_EXPERIENCE_DERIVED + [
            RTT_DL,
            RTT_UL,
            THROUGHPUT_DL,
            THROUGHPUT_UL,
            TCP_RETRANS_DL,
            TCP_RETRANS_UL,
        ]
        work, report = treat_missing_and_outliers_mixed(
            work,
            numeric_cols=[c for c in numeric_session_cols if c in work.columns],
            categorical_cols=[HANDSET_TYPE],
        )

    aggregated = (
        work.groupby(USER_ID, as_index=False)
        .agg(
            avg_tcp_retrans_bytes=("_tcp_retrans", "mean"),
            avg_rtt_ms=("_rtt_ms", "mean"),
            avg_throughput_kbps=("_throughput_kbps", "mean"),
            handset_type=(
                HANDSET_TYPE,
                lambda s: s.mode().iloc[0] if not s.mode().empty else "unknown",
            ),
        )
        .rename(columns={USER_ID: "customer_id"})
    )

    if clean:
        user_numeric = list(EXPERIENCE_FEATURES)
        aggregated, user_report = treat_missing_and_outliers_mixed(
            aggregated,
            numeric_cols=user_numeric,
            categorical_cols=["handset_type"],
        )
        if report is not None and user_report is not None:
            report = pd.concat([report, user_report], ignore_index=True)

    return aggregated, report


def top_bottom_frequent(
    df: pd.DataFrame,
    column: str,
    n: int = 10,
) -> dict[str, pd.DataFrame | pd.Series]:
    """
    Top N, bottom N, and N most frequent values for a metric (Task 4.2).
    """
    series = df[column].dropna()
    top = df.nlargest(n, column)[["customer_id", column]].reset_index(drop=True)
    bottom = df.nsmallest(n, column)[["customer_id", column]].reset_index(drop=True)
    # Round for meaningful frequency counts on continuous metrics
    rounded = series.round(2)
    frequent = rounded.value_counts().head(n)
    return {"top": top, "bottom": bottom, "most_frequent": frequent}


def throughput_by_handset(df: pd.DataFrame) -> pd.DataFrame:
    """Mean throughput per handset type (Task 4.3)."""
    return (
        df.groupby("handset_type")[AVG_THROUGHPUT_KBPS]
        .agg(["mean", "median", "count"])
        .sort_values("mean", ascending=False)
        .round(2)
    )


def tcp_retrans_by_handset(df: pd.DataFrame) -> pd.DataFrame:
    """Mean TCP retransmission per handset type (Task 4.3)."""
    return (
        df.groupby("handset_type")[AVG_TCP_RETRANS]
        .agg(["mean", "median", "count"])
        .sort_values("mean", ascending=False)
        .round(2)
    )


@dataclass
class ExperienceClusterResult:
    labels: np.ndarray
    model: KMeans
    data: pd.DataFrame
    pipeline: Pipeline


def worst_experience_cluster_id(clustered_df: pd.DataFrame) -> int:
    """Return the cluster id with the poorest network experience (Task 5.1)."""
    stats = describe_experience_clusters(clustered_df)
    labels = cluster_labels_from_stats(stats)
    for cluster_id, description in labels.items():
        if description.startswith("Poor experience"):
            return int(cluster_id)
    means = stats.xs("mean", axis=1, level=1)
    score = (
        means[AVG_THROUGHPUT_KBPS].rank()
        - means[AVG_RTT_MS].rank(ascending=False)
        - means[AVG_TCP_RETRANS].rank(ascending=False)
    )
    return int(score.idxmin())


def fit_experience_clusters(
    df: pd.DataFrame,
    k: int = 3,
    features: list[str] | None = None,
    random_state: int = 42,
) -> ExperienceClusterResult:
    """K-means (k=3) on scaled experience metrics (Task 4.4)."""
    features = features or EXPERIENCE_FEATURES
    pipeline = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("kmeans", KMeans(n_clusters=k, random_state=random_state, n_init=10)),
        ]
    )
    pipeline.fit(df[features])
    labels = pipeline.named_steps["kmeans"].labels_

    result_df = df.copy()
    result_df["cluster"] = labels
    return ExperienceClusterResult(
        labels=labels,
        model=pipeline.named_steps["kmeans"],
        data=result_df,
        pipeline=pipeline,
    )


def describe_experience_clusters(clustered_df: pd.DataFrame) -> pd.DataFrame:
    """Summary stats per cluster on raw (non-scaled) experience metrics."""
    return (
        clustered_df.groupby("cluster")[EXPERIENCE_FEATURES]
        .agg(["mean", "median", "min", "max", "count"])
        .round(2)
    )


def cluster_labels_from_stats(stats: pd.DataFrame) -> dict[int, str]:
    """
    Heuristic cluster descriptions based on mean RTT, throughput, and TCP.

    Lower throughput + higher RTT/TCP → worse experience.
    """
    descriptions: dict[int, str] = {}
    means = stats.xs("mean", axis=1, level=1)

    throughput_rank = means[AVG_THROUGHPUT_KBPS].rank()
    rtt_rank = means[AVG_RTT_MS].rank(ascending=False)
    tcp_rank = means[AVG_TCP_RETRANS].rank(ascending=False)
    score = throughput_rank - rtt_rank - tcp_rank

    ranked = score.sort_values(ascending=False).index.tolist()
    if ranked:
        descriptions[int(ranked[0])] = (
            "Good experience — higher throughput, lower RTT and TCP retransmission"
        )
    if len(ranked) >= 2:
        descriptions[int(ranked[-1])] = (
            "Poor experience — lower throughput, higher latency and packet retransmission"
        )
    for cluster_id in ranked[1:-1]:
        descriptions[int(cluster_id)] = (
            "Moderate experience — mid-range network performance across metrics"
        )
    return descriptions
