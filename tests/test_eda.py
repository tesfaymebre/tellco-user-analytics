"""Tests for EDA helpers."""

import pandas as pd

from tellco_user_analytics.analysis.eda import (
    application_correlation_matrix,
    duration_decile_analysis,
    run_pca,
    variable_overview,
)
from tellco_user_analytics.data.columns import APPLICATIONS


def _sample_user_df(n: int = 100) -> pd.DataFrame:
    rng = pd.Series(range(n))
    data = {
        "session_count": rng + 1,
        "total_duration_ms": rng * 1000,
        "total_data_bytes": rng * 500,
    }
    for app in APPLICATIONS:
        data[app] = rng * 10
    return pd.DataFrame(data)


def test_variable_overview_reports_dtypes():
    df = _sample_user_df(10)
    overview = variable_overview(df, columns=["session_count"])
    assert overview.loc[0, "dtype"] == "int64"
    assert overview.loc[0, "missing"] == 0


def test_duration_decile_analysis_returns_ten_groups():
    df = _sample_user_df(100)
    summary = duration_decile_analysis(df)
    assert len(summary) == 10
    assert "total_data_bytes" in summary.columns


def test_pca_runs_on_application_columns():
    df = _sample_user_df(50)
    result = run_pca(df, n_components=3)
    assert len(result.explained_variance) == 3
    assert result.loadings.shape[0] == len(APPLICATIONS)


def test_correlation_matrix_is_square():
    df = _sample_user_df(30)
    corr = application_correlation_matrix(df)
    assert corr.shape[0] == corr.shape[1] == len(APPLICATIONS)
