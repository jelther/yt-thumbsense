from datetime import datetime

import pytest
import pytest_asyncio
from freezegun import freeze_time
from mongomock_motor import AsyncMongoMockClient

from yt_thumbsense import database
from yt_thumbsense.main import app
from yt_thumbsense.models.request import ProcessingStatus


@pytest_asyncio.fixture
async def mongo_client():
    client = AsyncMongoMockClient()
    yield client
    client.close()


@pytest_asyncio.fixture
async def mock_database(mongo_client):
    db = mongo_client["test_db"]
    app.dependency_overrides[database.use_database] = lambda: db
    yield db
    await db.drop_collection("videos")
    await db.drop_collection("comments")


today_frozen_time: str = "2024-01-01 12:00:00"


@pytest.fixture()
@freeze_time(today_frozen_time)
def mock_video_data():
    return {
        "video_id": "abc",
        "status": ProcessingStatus.pending,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture()
@freeze_time(today_frozen_time)
def mock_multiple_video_data():
    return [
        {
            "video_id": "abc",
            "status": ProcessingStatus.pending,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        {
            "video_id": "def",
            "status": ProcessingStatus.pending,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
    ]


@pytest.fixture()
def mock_comment():
    return {
        "video_id": "abc",
        "comment_id": "123",
        "comment_parent_id": None,
        "text": "comment 1",
        "votes": 1,
        "replies": 0,
        "time_posted_raw": "1 hour ago",
        "time_posted": "2021-01-01T00:00:00",
        "status": ProcessingStatus.pending,
        "created_at": "2021-01-01T00:00:00",
        "updated_at": "2021-01-01T00:00:00",
    }
