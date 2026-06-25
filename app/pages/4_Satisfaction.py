"""Task 5 — satisfaction scores, regression, and feature store."""

import streamlit as st
from components.charts import bar_chart, scatter_chart
from components.layout import page_shell, section_header
from services.cache import get_analytics_bundle

from tellco_user_analytics.analysis.satisfaction import (
    satisfaction_cluster_summary,
    top_satisfied_customers,
)
from tellco_user_analytics.db.feature_store import (
    init_feature_store,
    sync_engagement_features,
    sync_experience_features,
    sync_satisfaction_features,
)
from tellco_user_analytics.db.mysql_export import export_satisfaction_scores, verify_mysql_export

st.set_page_config(page_title="Satisfaction", page_icon="⭐", layout="wide")
page_shell("User Satisfaction", "Combined engagement + experience scores, regression, and exports.")

bundle = get_analytics_bundle()
sat = bundle.satisfaction_clustered

section_header("Score distribution")
st.plotly_chart(
    scatter_chart(
        sat,
        "engagement_score",
        "experience_score",
        "satisfaction_cluster",
        "Engagement vs experience scores",
    ),
    width="stretch",
)

top10 = top_satisfied_customers(sat, n=10)
st.dataframe(top10, width="stretch")

cluster_avg = satisfaction_cluster_summary(sat).reset_index()
st.plotly_chart(
    bar_chart(
        cluster_avg, "satisfaction_cluster", "satisfaction_score", "Mean satisfaction by cluster"
    ),
    width="stretch",
)

if bundle.regression:
    section_header("Regression model")
    m1, m2 = st.columns(2)
    m1.metric("R²", f"{bundle.regression.metrics['r2']:.4f}")
    m2.metric("RMSE", f"{bundle.regression.metrics['rmse']:.4f}")
    st.caption(f"Model artifact: `{bundle.regression.artifact_path}`")

section_header("Feature store & MySQL export")
if st.button("Sync PostgreSQL feature store + MySQL export"):
    with st.spinner("Writing features…"):
        init_feature_store()
        n_eng = sync_engagement_features(
            bundle.engagement,
            bundle.engagement_clusters.data["cluster"],
        )
        n_exp = sync_experience_features(
            bundle.experience,
            bundle.experience_clusters.data["cluster"],
        )
        n_sat = sync_satisfaction_features(sat)
        n_mysql = export_satisfaction_scores(sat)
    st.success(
        f"Synced {n_eng} engagement, {n_exp} experience, {n_sat} satisfaction rows "
        f"to PostgreSQL · {n_mysql} rows to MySQL."
    )

with st.expander("MySQL sample (feature store export)"):
    try:
        st.dataframe(verify_mysql_export(limit=10), width="stretch")
    except Exception as exc:
        st.warning(f"MySQL not available: {exc}")
