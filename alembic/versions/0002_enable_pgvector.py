"""Enable pgvector on the configured PostgreSQL database.

Revision ID: 0002_enable_pgvector
Revises: 0001_core_tables
Create Date: 2026-10-16
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_enable_pgvector"
down_revision: Union[str, None] = "0001_core_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Neon supports pgvector. Keep IF NOT EXISTS so the migration is safe when the
    # extension was enabled manually before Alembic was introduced.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Intentionally leave the extension installed. Extensions are database-level shared
    # resources and may be used by other objects; rolling back this migration should not
    # unexpectedly remove an extension from a shared Neon database.
    pass
