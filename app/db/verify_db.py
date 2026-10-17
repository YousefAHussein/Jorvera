"""Verify Neon/PostgreSQL, pgvector, migrations, and basic CRUD in one repeatable run.

Run from the repository root after `alembic upgrade head`:
    python -m app.db.verify_db
"""
from __future__ import annotations

import sys
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import normalize_database_url
from app.models.db_models import Project


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
            version_row = connection.execute(
                text("SELECT current_database(), current_setting('server_version')")
            ).one()
            if connection.dialect.name != "postgresql":
                raise RuntimeError("The configured database is not PostgreSQL.")
            vector_version = connection.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).scalar_one_or_none()
            if vector_version is None:
                raise RuntimeError("pgvector is not installed; run `alembic upgrade head`.")
            vector_distance = connection.execute(
                text("SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector")
            ).scalar_one()
            if vector_distance is None:
                raise RuntimeError("pgvector smoke query returned no result.")
            migration_revision = connection.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).scalar_one_or_none()
            if migration_revision is None:
                raise RuntimeError("No Alembic revision is recorded; run `alembic upgrade head`.")

        # Exercise create/read/update/delete and leave no smoke-test row behind.
        with Session(engine, expire_on_commit=False) as session:
            with session.begin():
                project = Project(
                    name=f"SO04 smoke test {uuid.uuid4()}",
                    description="Temporary record created by the SO-04 verification script.",
                )
                session.add(project)
                session.flush()
                project_id = project.id

                created = session.get(Project, project_id)
                if created is None or created.description is None:
                    raise RuntimeError("CRUD verification failed while reading a created project.")

                created.description = "Updated by the SO-04 verification script."
                session.flush()
                session.refresh(created)
                if created.description != "Updated by the SO-04 verification script.":
                    raise RuntimeError("CRUD verification failed while updating a project.")

                session.delete(created)
                session.flush()
                if session.get(Project, project_id) is not None:
                    raise RuntimeError("CRUD verification failed while deleting a project.")

        print(f"PASS: PostgreSQL database={version_row[0]}, server_version={version_row[1]}")
        print(f"PASS: pgvector extension version={vector_version}; vector type/operator query passed")
        print(f"PASS: Alembic revision={migration_revision}")
        print("PASS: project create/read/update/delete smoke test completed")
        return 0
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
