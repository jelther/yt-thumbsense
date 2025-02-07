from datetime import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from unit.conftest import today_frozen_time

from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.tasks import start_pending_videos


@pytest.mark.asyncio
@freeze_time(today_frozen_time)
@patch("yt_thumbsense.tasks.pull_video_comments_from_youtube")
@patch("yt_thumbsense.tasks.main_queue")
async def test_start_pending_videos_valid(
    mock_queue, mock_pull_video_comments_from_youtube, mock_database, mock_video_data
):
    await mock_database.videos.insert_one(mock_video_data)

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await start_pending_videos()

    mock_queue.enqueue.assert_called_once_with(
        mock_pull_video_comments_from_youtube, mock_video_data["video_id"]
    )

    inserted_video = await mock_database.videos.find(
        {"video_id": mock_video_data["video_id"]}
    ).next()
    assert inserted_video["status"] == ProcessingStatus.processing
    assert (
        inserted_video["updated_at"]
        == datetime.fromisoformat(today_frozen_time).isoformat()
    )


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
async def test_start_pending_videos_no_pending_videos(mock_queue, mock_database):
    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await start_pending_videos()

    mock_queue.enqueue.assert_not_called()
