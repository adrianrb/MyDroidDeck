"""Token generation/hashing and the device-auth FastAPI dependency."""

from __future__ import annotations

import hashlib
import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.i18n.translator import negotiate, translate
from app.models.device import Device

TOKEN_BYTES = 32


def generate_token() -> str:
    """Random URL-safe token shown to the client exactly once."""

    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Stable, dependency-free token hash (SHA-256 hex)."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def require_device(
    authorization: str | None = Header(default=None),
    accept_language: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> Device:
    """Reject the request unless it carries a valid, non-revoked device token."""

    locale = negotiate(accept_language)
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        _unauthorized(locale)
    device = session.scalar(
        select(Device).where(Device.token_hash == hash_token(token))
    )
    if device is None or device.revoked:
        _unauthorized(locale)
    return device


def _unauthorized(locale: str) -> None:
    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        translate("error.unauthorized", locale),
        headers={"WWW-Authenticate": "Bearer"},
    )