"""Task 3 — engagement clustering and app usage."""

import streamlit as st
from components.charts import bar_chart, donut_chart, scatter_chart
from components.layout import page_shell, section_header
from services.cache import get_analytics_bundle

from tellco_user_analytics.analysis.engagement import (
    cluster_summary_stats,
    elbow_analysis,
    top_applications_by_traffic,
    top_users_per_application,
)

st.set_page_config(page_title="Engagement", page_icon="📊", layout="wide")
page_shell("User Engagement", "Session frequency, data volume, and k-means engagement segments.")

bundle = get_analytics_bundle()
eng = bundle.engagement_clusters.data

section_header("Cluster profiles")
stats = cluster_summary_stats(eng).reset_index()
st.dataframe(stats, width="stretch")

cluster_sizes = eng["cluster"].value_counts().sort_index()
st.plotly_chart(
    donut_chart(
        [f"Cluster {i}" for i in cluster_sizes.index],
        cluster_sizes.tolist(),
        "Engagement cluster sizes",
    ),
    width="stretch",
)

section_header("Feature space")
st.plotly_chart(
    scatter_chart(
        eng,
        "session_count",
        "total_traffic_bytes",
        "cluster",
        "Sessions vs traffic (coloured by cluster)",
    ),
    width="stretch",
)

section_header("Top applications & users")
apps = top_applications_by_traffic(bundle.engagement, n=7).reset_index()
apps.columns = ["Application", "Total bytes"]
st.plotly_chart(
    bar_chart(apps, "Application", "Total bytes", "Traffic by application"), width="stretch"
)

app_choice = st.selectbox("Top users by application", apps["Application"].tolist())
top_users = top_users_per_application(bundle.engagement, apps=[app_choice], n=10)[app_choice]
st.dataframe(top_users, width="stretch")

section_header("Elbow method (k selection)")
elbow = elbow_analysis(bundle.engagement)
st.plotly_chart(
    bar_chart(elbow.reset_index(), "k", "inertia", "K-means elbow curve"),
    width="stretch",
)
