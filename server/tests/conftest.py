import os
import tempfile

import pytest

# Point the app at a throwaway SQLite file *before* app modules import settings.
os.environ["MYDROIDDECK_DATABASE_URL"] = (
    f"sqlite:///{tempfile.mkdtemp(prefix='mydroiddeck-test-')}/test.db"
)

# Never launch real Windows programs from tests: record the attempt only.
os.environ["MYDROIDDECK_EXEC_ENGINE"] = "dry-run"

# Hermetic runs: a developer's .env must not change the pairing code under test.
os.environ["MYDROIDDECK_PAIRING_CODE"] = "pair-dev"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


def _fresh_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def anon_client():
    """Unauthenticated client; used to exercise the auth boundary."""
    _fresh_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def client(anon_client):
    """Authenticated client with a freshly paired device."""
    token = anon_client.post(
        "/pair", json={"code": settings.pairing_code, "device_name": "pytest"}
    ).json()["token"]
    anon_client.headers["Authorization"] = f"Bearer {token}"
    return anon_client