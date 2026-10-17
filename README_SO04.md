# SO-04: PostgreSQL, Alembic migrations, and pgvector

This is an additive database foundation for the existing Jorvera FastAPI/model-adapter application. The existing `/generate` route and model-adapter files are retained.

## Included

- Neon/PostgreSQL SQLAlchemy engine and request-scoped database sessions.
- Versioned Alembic migrations for `projects`, `change_requests`, and the `vector` extension.
- Basic project and change-request CRUD REST endpoints.
- `/health/db` readiness endpoint for PostgreSQL, pgvector, and Alembic revision verification.
- `python -m app.db.verify_db` connection, extension, migration, and CRUD smoke test.
- `scripts/test_migration_cycle.sh` for a disposable database branch only.
- SQLite-backed API tests that do not require Neon credentials.

## 1. Set up Neon safely

1. Create/select a development branch in Neon. Do not run migration rollback tests against a database containing important/shared data.
2. In Neon, copy the standard PostgreSQL connection string. Use `sslmode=require`.
3. Copy `.env.example` to `.env` and set:
   - `DATABASE_URL`: application's Neon URL (a pooled endpoint is fine for normal application requests).
   - `DATABASE_URL_DIRECT`: direct, non-pooler Neon URL, recommended for Alembic migrations and verification.
4. Keep `.env` out of Git. `.gitignore` excludes it; commit `.env.example` only.

Do not share real Neon connection strings in chat, screenshots, tickets, or GitHub.

## 2. Install dependencies

From the repository root, using Python 3.11+:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 3. Initialize or upgrade the database

Run from the project root:

```bash
alembic upgrade head
alembic current
python -m app.db.verify_db
```

`alembic upgrade head` is the clean initialization path and is also the repeatable upgrade path. Alembic records its current revision in `alembic_version`.

Expected verification output includes:

- `PASS: PostgreSQL database=...`
- `PASS: pgvector extension version=...; vector type/operator query passed`
- `PASS: Alembic revision=0002_enable_pgvector`
- `PASS: project create/read/update/delete smoke test completed`

## 4. Start the API and try CRUD

```bash
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Routes:

| Operation | Endpoint |
|---|---|
| Create/list projects | `POST /api/v1/projects`, `GET /api/v1/projects` |
| Read/update/delete project | `GET /api/v1/projects/{id}`, `PATCH /api/v1/projects/{id}`, `DELETE /api/v1/projects/{id}` |
| Create/list change requests | `POST /api/v1/change-requests`, `GET /api/v1/change-requests` |
| Read/update/delete change request | `GET /api/v1/change-requests/{id}`, `PATCH /api/v1/change-requests/{id}`, `DELETE /api/v1/change-requests/{id}` |
| Liveness | `GET /health` |
| DB readiness | `GET /health/db` |

Create a project first, copy its returned UUID, and use that UUID as `project_id` when creating a change request. Project names must be unique. Deleting a project cascades to its change requests.

## 5. Run tests

```bash
pytest -q
```

The API CRUD tests use an in-memory SQLite database so they do not need Neon credentials. Actual PostgreSQL and pgvector availability are tested by `python -m app.db.verify_db` against your configured Neon database.

## 6. Prove clean upgrade, rollback, and recovery

**This script is destructive.** Create a separate, disposable Neon development branch/database and copy its direct connection URL. Never point this test at a shared team database or production database.

PowerShell example:

```powershell
$env:MIGRATION_TEST_DATABASE_URL = "postgresql://...direct-neon-url...?sslmode=require"
$env:ALLOW_DESTRUCTIVE_MIGRATION_TEST = "YES"
bash scripts/test_migration_cycle.sh
```

On Windows, run this script inside Git Bash or WSL. On macOS/Linux:

```bash
export MIGRATION_TEST_DATABASE_URL='postgresql://...direct-neon-url...?sslmode=require'
export ALLOW_DESTRUCTIVE_MIGRATION_TEST=YES
bash scripts/test_migration_cycle.sh
```

The script intentionally runs `alembic downgrade base` on the disposable database, migrates up from base, rolls back, and migrates up again. The pgvector extension is intentionally retained during rollback to avoid removing a database-level extension that other objects may depend on.

## Schema scope and architecture note

This implements database infrastructure and the minimal project/change-request resources needed to demonstrate CRUD. It does **not** claim to implement the full Jorvera domain schema: immutable evidence, frozen baseline snapshots, dependency edges, requirements, gap/risk records, decisions, packages, exports, and audit events should be added in their own reviewed migrations as those sprint tasks are implemented. Embedding vector dimensions should be agreed with the team when the embedding model is selected; this sprint verifies pgvector availability without hard-coding an unapproved dimension.

## Neon caveats

- Migrations should run against a direct Neon connection, not a pooled endpoint, whenever possible.
- Keep `sslmode=require` in the Neon URL.
- A missing `DATABASE_URL` does not prevent the existing mock `/generate` route from importing; database endpoints return HTTP 503 until configured.
- This API has no authentication/authorization yet. Keep it development-only and do not expose it publicly with a live database until access controls are implemented.
