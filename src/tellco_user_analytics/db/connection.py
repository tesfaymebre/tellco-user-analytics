"""Database connection utilities."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from tellco_user_analytics.config import get_db_config


def get_engine() -> Engine:
    """Return a SQLAlchemy engine bound to the TellCo PostgreSQL database."""
    return create_engine(get_db_config().url)


def verify_connection() -> int:
    """
    Smoke-test: connect and count rows in xdr_data.
    Returns row count so we know the dump loaded correctly.
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM public.xdr_data'))
        return result.scalar_one()