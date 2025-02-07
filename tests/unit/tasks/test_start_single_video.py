from datetime import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from unit.conftest import today_frozen_time

from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.tasks import start_single_video


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
@patch("yt_thumbsense.tasks.pull_video_comments_from_youtube")
@patch("yt_thumbsense.tasks.main_queue")
async def test_start_single_video_valid(
    mock_queue, mock_process_video, mock_database, mock_video_data
):
    await mock_database.videos.insert_one(mock_video_data)

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await start_single_video(video_id=mock_video_data["video_id"])

    mock_queue.enqueue.assert_called_once_with(
        mock_process_video, mock_video_data["video_id"]
    )

    # Check if the video status was updated
    inserted_video = await mock_database.videos.find(
        {"video_id": mock_video_data["video_id"]}
    ).next()
    assert inserted_video["status"] == ProcessingStatus.processing
    assert (
        inserted_video["updated_at"]
        == datetime.fromisoformat(today_frozen_time).isoformat()
    )


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
@patch("yt_thumbsense.tasks.pull_video_comments_from_youtube")
@patch("yt_thumbsense.tasks.main_queue")
async def test_start_single_video_not_pending(
    mock_queue, mock_process_video, mock_database, mock_video_data
):
    mock_video_data["status"] = ProcessingStatus.processing
    await mock_database.videos.insert_one(mock_video_data)
    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await start_single_video(video_id=mock_video_data["video_id"])

    mock_queue.enqueue.assert_not_called()


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
async def test_start_single_video_not_found(mock_queue, mock_database):
    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await start_single_video(video_id="non-existing-video")

    mock_queue.enqueue.assert_not_called()
