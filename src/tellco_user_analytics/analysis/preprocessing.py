"""Data cleaning — missing values and outlier treatment (Task 2.2)."""

from __future__ import annotations

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


def numeric_columns(df: pd.DataFrame, exclude: list[str] | None = None) -> list[str]:
    """Return numeric column names, optionally excluding identifiers."""
    exclude = exclude or []
    return [c for c in df.select_dtypes(include="number").columns if c not in exclude]


def detect_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """
    Return a boolean mask for outliers using the IQR rule.

    Values below Q1 - factor*IQR or above Q3 + factor*IQR are flagged.
    """
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)


def treat_missing_and_outliers(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    exclude: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Replace missing values and outliers with the column mean.

    Returns
    -------
    cleaned_df : pd.DataFrame
        Copy of the input with imputed values.
    report : pd.DataFrame
        Per-column counts of missing and outlier values replaced.
    """
    cleaned = df.copy()
    columns = columns or numeric_columns(cleaned, exclude=exclude)
    rows: list[dict[str, object]] = []

    for col in columns:
        col_mean = cleaned[col].mean()
        missing_mask = cleaned[col].isna()
        missing_count = int(missing_mask.sum())

        # Impute missing before outlier detection so IQR is stable
        cleaned.loc[missing_mask, col] = col_mean

        outlier_mask = detect_outliers_iqr(cleaned[col])
        outlier_count = int(outlier_mask.sum())
        cleaned.loc[outlier_mask, col] = col_mean

        rows.append(
            {
                "column": col,
                "missing_replaced": missing_count,
                "outliers_replaced": outlier_count,
                "replacement_value": col_mean,
            }
        )

    return cleaned, pd.DataFrame(rows)


def treat_missing_and_outliers_mixed(
    df: pd.DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Impute numeric columns with mean (+ IQR outlier replacement)
    and categorical columns with mode (Task 4.1).
    """
    cleaned, report = treat_missing_and_outliers(df, columns=numeric_cols)
    categorical_cols = categorical_cols or []

    extra_rows: list[dict[str, object]] = []
    for col in categorical_cols:
        if col not in cleaned.columns:
            continue
        mode_val = cleaned[col].mode(dropna=True)
        fill = mode_val.iloc[0] if not mode_val.empty else "unknown"
        missing_mask = cleaned[col].isna() | (cleaned[col].astype(str).str.lower() == "undefined")
        missing_count = int(missing_mask.sum())
        cleaned.loc[missing_mask, col] = fill
        extra_rows.append(
            {
                "column": col,
                "missing_replaced": missing_count,
                "outliers_replaced": 0,
                "replacement_value": fill,
            }
        )

    if extra_rows:
        report = pd.concat([report, pd.DataFrame(extra_rows)], ignore_index=True)
    return cleaned, report


class MeanImputeOutlierTransformer(BaseEstimator, TransformerMixin):
    """Sklearn-compatible transformer wrapping mean imputation + IQR outlier treatment."""

    def __init__(self, columns: list[str] | None = None, exclude: list[str] | None = None):
        self.columns = columns
        self.exclude = exclude or []
        self.report_: pd.DataFrame | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> MeanImputeOutlierTransformer:
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        cleaned, self.report_ = treat_missing_and_outliers(
            X, columns=self.columns, exclude=self.exclude
        )
        return cleaned
