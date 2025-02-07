import pytest
from freezegun import freeze_time
from unit.conftest import today_frozen_time


@pytest.mark.asyncio
async def test_fetch_existing_video(api_client, mock_database, mock_video_data):
    await mock_database.videos.insert_one(mock_video_data)
    response = api_client.get(f"/video/{mock_video_data['video_id']}")
    assert response.status_code == 200
    assert response.json() == {
        "video_id": mock_video_data["video_id"],
        "status": mock_video_data["status"],
        "created_at": mock_video_data["created_at"],
        "updated_at": mock_video_data["updated_at"],
    }


@pytest.mark.asyncio
async def test_fetch_non_existing_video(api_client, mock_database):
    response = api_client.get("/video/non-existing-video")
    assert response.status_code == 404


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_list_videos_default_pagination(
    api_client, mock_database, mock_multiple_video_data
):
    """Test default pagination (skip=0, limit=10)"""
    await mock_database.videos.insert_many(mock_multiple_video_data)
    response = api_client.get("/videos")
    assert response.status_code == 200
    expected_response = [
        {
            "video_id": mock_multiple_video_data[0]["video_id"],
            "status": mock_multiple_video_data[0]["status"],
            "created_at": mock_multiple_video_data[0]["created_at"],
            "updated_at": mock_multiple_video_data[0]["updated_at"],
        },
        {
            "video_id": mock_multiple_video_data[1]["video_id"],
            "status": mock_multiple_video_data[1]["status"],
            "created_at": mock_multiple_video_data[1]["created_at"],
            "updated_at": mock_multiple_video_data[1]["updated_at"],
        },
    ]
    assert response.json() == expected_response


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_list_videos_with_limit(
    api_client, mock_database, mock_multiple_video_data
):
    """Test pagination with custom limit"""
    await mock_database.videos.insert_many(mock_multiple_video_data)
    response = api_client.get("/videos?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    expected_response = [
        {
            "video_id": mock_multiple_video_data[0]["video_id"],
            "status": mock_multiple_video_data[0]["status"],
            "created_at": mock_multiple_video_data[0]["created_at"],
            "updated_at": mock_multiple_video_data[0]["updated_at"],
        },
    ]
    assert response.json() == expected_response


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_list_videos_with_skip(
    api_client, mock_database, mock_multiple_video_data
):
    """Test pagination with skip parameter"""
    await mock_database.videos.insert_many(mock_multiple_video_data)
    response = api_client.get("/videos?skip=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    expected_response = [
        {
            "video_id": mock_multiple_video_data[1]["video_id"],
            "status": mock_multiple_video_data[1]["status"],
            "created_at": mock_multiple_video_data[1]["created_at"],
            "updated_at": mock_multiple_video_data[1]["updated_at"],
        },
    ]
    assert response.json() == expected_response


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_list_videos_with_skip_and_limit(
    api_client, mock_database, mock_multiple_video_data
):
    """Test pagination with both skip and limit"""
    await mock_database.videos.insert_many(mock_multiple_video_data)
    response = api_client.get("/videos?skip=1&limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    expected_response = [
        {
            "video_id": mock_multiple_video_data[1]["video_id"],
            "status": mock_multiple_video_data[1]["status"],
            "created_at": mock_multiple_video_data[1]["created_at"],
            "updated_at": mock_multiple_video_data[1]["updated_at"],
        },
    ]
    assert response.json() == expected_response


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_delete_existing_video(api_client, mock_database, mock_video_data):
    await mock_database.videos.insert_one(mock_video_data)
    response = api_client.delete(f"/video/{mock_video_data['video_id']}")
    assert response.status_code == 200
    assert response.json() == {"message": "Video deleted"}


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_delete_non_existing_video(api_client, mock_database):
    response = api_client.delete("/video/non-existing-video")
    assert response.status_code == 404


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_get_video_comments_default_pagination(
    api_client, mock_database, mock_video_data
):
    """Test default pagination for comments (skip=0, limit=10)"""
    # Insert test video
    await mock_database.videos.insert_one(mock_video_data)

    # Insert test comments
    test_comments = [
        {
            "comment_id": "comment1",
            "video_id": mock_video_data["video_id"],
            "text": "First comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
        {
            "comment_id": "comment2",
            "video_id": mock_video_data["video_id"],
            "text": "Second comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
    ]
    await mock_database.comments.insert_many(test_comments)

    response = api_client.get(f"/video/{mock_video_data['video_id']}/comments")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["comment_id"] == "comment1"
    assert response.json()[1]["comment_id"] == "comment2"


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_get_video_comments_with_limit(
    api_client, mock_database, mock_video_data
):
    """Test pagination with custom limit for comments"""
    await mock_database.videos.insert_one(mock_video_data)
    test_comments = [
        {
            "comment_id": "comment1",
            "video_id": mock_video_data["video_id"],
            "text": "First comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
        {
            "comment_id": "comment2",
            "video_id": mock_video_data["video_id"],
            "text": "Second comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
    ]
    await mock_database.comments.insert_many(test_comments)

    response = api_client.get(f"/video/{mock_video_data['video_id']}/comments?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["comment_id"] == "comment1"


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_get_video_comments_with_skip(api_client, mock_database, mock_video_data):
    """Test pagination with skip parameter for comments"""
    await mock_database.videos.insert_one(mock_video_data)
    test_comments = [
        {
            "comment_id": "comment1",
            "video_id": mock_video_data["video_id"],
            "text": "First comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
        {
            "comment_id": "comment2",
            "video_id": mock_video_data["video_id"],
            "text": "Second comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
    ]
    await mock_database.comments.insert_many(test_comments)

    response = api_client.get(f"/video/{mock_video_data['video_id']}/comments?skip=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["comment_id"] == "comment2"


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
async def test_get_video_comments_with_skip_and_limit(
    api_client, mock_database, mock_video_data
):
    """Test pagination with both skip and limit for comments"""
    await mock_database.videos.insert_one(mock_video_data)
    test_comments = [
        {
            "comment_id": "comment1",
            "video_id": mock_video_data["video_id"],
            "text": "First comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
        {
            "comment_id": "comment2",
            "video_id": mock_video_data["video_id"],
            "text": "Second comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
        {
            "comment_id": "comment3",
            "video_id": mock_video_data["video_id"],
            "text": "Third comment",
            "comment_parent_id": None,
            "votes": 0,
            "replies": 0,
            "time_posted": "2024-01-01T12:00:00",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        },
    ]
    await mock_database.comments.insert_many(test_comments)

    response = api_client.get(
        f"/video/{mock_video_data['video_id']}/comments?skip=1&limit=1"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["comment_id"] == "comment2"


@pytest.mark.asyncio
async def test_get_video_comments_empty_list(
    api_client, mock_database, mock_video_data
):
    """Test getting comments for a video with no comments"""
    await mock_database.videos.insert_one(mock_video_data)
    response = api_client.get(f"/video/{mock_video_data['video_id']}/comments")
    assert response.status_code == 200
    assert response.json() == []
