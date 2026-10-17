from collections.abc import Generator
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when database access is requested before DATABASE_URL is set."""


def normalize_database_url(url: str) -> str:
    """Use Psycopg 3 with SQLAlchemy when given a standard PostgreSQL URL."""
    clean_url = url.strip()
    if clean_url.startswith("postgres://"):
        return "postgresql+psycopg://" + clean_url[len("postgres://"):]
    if clean_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + clean_url[len("postgresql://"):]
    return clean_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create the application engine lazily so non-database routes can load without .env."""
    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "Database is not configured. Set DATABASE_URL in your local .env file."
        )

    return create_engine(
        normalize_database_url(settings.database_url),
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.database_echo,
        connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
    )


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields one SQLAlchemy session per request."""
    try:
        engine = get_engine()
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    with Session(engine, expire_on_commit=False) as session:
        yield session
