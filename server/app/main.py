"""FastAPI application factory and ASGI entrypoint (``app.main:app``)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import actions, admin, health, pairing, profiles
from app.core.config import settings
from app.db.session import Base, engine, ensure_schema

logger = logging.getLogger("mydroiddeck")

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    if settings.admin_password == "admin" or settings.admin_secret_key == "change-me":
        logger.warning(
            "Admin UI is using default credentials/secret; set "
            "MYDROIDDECK_ADMIN_USER / _ADMIN_PASSWORD / _ADMIN_SECRET_KEY in .env "
            "before exposing the server."
        )
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="MyDroidDeck", version=__version__, lifespan=lifespan)
    application.mount(
        "/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static"
    )
    application.include_router(health.router)
    application.include_router(pairing.router)
    application.include_router(profiles.router)
    application.include_router(actions.router)
    application.include_router(admin.auth_router)
    application.include_router(admin.router)
    return application


app = create_app()
