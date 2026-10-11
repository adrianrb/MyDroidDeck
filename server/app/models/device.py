"""ORM model: a paired device and the hash of its API token.

Only the SHA-256 hash of a token is stored, so a database leak does not reveal
usable tokens. The plaintext token is returned to the client once, at pairing.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
