"""Cached data accessors for Streamlit pages."""

from __future__ import annotations

import streamlit as st
from services.pipeline import AnalyticsBundle, build_analytics_bundle, executive_summary


@st.cache_data(show_spinner="Loading telecom analytics…", ttl=3600)
def get_analytics_bundle() -> AnalyticsBundle:
    """Build or retrieve the full analytics pipeline (cached 1 h)."""
    return build_analytics_bundle()


@st.cache_data(show_spinner=False, ttl=3600)
def get_executive_summary() -> dict[str, float | int | str]:
    """Cached KPI dictionary for the home page."""
    return executive_summary(get_analytics_bundle())
