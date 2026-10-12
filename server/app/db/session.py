"""Database engine, session factory, and FastAPI dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """Idempotently bring the (SQLite) schema up to date with the models.

    ``Base.metadata.create_all`` creates missing *tables* but never alters existing
    ones, so columns added after a database was first created (e.g. ``icon`` and
    ``sort_order`` on ``action_bindings``) are added here with a plain ALTER.
    Fresh databases are created complete by ``create_all`` and this becomes a no-op.
    """
    if not settings.database_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(action_bindings)"))
        }
        if "icon" not in columns:
            connection.execute(
                text("ALTER TABLE action_bindings ADD COLUMN icon VARCHAR(512)")
            )
        if "sort_order" not in columns:
            connection.execute(
                text("ALTER TABLE action_bindings ADD COLUMN sort_order INTEGER DEFAULT 0")
            )
