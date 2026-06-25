"""Tests for preprocessing utilities."""

import pandas as pd

from tellco_user_analytics.analysis.preprocessing import (
    detect_outliers_iqr,
    treat_missing_and_outliers,
)


def test_treat_missing_replaces_with_mean():
    df = pd.DataFrame({"a": [1.0, None, 3.0, 4.0]})
    cleaned, report = treat_missing_and_outliers(df, columns=["a"])
    assert cleaned["a"].isna().sum() == 0
    assert report.loc[0, "missing_replaced"] == 1


def test_detect_outliers_iqr_flags_extreme_value():
    # Tight cluster + one extreme outlier
    series = pd.Series([10, 11, 10, 12, 11, 10_000])
    assert detect_outliers_iqr(series).iloc[-1]
