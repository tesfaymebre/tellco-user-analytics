"""Pure analytics pipeline for the Streamlit dashboard (no Streamlit imports)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tellco_user_analytics.analysis.engagement import (
    ClusterResult,
    aggregate_engagement,
    cluster_summary_stats,
    fit_engagement_clusters,
    top_applications_by_traffic,
)
from tellco_user_analytics.analysis.experience import (
    ExperienceClusterResult,
    aggregate_experience,
    describe_experience_clusters,
    fit_experience_clusters,
    throughput_by_handset,
)
from tellco_user_analytics.analysis.satisfaction import (
    RegressionResult,
    build_satisfaction_table,
    cluster_satisfaction_scores,
    satisfaction_cluster_summary,
    top_satisfied_customers,
    train_satisfaction_regressor,
)
from tellco_user_analytics.data.loader import load_xdr_experience_sessions, load_xdr_sessions


@dataclass(frozen=True)
class AnalyticsBundle:
    """All computed artefacts needed across dashboard pages."""

    sessions: pd.DataFrame
    exp_sessions: pd.DataFrame
    engagement: pd.DataFrame
    engagement_clusters: ClusterResult
    experience: pd.DataFrame
    experience_clusters: ExperienceClusterResult
    satisfaction: pd.DataFrame
    satisfaction_clustered: pd.DataFrame
    regression: RegressionResult | None = None


def build_analytics_bundle(
    *,
    engagement_k: int = 3,
    experience_k: int = 3,
    satisfaction_k: int = 2,
    train_model: bool = True,
) -> AnalyticsBundle:
    """Load raw data and compute engagement, experience, and satisfaction views."""
    sessions = load_xdr_sessions()
    exp_sessions = load_xdr_experience_sessions()

    engagement = aggregate_engagement(sessions)
    engagement_clusters = fit_engagement_clusters(engagement, k=engagement_k)

    experience, _ = aggregate_experience(exp_sessions)
    experience_clusters = fit_experience_clusters(experience, k=experience_k)

    satisfaction = build_satisfaction_table(
        engagement,
        experience,
        engagement_clusters,
        experience_clusters,
    )
    satisfaction_clustered = cluster_satisfaction_scores(satisfaction, k=satisfaction_k)

    regression = None
    if train_model:
        regression = train_satisfaction_regressor(engagement, experience, satisfaction)

    return AnalyticsBundle(
        sessions=sessions,
        exp_sessions=exp_sessions,
        engagement=engagement,
        engagement_clusters=engagement_clusters,
        experience=experience,
        experience_clusters=experience_clusters,
        satisfaction=satisfaction,
        satisfaction_clustered=satisfaction_clustered,
        regression=regression,
    )


def executive_summary(bundle: AnalyticsBundle) -> dict[str, float | int | str]:
    """High-level KPIs for the home page."""
    eng_stats = cluster_summary_stats(bundle.engagement_clusters.data)
    exp_stats = describe_experience_clusters(bundle.experience_clusters.data)
    sat_stats = satisfaction_cluster_summary(bundle.satisfaction_clustered)
    top_apps = top_applications_by_traffic(bundle.engagement, n=1)

    avg_sat = float(bundle.satisfaction["satisfaction_score"].mean())
    top_app = top_apps.index[0] if len(top_apps) else "N/A"
    worst_tp = throughput_by_handset(bundle.experience)
    worst_handset = str(worst_tp.index[-1])

    return {
        "customers": int(bundle.engagement["customer_id"].nunique()),
        "sessions": int(len(bundle.sessions)),
        "avg_satisfaction": round(avg_sat, 2),
        "top_app": str(top_app),
        "worst_handset": str(worst_handset),
        "engagement_clusters": int(eng_stats.shape[0]),
        "experience_clusters": int(exp_stats.shape[0]),
        "satisfaction_clusters": int(sat_stats.shape[0]),
        "model_r2": round(bundle.regression.metrics["r2"], 3) if bundle.regression else 0.0,
    }


def purchase_recommendation(bundle: AnalyticsBundle) -> dict[str, str]:
    """Simple rule-based buy/hold/sell narrative for the insights page."""
    summary = executive_summary(bundle)
    avg_sat = float(summary["avg_satisfaction"])
    r2 = float(summary["model_r2"])

    if avg_sat >= 5000 and r2 >= 0.5:
        verdict = "BUY"
        rationale = (
            "Strong average satisfaction and a predictive regression model suggest "
            "healthy, engaged users with measurable network quality — a solid acquisition target."
        )
    elif avg_sat >= 2000:
        verdict = "HOLD"
        rationale = (
            "Moderate satisfaction with identifiable high-value segments. "
            "Invest in network QoS for low-throughput handsets before committing capital."
        )
    else:
        verdict = "SELL / PASS"
        rationale = (
            "Low satisfaction scores and weak engagement signals indicate churn risk. "
            "Due diligence should focus on infrastructure capex before purchase."
        )

    top10 = top_satisfied_customers(bundle.satisfaction, n=10)
    return {
        "verdict": verdict,
        "rationale": rationale,
        "top_customer": str(int(top10.iloc[0]["customer_id"])),
        "top_score": f"{top10.iloc[0]['satisfaction_score']:.0f}",
    }
