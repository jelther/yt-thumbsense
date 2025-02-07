from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from unit.conftest import today_frozen_time

from yt_thumbsense.routers.request import ProcessingStatus
from yt_thumbsense.tasks import start_single_video


@pytest.mark.asyncio
@patch("yt_thumbsense.routers.request.is_valid_youtube_video", return_value=False)
@patch("yt_thumbsense.routers.request.main_queue")
async def test_request_invalid_video_id(
    mock_queue, mock_is_valid_youtube_video, api_client, mock_database
):
    """Test requesting processing for an invalid video ID."""
    video_id = "invalid"
    response = api_client.post("/request/", json={"video_id": video_id})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid YouTube video ID."

    mock_queue.enqueue.assert_not_called()


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
@patch("yt_thumbsense.routers.request.is_valid_youtube_video", return_value=True)
@patch("yt_thumbsense.routers.request.main_queue")
async def test_request_new_video(
    mock_queue, mock_is_valid_youtube_video, api_client, mock_database, mock_video_data
):
    """Test requesting processing for a new video."""
    response = api_client.post(
        "/request/", json={"video_id": mock_video_data["video_id"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == mock_video_data["video_id"]
    assert data["status"] == ProcessingStatus.pending
    assert data["created_at"] == mock_video_data["created_at"]
    assert data["updated_at"] == mock_video_data["updated_at"]

    mock_queue.enqueue.assert_called_once_with(
        start_single_video, mock_video_data["video_id"]
    )


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
@patch("yt_thumbsense.routers.request.is_valid_youtube_video", return_value=True)
@patch("yt_thumbsense.routers.request.main_queue")
async def test_request_existing_pending_video(
    mock_queue, mock_valid_video, api_client, mock_database, mock_video_data
):
    """Test requesting an existing video that's already pending."""
    await mock_database["videos"].insert_one(mock_video_data)
    response = api_client.post(
        f"/request/", json={"video_id": mock_video_data["video_id"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == mock_video_data["video_id"]
    assert data["status"] == ProcessingStatus.pending
    assert data["created_at"] == mock_video_data["created_at"]
    assert data["updated_at"] == mock_video_data["updated_at"]

    mock_queue.enqueue.assert_not_called()


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
@patch("yt_thumbsense.routers.request.is_valid_youtube_video", return_value=True)
@patch("yt_thumbsense.routers.request.main_queue")
async def test_request_existing_processed_video_expired(
    mock_queue, mock_valid_video, api_client, mock_database, mock_video_data
):
    """Test requesting a processed video that's old enough for reprocessing."""
    mock_video_data["status"] = ProcessingStatus.processed
    # make it 1 day old
    mock_video_data["updated_at"] = (
        datetime.now() - timedelta(days=1, hours=1)
    ).isoformat()

    await mock_database["videos"].insert_one(mock_video_data)
    response = api_client.post(
        f"/request/", json={"video_id": mock_video_data["video_id"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == mock_video_data["video_id"]
    assert data["status"] == ProcessingStatus.pending
    assert data["created_at"] == mock_video_data["created_at"]
    assert data["updated_at"] == datetime.fromisoformat(today_frozen_time).isoformat()

    mock_queue.enqueue.assert_called_once_with(
        start_single_video, mock_video_data["video_id"]
    )


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
@patch("yt_thumbsense.routers.request.is_valid_youtube_video", return_value=True)
@patch("yt_thumbsense.routers.request.main_queue")
async def test_request_existing_processed_video_not_expired(
    mock_queue, mock_valid_video, api_client, mock_database, mock_video_data
):
    """Test requesting a processed video that's not old enough for reprocessing."""
    mock_video_data["status"] = ProcessingStatus.processed
    # make it 1 hour old
    mock_video_data["updated_at"] = (datetime.now() - timedelta(hours=1)).isoformat()
    await mock_database["videos"].insert_one(mock_video_data)
    response = api_client.post(
        f"/request/", json={"video_id": mock_video_data["video_id"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == mock_video_data["video_id"]
    assert data["status"] == ProcessingStatus.processed
    assert data["created_at"] == mock_video_data["created_at"]
    assert data["updated_at"] == mock_video_data["updated_at"]

    mock_queue.enqueue.assert_not_called()
