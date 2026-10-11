"""Health and version endpoints (used by the app to detect compatible servers)."""

from __future__ import annotations

from fastapi import APIRouter, Header

from app import __version__
from app.i18n.translator import negotiate, translate

router = APIRouter(tags=["meta"])


@router.get("/health")
def health(accept_language: str | None = Header(default=None)) -> dict[str, str]:
    locale = negotiate(accept_language)
    return {
        "status": "ok",
        "version": __version__,
        "message": translate("health.ok", locale),
    }


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": __version__}
