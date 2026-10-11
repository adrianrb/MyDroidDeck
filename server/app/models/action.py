"""ORM model: maps a deck button action key to a Windows executable to launch.

Admin-configured only: a button action (e.g. ``obs.scene.iniciar``) is never
mapped to a command unless a binding exists. Last run/status are recorded here
so the admin page shows what the deck actually triggered.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActionBinding(Base):
    __tablename__ = "action_bindings"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    executable: Mapped[str] = mapped_column(String(512))
    args: Mapped[str] = mapped_column(String(512), default="")
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)