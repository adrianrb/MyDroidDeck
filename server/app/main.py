"""FastAPI application factory and ASGI entrypoint (``app.main:app``)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api import health, profiles
from app.db.session import Base, engine
from app.ws import deck


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="MyDroidDeck", version=__version__, lifespan=lifespan)
    application.include_router(health.router)
    application.include_router(profiles.router)
    application.include_router(deck.router)
    return application


app = create_app()
