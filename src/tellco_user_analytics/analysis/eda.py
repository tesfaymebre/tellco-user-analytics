"""Exploratory data analysis helpers (Task 2.2)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from tellco_user_analytics.data.columns import APPLICATIONS

# Columns produced by aggregate_user_sessions()
USER_METRIC_COLUMNS = [
    "session_count",
    "total_duration_ms",
    "total_dl_bytes",
    "total_ul_bytes",
    "total_data_bytes",
]

APP_COLUMNS = list(APPLICATIONS.keys())
ANALYSIS_COLUMNS = USER_METRIC_COLUMNS + APP_COLUMNS


def variable_overview(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Summarise variable names, dtypes, non-null counts, and missing %. """
    columns = columns or list(df.columns)
    rows = []
    for col in columns:
        if col not in df.columns:
            continue
        missing = int(df[col].isna().sum())
        rows.append(
            {
                "variable": col,
                "dtype": str(df[col].dtype),
                "non_null": int(df[col].notna().sum()),
                "missing": missing,
                "missing_pct": round(100 * missing / len(df), 2),
            }
        )
    return pd.DataFrame(rows)


def basic_metrics(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Compute mean, median, std, min, max for quantitative variables."""
    columns = columns or [c for c in ANALYSIS_COLUMNS if c in df.columns]
    return df[columns].agg(["mean", "median", "std", "min", "max"]).T.round(2)


def dispersion_parameters(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """
    Non-graphical univariate analysis: range, variance, std, IQR, coefficient of variation.
    """
    columns = columns or [c for c in ANALYSIS_COLUMNS if c in df.columns]
    rows = []
    for col in columns:
        s = df[col].dropna()
        mean = s.mean()
        rows.append(
            {
                "variable": col,
                "range": s.max() - s.min(),
                "variance": s.var(),
                "std": s.std(),
                "iqr": s.quantile(0.75) - s.quantile(0.25),
                "cv": (s.std() / mean) if mean else np.nan,
            }
        )
    return pd.DataFrame(rows).round(4)


def duration_decile_analysis(
    df: pd.DataFrame,
    duration_col: str = "total_duration_ms",
    data_col: str = "total_data_bytes",
    n_deciles: int = 10,
) -> pd.DataFrame:
    """
    Segment users into decile classes by total session duration.

    Returns total data volume (DL+UL) per decile class.
    """
    work = df[[duration_col, data_col]].copy()
    work["decile"] = pd.qcut(
        work[duration_col],
        q=n_deciles,
        labels=[f"D{i}" for i in range(1, n_deciles + 1)],
        duplicates="drop",
    )
    summary = (
        work.groupby("decile", observed=True)
        .agg(
            users=(duration_col, "count"),
            avg_duration_ms=(duration_col, "mean"),
            total_data_bytes=(data_col, "sum"),
            avg_data_bytes=(data_col, "mean"),
        )
        .reset_index()
    )
    return summary.round(2)


def top_decile_classes(
    decile_summary: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    """Return the top N decile classes (D6–D10 when n_deciles=10)."""
    return decile_summary.tail(top_n)


def app_total_correlation(
    df: pd.DataFrame,
    total_col: str = "total_data_bytes",
) -> pd.Series:
    """Pearson correlation between each application and total data volume."""
    correlations = {}
    for app in APP_COLUMNS:
        if app in df.columns:
            correlations[app] = df[app].corr(df[total_col])
    return pd.Series(correlations, name="corr_with_total_data").sort_values(ascending=False)


def application_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix across application byte columns."""
    cols = [c for c in APP_COLUMNS if c in df.columns]
    return df[cols].corr().round(3)


@dataclass
class PCAResult:
    """Container for PCA outputs."""

    components: pd.DataFrame
    explained_variance: pd.Series
    loadings: pd.DataFrame
    transformed: pd.DataFrame


def run_pca(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    n_components: int | None = None,
) -> PCAResult:
    """
    Standardise application columns and run PCA.

    Parameters
    ----------
    df : pd.DataFrame
        User-level aggregated data (after cleaning).
    columns : list[str], optional
        Feature columns; defaults to application byte volumes.
    n_components : int, optional
        Number of components; defaults to all features.
    """
    columns = columns or [c for c in APP_COLUMNS if c in df.columns]
    n_components = n_components or len(columns)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[columns])

    pca = PCA(n_components=n_components)
    transformed = pca.fit_transform(scaled)

    explained = pd.Series(
        pca.explained_variance_ratio_,
        index=[f"PC{i}" for i in range(1, n_components + 1)],
        name="explained_variance_ratio",
    )
    loadings = pd.DataFrame(
        pca.components_.T,
        index=columns,
        columns=[f"PC{i}" for i in range(1, n_components + 1)],
    )
    components_df = pd.DataFrame(
        transformed,
        columns=[f"PC{i}" for i in range(1, n_components + 1)],
    )

    return PCAResult(
        components=components_df,
        explained_variance=explained,
        loadings=loadings.round(3),
        transformed=components_df,
    )


def interpret_pca(pca_result: PCAResult, top_features: int = 3) -> list[str]:
    """
    Generate up to four bullet-point interpretations from PCA loadings.

    Identifies dominant features per principal component.
    """
    bullets: list[str] = []
    ev = pca_result.explained_variance

    bullets.append(
        f"PC1 explains {ev.iloc[0]:.1%} of variance — driven mainly by "
        f"{', '.join(_top_loading_features(pca_result.loadings, 'PC1', top_features))}."
    )

    if len(ev) > 1:
        bullets.append(
            f"PC2 explains {ev.iloc[1]:.1%} — highlights "
            f"{', '.join(_top_loading_features(pca_result.loadings, 'PC2', top_features))}."
        )

    cumulative = ev.cumsum()
    bullets.append(
        f"First {min(3, len(ev))} components capture {cumulative.iloc[min(2, len(ev) - 1)]:.1%} "
        "of total application-traffic variation."
    )

    # Contrast PC1 loadings: streaming vs communication apps
    pc1 = pca_result.loadings["PC1"].abs().sort_values(ascending=False)
    bullets.append(
        f"Largest absolute loadings on PC1: {pc1.index[0]} ({pc1.iloc[0]:.2f}), "
        f"suggesting usage splits between high-volume and niche applications."
    )

    return bullets[:4]


def _top_loading_features(loadings: pd.DataFrame, pc: str, n: int) -> list[str]:
    ranked = loadings[pc].abs().sort_values(ascending=False)
    return ranked.head(n).index.tolist()
