import pytest
from starlette.testclient import TestClient


@pytest.fixture
def api_client():
    from yt_thumbsense.main import app

    client = TestClient(app)
    yield client
