"""Database migration support."""

from __future__ import annotations

import logging

from sqlalchemy import inspect

from .models import Base

logger = logging.getLogger(__name__)


def run_migrations(engine) -> None:
    """Run database migrations. Creates tables if they don't exist."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = set(Base.metadata.tables.keys())

    missing = required_tables - existing_tables
    if missing:
        logger.info("Creating missing tables: %s", missing)
        Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in missing])
    else:
        logger.debug("All required tables already exist")


def get_schema_version(engine) -> int:
    """Get current schema version."""
    inspector = inspect(engine)
    if "app_settings" not in inspector.get_table_names():
        return 0
    # Check for schema_version setting
    with engine.connect() as conn:
        from sqlalchemy import text

        result = conn.execute(
            text("SELECT value FROM app_settings WHERE key = 'schema_version'")
        ).fetchone()
        if result:
            return int(result[0])
    return 1


def set_schema_version(engine, version: int) -> None:
    """Set schema version."""
    with engine.connect() as conn:
        from sqlalchemy import text

        conn.execute(
            text(
                "INSERT OR REPLACE INTO app_settings (key, value, updated_at) "
                "VALUES ('schema_version', :version, datetime('now'))"
            ),
            {"version": str(version)},
        )
        conn.commit()
