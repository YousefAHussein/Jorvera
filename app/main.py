from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_model_adapter
from app.api.routes.change_requests import router as change_requests_router
from app.api.routes.projects import router as projects_router
from app.db.session import get_db
from app.models.adapter.base import BaseProviderAdapter
from app.models.adapter.schemas import ModelRequest, ModelResponse

app = FastAPI(title="Jorvera API", version="0.1.0")
app.include_router(projects_router)
app.include_router(change_requests_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check; does not require a database connection."""
    return {"status": "ok", "service": "jorvera-api"}


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness check proving PostgreSQL, pgvector, and Alembic migrations are present."""
    try:
        if db.bind is None or db.bind.dialect.name != "postgresql":
            raise HTTPException(status_code=503, detail="A PostgreSQL database is required.")
        row = db.execute(
            text("SELECT current_database() AS database_name, current_setting('server_version') AS version")
        ).mappings().one()
        vector_version = db.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one_or_none()
        # Exercise the vector type and cosine-distance operator, not just pg_extension metadata.
        vector_distance = db.execute(
            text("SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector")
        ).scalar_one()
        migration_revision = db.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        # Avoid returning connection details or credentials in health output.
        raise HTTPException(
            status_code=503,
            detail="Database readiness check failed. Apply migrations and verify pgvector is enabled.",
        ) from exc

    if vector_version is None or migration_revision is None:
        raise HTTPException(
            status_code=503,
            detail="Database is reachable, but pgvector or migrations are missing.",
        )
    return {
        "status": "ok",
        "database": str(row["database_name"]),
        "postgresql_version": str(row["version"]),
        "pgvector_version": str(vector_version),
        "pgvector_smoke": "ok" if vector_distance is not None else "failed",
        "alembic_revision": str(migration_revision),
    }


@app.post("/generate", response_model=ModelResponse)
async def generate_text(
    request: ModelRequest,
    adapter: BaseProviderAdapter = Depends(get_current_model_adapter),
):
    return await adapter.generate(request)
