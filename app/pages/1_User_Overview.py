"""Task 2 — user overview, handsets, and exploratory analysis."""

import streamlit as st
from components.charts import bar_chart, heatmap_chart, line_chart
from components.layout import page_shell, section_header
from services.cache import get_analytics_bundle

from tellco_user_analytics.analysis.eda import (
    app_total_correlation,
    application_correlation_matrix,
    duration_decile_analysis,
    interpret_pca,
    run_pca,
    variable_overview,
)
from tellco_user_analytics.analysis.handsets import (
    marketing_handset_summary,
    top_handsets,
    top_manufacturers,
)
from tellco_user_analytics.analysis.preprocessing import treat_missing_and_outliers
from tellco_user_analytics.analysis.user_overview import aggregate_user_sessions
from tellco_user_analytics.data.columns import APPLICATIONS

st.set_page_config(page_title="User Overview", page_icon="👥", layout="wide")
page_shell("User Overview", "Handset landscape, session behaviour, and exploratory patterns.")

bundle = get_analytics_bundle()
sessions = bundle.sessions
user_agg = aggregate_user_sessions(sessions)

section_header("Handset & manufacturer landscape")
m1, m2 = st.columns(2)
with m1:
    mfr = top_manufacturers(sessions, n=5).reset_index()
    mfr.columns = ["Manufacturer", "Sessions"]
    st.plotly_chart(
        bar_chart(mfr, "Manufacturer", "Sessions", "Top manufacturers"), width="stretch"
    )
with m2:
    handsets = top_handsets(sessions, n=10).reset_index()
    handsets.columns = ["Handset", "Sessions"]
    st.plotly_chart(bar_chart(handsets, "Handset", "Sessions", "Top handsets"), width="stretch")

with st.expander("Marketing recommendation"):
    st.markdown(marketing_handset_summary(sessions))

section_header("Exploratory data analysis")
app_cols = list(APPLICATIONS.keys()) + ["total_data_bytes"]
cleaned, report = treat_missing_and_outliers(
    user_agg,
    columns=[c for c in app_cols if c in user_agg.columns],
)
if report is not None and not report.empty:
    st.caption("Outlier treatment applied to engagement aggregates.")
    st.dataframe(report.head(10), width="stretch")

overview = variable_overview(cleaned)
st.dataframe(overview, width="stretch")

corr = app_total_correlation(cleaned)
corr_df = corr.reset_index()
corr_df.columns = ["Application", "Correlation with total traffic"]
st.plotly_chart(
    bar_chart(corr_df, "Application", "Correlation with total traffic", "App vs total data"),
    width="stretch",
)

section_header("Duration deciles & PCA")
deciles = duration_decile_analysis(user_agg)
st.plotly_chart(
    line_chart(deciles, "decile", "total_data_bytes", "Total data by duration decile"),
    width="stretch",
)

pca_result = run_pca(cleaned, columns=[c for c in APPLICATIONS if c in cleaned.columns])
ev = pca_result.explained_variance.reset_index()
ev.columns = ["component", "explained_variance_ratio"]
st.plotly_chart(
    line_chart(ev, "component", "explained_variance_ratio", "PCA explained variance"),
    width="stretch",
)
for line in interpret_pca(pca_result):
    st.markdown(f"- {line}")

corr_matrix = application_correlation_matrix(cleaned)
st.plotly_chart(heatmap_chart(corr_matrix, "Application correlation matrix"), width="stretch")
