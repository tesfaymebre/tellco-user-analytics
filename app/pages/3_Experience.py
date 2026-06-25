"""Task 4 — network experience and QoS clustering."""

import streamlit as st
from components.charts import bar_chart, scatter_chart
from components.layout import page_shell, section_header
from services.cache import get_analytics_bundle

from tellco_user_analytics.analysis.experience import (
    cluster_labels_from_stats,
    describe_experience_clusters,
    tcp_retrans_by_handset,
    throughput_by_handset,
    top_bottom_frequent,
)

st.set_page_config(page_title="Experience", page_icon="📡", layout="wide")
page_shell("User Experience", "TCP retransmission, RTT, throughput, and QoS clusters.")

bundle = get_analytics_bundle()
exp = bundle.experience_clusters.data

section_header("Cluster summary")
stats = describe_experience_clusters(bundle.experience_clusters.data)
labels = cluster_labels_from_stats(stats)
st.dataframe(stats, width="stretch")
st.caption("Labels: " + " · ".join(f"Cluster {k}: {v}" for k, v in labels.items()))

section_header("QoS feature space")
st.plotly_chart(
    scatter_chart(
        exp,
        "avg_rtt_ms",
        "avg_throughput_kbps",
        "cluster",
        "RTT vs throughput by cluster",
    ),
    width="stretch",
)

section_header("Handset performance")
tp = throughput_by_handset(bundle.experience).head(15).reset_index()
tp = tp.rename(columns={"handset_type": "Handset", "mean": "Avg throughput (kbps)"})
st.plotly_chart(
    bar_chart(tp, "Handset", "Avg throughput (kbps)", "Throughput by handset"),
    width="stretch",
)

tcp = tcp_retrans_by_handset(bundle.experience).head(15).reset_index()
tcp = tcp.rename(columns={"handset_type": "Handset", "mean": "Avg TCP retrans (bytes)"})
st.plotly_chart(
    bar_chart(tcp, "Handset", "Avg TCP retrans (bytes)", "TCP retrans by handset", color="#FF6B6B"),
    width="stretch",
)

section_header("Extreme users")
extremes = top_bottom_frequent(bundle.experience, "avg_throughput_kbps", n=10)
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Highest throughput**")
    st.dataframe(extremes["top"], width="stretch")
with col2:
    st.markdown("**Lowest throughput**")
    st.dataframe(extremes["bottom"], width="stretch")
