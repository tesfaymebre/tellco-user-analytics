"""Sanity check that the package imports and config is constructible."""

from tellco_user_analytics.config import DatabaseConfig


def test_database_config_url():
    cfg = DatabaseConfig(
        host="localhost",
        port=5432,
        name="tellco",
        user="postgres",
        password="secret",
    )
    assert "postgresql+psycopg2://" in cfg.url
    assert "tellco" in cfg.url