"""Plotly chart builders shared across dashboard pages."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CHART_TEMPLATE = "plotly_dark"
ACCENT = "#6C63FF"
ACCENT_2 = "#00D4AA"
ACCENT_3 = "#FF6B6B"


def _base_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text=title, x=0.02, font=dict(size=16)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=24, t=56, b=24),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str = ACCENT) -> go.Figure:
    fig = px.bar(df, x=x, y=y, color_discrete_sequence=[color])
    return _base_layout(fig, title)


def scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None,
    title: str,
) -> go.Figure:
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=[ACCENT, ACCENT_2, ACCENT_3],
        opacity=0.75,
    )
    return _base_layout(fig, title)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    fig = px.line(df, x=x, y=y, markers=True, color_discrete_sequence=[ACCENT_2])
    return _base_layout(fig, title)


def donut_chart(labels: list[str], values: list[float], title: str) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=[ACCENT, ACCENT_2, ACCENT_3, "#FFD166", "#118AB2"]),
            )
        ]
    )
    return _base_layout(fig, title)


def heatmap_chart(matrix: pd.DataFrame, title: str) -> go.Figure:
    fig = px.imshow(
        matrix,
        color_continuous_scale="Viridis",
        aspect="auto",
    )
    return _base_layout(fig, title)
