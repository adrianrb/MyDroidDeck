import os
import tempfile

import pytest

# Point the app at a throwaway SQLite file *before* app modules import settings.
os.environ["MYDROIDDECK_DATABASE_URL"] = (
    f"sqlite:///{tempfile.mkdtemp(prefix='mydroiddeck-test-')}/test.db"
)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
