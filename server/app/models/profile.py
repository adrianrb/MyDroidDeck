"""ORM models: a profile owns an ordered list of deck buttons."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    locale: Mapped[str] = mapped_column(String(10), default="pt_BR")

    buttons: Mapped[list["Button"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Button.index",
    )


class Button(Base):
    __tablename__ = "buttons"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120))

    profile: Mapped[Profile] = relationship(back_populates="buttons")
