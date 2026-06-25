"""User engagement metrics and clustering (Task 3)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer

from tellco_user_analytics.data.columns import (
    APPLICATIONS,
    BEARER_ID,
    DURATION_MS,
    TOTAL_DL,
    TOTAL_UL,
    USER_ID,
)

# Canonical engagement feature names (per-user, non-normalized)
ENGAGEMENT_FEATURES = ["session_count", "total_duration_ms", "total_traffic_bytes"]


def aggregate_engagement(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate engagement metrics per customer (MSISDN).

    Metrics
    -------
    session_count : number of xDR sessions (frequency)
    total_duration_ms : sum of session durations
    total_traffic_bytes : sum of download + upload bytes
    Plus per-application total bytes for app-level engagement.
    """
    work = df.copy()
    work["total_traffic_bytes"] = work[TOTAL_DL].fillna(0) + work[TOTAL_UL].fillna(0)

    for app_name, (dl_col, ul_col) in APPLICATIONS.items():
        work[app_name] = work[dl_col].fillna(0) + work[ul_col].fillna(0)

    agg_spec: dict[str, str] = {
        BEARER_ID: "count",
        DURATION_MS: "sum",
        "total_traffic_bytes": "sum",
    }
    for app_name in APPLICATIONS:
        agg_spec[app_name] = "sum"

    aggregated = work.groupby(USER_ID, as_index=False).agg(agg_spec)
    return aggregated.rename(
        columns={
            BEARER_ID: "session_count",
            DURATION_MS: "total_duration_ms",
            USER_ID: "customer_id",
        }
    )


def top_customers_per_metric(
    df: pd.DataFrame,
    metrics: list[str] | None = None,
    n: int = 10,
) -> dict[str, pd.DataFrame]:
    """Return top N customers for each engagement metric."""
    metrics = metrics or ENGAGEMENT_FEATURES
    result: dict[str, pd.DataFrame] = {}
    for metric in metrics:
        cols = ["customer_id", metric]
        result[metric] = df[cols].nlargest(n, metric).reset_index(drop=True)
    return result


def normalize_engagement(df: pd.DataFrame, features: list[str] | None = None) -> np.ndarray:
    """L2-normalize engagement features (required before k-means per challenge)."""
    features = features or ENGAGEMENT_FEATURES
    normalizer = Normalizer()
    return normalizer.fit_transform(df[features])


class EngagementNormalizer(BaseEstimator, TransformerMixin):
    """Sklearn transformer wrapping L2 normalization of engagement features."""

    def __init__(self, features: list[str] | None = None):
        self.features = features or ENGAGEMENT_FEATURES
        self.normalizer_ = Normalizer()

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> EngagementNormalizer:
        self.normalizer_.fit(X[self.features])
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        return self.normalizer_.transform(X[self.features])


@dataclass
class ClusterResult:
    """K-means output with labels on the original (non-normalized) dataframe."""

    labels: np.ndarray
    model: KMeans
    data: pd.DataFrame
    pipeline: Pipeline


def less_engaged_cluster_id(clustered_df: pd.DataFrame) -> int:
    """Return the cluster id with the lowest combined engagement (Task 5.1)."""
    means = clustered_df.groupby("cluster")[ENGAGEMENT_FEATURES].mean().sum(axis=1)
    return int(means.idxmin())


def fit_engagement_clusters(
    df: pd.DataFrame,
    k: int = 3,
    features: list[str] | None = None,
    random_state: int = 42,
) -> ClusterResult:
    """
    Normalize engagement metrics and run k-means clustering.

    Clustering is performed on normalized features; summaries use raw metrics.
    """
    features = features or ENGAGEMENT_FEATURES
    pipeline = Pipeline(
        steps=[
            ("normalize", EngagementNormalizer(features=features)),
            ("kmeans", KMeans(n_clusters=k, random_state=random_state, n_init=10)),
        ]
    )
    pipeline.fit(df)
    labels = pipeline.named_steps["kmeans"].labels_

    result_df = df.copy()
    result_df["cluster"] = labels
    return ClusterResult(
        labels=labels,
        model=pipeline.named_steps["kmeans"],
        data=result_df,
        pipeline=pipeline,
    )


def cluster_summary_stats(
    clustered_df: pd.DataFrame,
    metrics: list[str] | None = None,
) -> pd.DataFrame:
    """
    Min, max, mean, and total of non-normalized metrics per cluster.
    """
    metrics = metrics or ENGAGEMENT_FEATURES
    summary = clustered_df.groupby("cluster")[metrics].agg(["min", "max", "mean", "sum"]).round(2)
    return summary


def top_users_per_application(
    df: pd.DataFrame,
    apps: list[str] | None = None,
    n: int = 10,
) -> dict[str, pd.DataFrame]:
    """Top N most engaged customers per application by total app bytes."""
    apps = apps or [a for a in APPLICATIONS if a in df.columns]
    result: dict[str, pd.DataFrame] = {}
    for app in apps:
        result[app] = df[["customer_id", app]].nlargest(n, app).reset_index(drop=True)
    return result


def top_applications_by_traffic(df: pd.DataFrame, n: int = 3) -> pd.Series:
    """Return the top N applications by aggregate user traffic."""
    apps = [a for a in APPLICATIONS if a in df.columns]
    totals = df[apps].sum().sort_values(ascending=False)
    return totals.head(n)


def elbow_analysis(
    df: pd.DataFrame,
    k_range: range | None = None,
    features: list[str] | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Compute within-cluster sum of squares (inertia) for elbow-method k selection.
    """
    features = features or ENGAGEMENT_FEATURES
    k_range = k_range or range(1, 11)

    scaled = normalize_engagement(df, features)
    rows: list[dict[str, float | int]] = []

    for k in k_range:
        if k == 1:
            # Single cluster: inertia relative to centroid
            centroid = scaled.mean(axis=0)
            wcss = float(((scaled - centroid) ** 2).sum())
            rows.append({"k": k, "inertia": wcss})
        else:
            model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
            model.fit(scaled)
            rows.append({"k": k, "inertia": float(model.inertia_)})

    return pd.DataFrame(rows)


def suggest_elbow_k(elbow_df: pd.DataFrame) -> int:
    """
    Suggest optimal k using the maximum second derivative (elbow) of inertia.
    """
    if len(elbow_df) < 3:
        return int(elbow_df.loc[elbow_df["inertia"].idxmin(), "k"])

    inertia = elbow_df["inertia"].values
    # First difference (drop in inertia) then second difference (change in drop)
    first_diff = np.diff(inertia)
    second_diff = np.diff(first_diff)
    # Elbow = k where deceleration is largest (after k>=2)
    elbow_idx = int(np.argmax(second_diff)) + 2  # offset for diff indices
    return int(elbow_df.iloc[elbow_idx]["k"])
