#!/usr/bin/env bash
set -euo pipefail

if [[ "${ALLOW_DESTRUCTIVE_MIGRATION_TEST:-}" != "YES" ]]; then
  echo "Refusing to run: this test drops and recreates the schema." >&2
  echo "Use a disposable Neon development branch/database, then set ALLOW_DESTRUCTIVE_MIGRATION_TEST=YES." >&2
  exit 2
fi
if [[ -z "${MIGRATION_TEST_DATABASE_URL:-}" ]]; then
  echo "Set MIGRATION_TEST_DATABASE_URL to a disposable PostgreSQL database/Neon branch URL." >&2
  exit 2
fi

# Keep destructive migration tests separate from the app's normal DATABASE_URL.
export DATABASE_URL_DIRECT="${MIGRATION_TEST_DATABASE_URL}"

echo "[1/6] Reset disposable test schema to Alembic base..."
alembic downgrade base

echo "[2/6] Apply all migrations from an empty schema..."
alembic upgrade head
python -m app.db.verify_db

echo "[3/6] Roll all application migrations back to base..."
alembic downgrade base

echo "[4/6] Verify the rollback removed the application tables..."
python -m app.db.verify_rollback

echo "[5/6] Re-apply migrations after rollback..."
alembic upgrade head

echo "[6/6] Verify database and CRUD after re-upgrade..."
python -m app.db.verify_db

echo "PASS: clean upgrade -> rollback -> re-upgrade cycle completed."
echo "Note: pgvector intentionally remains installed after downgrade; see migration comment."
