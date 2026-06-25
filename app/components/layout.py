"""Reusable layout helpers, CSS injection, and branded chrome."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_STATIC = Path(__file__).resolve().parents[1] / "static"


def inject_theme() -> None:
    """Load custom CSS and lightweight JS enhancements."""
    css = (_STATIC / "styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    js = (_STATIC / "theme.js").read_text(encoding="utf-8")
    components.html(f"<script>{js}</script>", height=0)


def page_shell(title: str, subtitle: str = "") -> None:
    """Standard page header with gradient hero."""
    inject_theme()
    sub = f"<p class='hero-sub'>{subtitle}</p>" if subtitle else ""
    st.html(
        f"<div class='hero-banner fade-in'>"
        f"<p class='hero-kicker'>TellCo Analytics</p>"
        f"<h1 class='hero-title'>{title}</h1>"
        f"{sub}"
        f"</div>"
    )


def metric_card(label: str, value: str, delta: str = "", icon: str = "📊") -> None:
    """Glass-style KPI card."""
    delta_html = f"<span class='metric-delta'>{delta}</span>" if delta else ""
    st.html(
        f"<div class='metric-card fade-in'>"
        f"<div class='metric-icon'>{icon}</div>"
        f"<div class='metric-body'>"
        f"<p class='metric-label'>{label}</p>"
        f"<p class='metric-value'>{value}</p>"
        f"{delta_html}"
        f"</div></div>"
    )


def section_header(text: str) -> None:
    st.html(f"<h3 class='section-header'>{text}</h3>")


def verdict_badge(verdict: str) -> None:
    css_class = {
        "BUY": "badge-buy",
        "HOLD": "badge-hold",
        "SELL / PASS": "badge-sell",
    }.get(verdict, "badge-hold")
    st.html(f"<div class='verdict-badge {css_class}'>{verdict}</div>")
