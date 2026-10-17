"""Assert that the core application tables are absent after `alembic downgrade base`.

Only run against the disposable database selected for the migration-cycle test.
"""
import sys

from sqlalchemy import create_engine, text

from app.core.config import settings
from app.db.session import normalize_database_url


def main() -> int:
    url = settings.database_url_direct or settings.database_url
    if not url:
        print("FAIL: set DATABASE_URL_DIRECT or DATABASE_URL in .env", file=sys.stderr)
        return 2

    engine = create_engine(
        normalize_database_url(url),
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
    )
    try:
        with engine.connect() as connection:
            if connection.dialect.name != "postgresql":
                raise RuntimeError("The configured migration-test database is not PostgreSQL.")
            row = connection.execute(
                text("SELECT to_regclass('public.projects'), to_regclass('public.change_requests'), "
                     "to_regclass('public.alembic_version')")
            ).one()
            if row[0] is not None or row[1] is not None:
                raise RuntimeError("Rollback failed: projects or change_requests still exists.")
            if row[2] is not None:
                count = connection.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar_one()
                if count != 0:
                    raise RuntimeError("Rollback failed: Alembic still records an applied revision.")
        print("PASS: rollback removed the Jorvera core tables and left no applied Alembic revision.")
        return 0
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
