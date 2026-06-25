"""Handset and manufacturer analysis (Task 2 — device overview)."""

from __future__ import annotations

import pandas as pd

from tellco_user_analytics.data.columns import HANDSET_MANUFACTURER, HANDSET_TYPE


def top_handsets(df: pd.DataFrame, n: int = 10) -> pd.Series:
    """Return the top N handset types by session count."""
    return df[HANDSET_TYPE].value_counts().head(n)


def top_manufacturers(df: pd.DataFrame, n: int = 3) -> pd.Series:
    """Return the top N handset manufacturers by session count."""
    return df[HANDSET_MANUFACTURER].value_counts().head(n)


def top_handsets_by_manufacturer(
    df: pd.DataFrame,
    manufacturers: list[str] | pd.Index,
    n: int = 5,
) -> dict[str, pd.Series]:
    """
    For each manufacturer, return the top N handset models by session count.

    Returns a dict mapping manufacturer name → Series of handset counts.
    """
    result: dict[str, pd.Series] = {}
    for manufacturer in manufacturers:
        subset = df[df[HANDSET_MANUFACTURER] == manufacturer]
        result[manufacturer] = subset[HANDSET_TYPE].value_counts().head(n)
    return result


def marketing_handset_summary(
    df: pd.DataFrame,
    top_mfr_count: int = 3,
    top_model_per_mfr: int = 5,
) -> str:
    """
    Build a short narrative recommendation for the marketing team
    based on dominant handsets and manufacturers.
    """
    top_mfrs = top_manufacturers(df, top_mfr_count)
    top_models = top_handsets(df, 10)
    by_mfr = top_handsets_by_manufacturer(df, top_mfrs.index, top_model_per_mfr)

    lines = [
        "Handset & Manufacturer Insights",
        "-------------------------------",
        f"Top {top_mfr_count} manufacturers (by session volume): "
        + ", ".join(f"{name} ({count:,})" for name, count in top_mfrs.items()),
        "Top 10 handset models: "
        + ", ".join(f"{name} ({count:,})" for name, count in top_models.items()),
        "",
        "Top models within leading manufacturers:",
    ]
    for mfr, models in by_mfr.items():
        model_str = ", ".join(f"{m} ({c:,})" for m, c in models.items())
        lines.append(f"  • {mfr}: {model_str}")

    lines.extend(
        [
            "",
            "Recommendation:",
            "  Prioritize marketing campaigns and app compatibility testing for the",
            "  dominant manufacturers and mid-range Samsung/Huawei/Apple models above.",
            "  Bundle promotions with device-upgrade offers tied to the top 5 models",
            "  within each leading manufacturer to maximize reach.",
        ]
    )
    return "\n".join(lines)
