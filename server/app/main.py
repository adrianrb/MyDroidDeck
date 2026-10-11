"""FastAPI application factory and ASGI entrypoint (``app.main:app``)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import actions, admin, health, pairing, profiles
from app.db.session import Base, engine

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
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
    application.include_router(admin.router)
    return application


app = create_app()
