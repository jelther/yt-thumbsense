import pytest

from yt_thumbsense.config import get_settings


@pytest.mark.asyncio
async def test_settings_override(api_client, mongodb_service_uri, redis_service_uri):
    settings = get_settings()
    assert settings.mongodb_uri == mongodb_service_uri
    assert settings.redis_url == redis_service_uri
