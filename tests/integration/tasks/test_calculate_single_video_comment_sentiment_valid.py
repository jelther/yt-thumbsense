from unittest.mock import patch

import pytest

from yt_thumbsense.database import use_database
from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.tasks import calculate_single_video_comment_sentiment


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.LibreTranslateAPI", side_effect=None)
async def test_calculate_single_video_comment_sentiment_valid(
    mock_libre_translate, api_client
):

    db = await use_database()

    mock_video = {
        "video_id": "abc",
    }

    await db["videos"].insert_one(mock_video)

    mock_comment = {
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

    await db["comments"].insert_one(mock_comment)

    await calculate_single_video_comment_sentiment(
        mock_comment["video_id"], mock_comment["comment_id"]
    )

    comment = await db["comments"].find_one(
        {"video_id": mock_comment["video_id"], "comment_id": mock_comment["comment_id"]}
    )

    assert comment["status"] == ProcessingStatus.processed
    assert comment.get("vader_sentiment") is not None
