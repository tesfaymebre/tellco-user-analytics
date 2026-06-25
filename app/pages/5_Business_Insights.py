"""Acquisition recommendation — synthesises Tasks 2–5."""

import streamlit as st
from components.charts import bar_chart
from components.layout import page_shell, section_header, verdict_badge
from services.cache import get_analytics_bundle
from services.pipeline import purchase_recommendation

from tellco_user_analytics.analysis.handsets import marketing_handset_summary

st.set_page_config(page_title="Business Insights", page_icon="💡", layout="wide")
page_shell(
    "Business Insights",
    "Executive summary and TellCo acquisition recommendation for investors.",
)

bundle = get_analytics_bundle()
rec = purchase_recommendation(bundle)

section_header("Acquisition verdict")
verdict_badge(rec["verdict"])
st.markdown(rec["rationale"])

col1, col2, col3 = st.columns(3)
col1.metric("Top satisfied customer", rec["top_customer"])
col2.metric("Their score", rec["top_score"])
col3.metric("Model R²", f"{bundle.regression.metrics['r2']:.3f}" if bundle.regression else "N/A")

section_header("Satisfaction distribution")
hist = bundle.satisfaction["satisfaction_score"].describe().reset_index()
hist.columns = ["Statistic", "Value"]
st.plotly_chart(
    bar_chart(hist, "Statistic", "Value", "Satisfaction score summary"),
    width="stretch",
)

section_header("Marketing handset strategy")
st.markdown(marketing_handset_summary(bundle.sessions))

section_header("Key takeaways")
st.markdown(
    """
    1. **Engagement** — High-traffic apps (Gaming, YouTube) drive data revenue; cluster analysis
       reveals a small highly-engaged segment worth premium plans.
    2. **Experience** — Handset-level throughput gaps highlight where network investment yields
       the highest QoS improvement.
    3. **Satisfaction** — Combined scores identify retention risk and upsell candidates; regression
       links measurable network KPIs to satisfaction for proactive monitoring.
    4. **Feature store** — PostgreSQL + MySQL layers persist curated features for this dashboard
       and future model retraining pipelines.
    """
)
