import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import db_models  # noqa: F401 - register SQLAlchemy models


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_project_crud(client):
    created = client.post("/api/v1/projects", json={"name": "Jorvera Test", "description": "before"})
    assert created.status_code == 201, created.text
    project = created.json()
    project_id = project["id"]
    assert project["description"] == "before"

    listed = client.get("/api/v1/projects")
    assert listed.status_code == 200
    assert any(row["id"] == project_id for row in listed.json())

    fetched = client.get(f"/api/v1/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Jorvera Test"

    updated = client.patch(f"/api/v1/projects/{project_id}", json={"description": "after"})
    assert updated.status_code == 200
    assert updated.json()["description"] == "after"

    deleted = client.delete(f"/api/v1/projects/{project_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404


def test_change_request_crud_and_project_cascade(client):
    project_response = client.post("/api/v1/projects", json={"name": "Jorvera CRUD Project"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    created = client.post(
        "/api/v1/change-requests",
        json={"project_id": project_id, "title": "Automate eligible refunds", "description": "draft"},
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    assert created.json()["status"] == "draft"

    assert client.get(f"/api/v1/change-requests/{request_id}").status_code == 200
    updated = client.patch(
        f"/api/v1/change-requests/{request_id}",
        json={"title": "Clarify refund approval", "status": "in_review"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Clarify refund approval"
    assert updated.json()["status"] == "in_review"

    filtered = client.get("/api/v1/change-requests", params={"project_id": project_id})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    assert client.delete(f"/api/v1/change-requests/{request_id}").status_code == 204
    assert client.get(f"/api/v1/change-requests/{request_id}").status_code == 404

    # A project can also be deleted, and any remaining change requests are database-cascaded.
    second = client.post(
        "/api/v1/change-requests",
        json={"project_id": project_id, "title": "Delete with project"},
    )
    assert second.status_code == 201
    second_id = second.json()["id"]
    assert client.delete(f"/api/v1/projects/{project_id}").status_code == 204
    assert client.get(f"/api/v1/change-requests/{second_id}").status_code == 404


def test_project_validation_and_duplicate_name(client):
    assert client.post("/api/v1/projects", json={"name": "   "}).status_code == 422
    assert client.post("/api/v1/projects", json={"name": "Unique project"}).status_code == 201
    duplicate = client.post("/api/v1/projects", json={"name": "Unique project"})
    assert duplicate.status_code == 409

