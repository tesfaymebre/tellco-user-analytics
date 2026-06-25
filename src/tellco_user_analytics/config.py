"""Central configuration — keeps secrets out of source code."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable DB settings loaded once from the environment."""

    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def url(self) -> str:
        """SQLAlchemy connection URL for PostgreSQL."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        )


@dataclass(frozen=True)
class MySQLConfig:
    """MySQL settings for satisfaction score export (Task 5.6)."""

    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def url(self) -> str:
        """SQLAlchemy connection URL for MySQL."""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


def get_db_config() -> DatabaseConfig:
    """Build config from environment variables (see .env.example)."""
    return DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        name=os.getenv("DB_NAME", "tellco"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def get_mysql_config() -> MySQLConfig:
    """Build MySQL config from environment variables (see .env.example)."""
    return MySQLConfig(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        name=os.getenv("MYSQL_DB", "tellco_analytics"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "tellco_dev"),
    )
