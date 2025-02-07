import pytest


@pytest.mark.asyncio
async def test_root_path(api_client):
    response = api_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"app_name": "yt-thumbsense-test", "version": "0.1.0"}


@pytest.mark.asyncio
async def test_health_check(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
