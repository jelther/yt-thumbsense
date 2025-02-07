import pytest


@pytest.mark.asyncio
async def test_root_path(api_client):
    response = api_client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_not_rate_limited(api_client):
    for i in range(1, 60):
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
