from pathlib import Path

import pytest
from starlette.testclient import TestClient

TESTS_ROOT_DIR = Path(__file__).parent.parent
PROJECT_ROOT_DIR = TESTS_ROOT_DIR.parent


@pytest.fixture(scope="session")
def docker_setup():
    return ["--profile testing down -v", "--profile testing up --build -d"]


@pytest.fixture(scope="session")
def docker_cleanup():
    return ["--profile testing down -v"]


@pytest.fixture(scope="session")
def docker_compose_project_name() -> str:
    return "pytest-ytthumbnail"


@pytest.fixture(scope="session")
def docker_compose_file():
    return [
        str(PROJECT_ROOT_DIR / "docker-compose.yml"),
        str(PROJECT_ROOT_DIR / "docker-compose.testing.yml"),
    ]


@pytest.fixture(scope="session", autouse=True)
def mongodb_service_uri(docker_ip, docker_services):
    port = docker_services.port_for("db", 27017)
    mongodb_uri = (
        f"mongodb://admin:password@{docker_ip}:{port}/yt_thumbsense?authSource=admin"
    )
    return mongodb_uri


@pytest.fixture(scope="session", autouse=True)
def redis_service_uri(docker_ip, docker_services):
    port = docker_services.port_for("redis", 6379)
    redis_uri = f"redis://{docker_ip}:{port}"
    return redis_uri


@pytest.fixture
def api_client(mongodb_service_uri, redis_service_uri):
    from functools import lru_cache

    from yt_thumbsense.config import get_settings
    from yt_thumbsense.main import app

    # Clear the LRU cache before override
    get_settings.cache_clear()

    # Store original settings function
    original_get_settings = get_settings

    # Create new settings with test values
    test_settings = original_get_settings()
    test_settings.mongodb_uri = mongodb_service_uri
    test_settings.redis_url = redis_service_uri
    test_settings.app_name = "yt-thumbsense-test"
    test_settings.version = "0.1.0"

    @lru_cache
    def get_settings_override():
        return test_settings

    app.dependency_overrides[get_settings] = get_settings_override

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()
    get_settings.cache_clear()
