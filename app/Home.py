"""TellCo User Analytics — executive dashboard home page."""

import streamlit as st
from components.layout import metric_card, page_shell
from services.cache import get_analytics_bundle, get_executive_summary

st.set_page_config(
    page_title="TellCo Analytics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

page_shell(
    "Telecom User Analytics",
    "Growth insights, network experience, and satisfaction scoring for TellCo acquisition due diligence.",
)

try:
    summary = get_executive_summary()
    bundle = get_analytics_bundle()
except Exception as exc:
    st.error(
        "Could not connect to the database. Run `make setup` or start Docker with `make db-up` "
        "and load data via `make db-load`."
    )
    st.code(str(exc))
    st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Unique Customers", f"{summary['customers']:,}", icon="👥")
with col2:
    metric_card("xDR Sessions", f"{summary['sessions']:,}", icon="📶")
with col3:
    metric_card("Avg Satisfaction", f"{summary['avg_satisfaction']:,.0f}", icon="⭐")
with col4:
    metric_card("Model R²", f"{summary['model_r2']:.3f}", icon="🎯")

st.markdown("---")

left, right = st.columns([1, 1])
with left:
    st.markdown("### Navigation")
    st.markdown(
        """
        Use the sidebar to explore each analysis task:

        | Page | Focus |
        |------|-------|
        | **User Overview** | Handsets, EDA, PCA |
        | **Engagement** | App usage & k-means clusters |
        | **Experience** | Network QoS & handset throughput |
        | **Satisfaction** | Scores, regression, feature store |
        | **Business Insights** | Buy / hold / sell recommendation |
        """
    )

with right:
    st.markdown("### Quick facts")
    st.info(f"**Top application:** {summary['top_app']}")
    st.warning(f"**Lowest-throughput handset:** {summary['worst_handset']}")
    st.success(
        f"**Clusters:** {summary['engagement_clusters']} engagement · "
        f"{summary['experience_clusters']} experience · "
        f"{summary['satisfaction_clusters']} satisfaction"
    )

with st.expander("Refresh cached analytics"):
    if st.button("Clear cache & reload"):
        st.cache_data.clear()
        st.rerun()
