"""Database initialization and session management."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from ..product.paths import WorkspaceManager
from .models import Base


def _get_engine(db_path: Path):
    """Create SQLAlchemy engine for SQLite."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, echo=False, future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


class Database:
    """Database manager for CogAlpha Studio."""

    def __init__(self, workspace: WorkspaceManager | None = None) -> None:
        self.workspace = workspace or WorkspaceManager()
        self.workspace.initialize()
        self.engine = _get_engine(self.workspace.db_path)
        self._session_factory = sessionmaker(
            bind=self.engine, expire_on_commit=False, class_=Session
        )

    def create_tables(self) -> None:
        """Create all tables."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all tables (for testing)."""
        Base.metadata.drop_all(self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a database session context."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """Get a raw session (caller manages lifecycle)."""
        return self._session_factory()
