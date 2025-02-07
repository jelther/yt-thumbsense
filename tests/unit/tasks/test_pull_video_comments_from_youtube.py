from unittest.mock import patch

import dateparser
import pytest
from freezegun import freeze_time
from unit.conftest import today_frozen_time

from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.tasks import (
    calculate_single_video_comment_sentiment,
    pull_video_comments_from_youtube,
)


@pytest.fixture()
def mock_youtube_comment_single():
    return {
        "cid": "123",
        "text": "comment 1",
        "votes": 1,
        "replies": 0,
        "reply": False,
        "time": "1 hour ago",
    }


@pytest.fixture()
def mock_youtube_comment_with_parent():
    return {
        "cid": "parent_id.comment_id",
        "text": "comment 1",
        "votes": 1,
        "replies": 0,
        "reply": True,
        "time": "1 hour ago",
    }


@pytest.fixture()
def mock_youtube_comment_with_edition():
    return {
        "cid": "comment_id",
        "text": "comment 1",
        "votes": 1,
        "replies": 0,
        "reply": False,
        "time": "1 hour ago (edited)",
    }


@pytest.fixture()
def mock_youtube_comment_with_edition_wrong():
    return {
        "cid": "comment_id",
        "text": "comment 1",
        "votes": 1,
        "replies": 0,
        "reply": False,
        "time": "xx hour ago (edited)",
    }


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
@patch("yt_thumbsense.tasks.YoutubeCommentDownloader")
@freeze_time(today_frozen_time)
async def test_pull_video_comments_from_youtube_valid(
    mock_youtube_downloader,
    mock_queue,
    mock_database,
    mock_video_data,
    mock_youtube_comment_single,
):
    mock_youtube_downloader.return_value.get_comments.return_value = [
        mock_youtube_comment_single
    ]

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await mock_database["videos"].insert_one(mock_video_data)

        await pull_video_comments_from_youtube(mock_video_data["video_id"])

        inserted_comment = await mock_database["comments"].find_one(
            {
                "video_id": mock_video_data["video_id"],
                "comment_id": mock_youtube_comment_single["cid"],
            }
        )

        assert inserted_comment["video_id"] == mock_video_data["video_id"]
        assert inserted_comment["comment_id"] == mock_youtube_comment_single["cid"]
        assert inserted_comment["comment_parent_id"] is None

        assert inserted_comment["text"] == mock_youtube_comment_single["text"]
        assert inserted_comment["votes"] == mock_youtube_comment_single["votes"]
        assert inserted_comment["replies"] == mock_youtube_comment_single["replies"]
        assert (
            inserted_comment["time_posted_raw"] == mock_youtube_comment_single["time"]
        )
        assert (
            inserted_comment["time_posted"]
            == dateparser.parse(mock_youtube_comment_single["time"]).isoformat()
        )

        assert inserted_comment["status"] == ProcessingStatus.pending

        mock_queue.enqueue.assert_called_once_with(
            calculate_single_video_comment_sentiment,
            mock_video_data["video_id"],
            inserted_comment["comment_id"],
        )


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
@patch("yt_thumbsense.tasks.YoutubeCommentDownloader")
@freeze_time(today_frozen_time)
async def test_pull_video_comments_from_youtube_valid_with_parent_comment(
    mock_youtube_downloader,
    mock_queue,
    mock_database,
    mock_video_data,
    mock_youtube_comment_with_parent,
):
    mock_youtube_downloader.return_value.get_comments.return_value = [
        mock_youtube_comment_with_parent
    ]

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await mock_database["videos"].insert_one(mock_video_data)

        await pull_video_comments_from_youtube(mock_video_data["video_id"])

        comment_parent_id, comment_id = mock_youtube_comment_with_parent["cid"].split(
            ".", 1
        )

        inserted_comment = await mock_database["comments"].find_one(
            {
                "video_id": mock_video_data["video_id"],
                "comment_id": comment_id,
            }
        )

        assert inserted_comment["video_id"] == mock_video_data["video_id"]
        assert inserted_comment["comment_id"] == comment_id
        assert inserted_comment["comment_parent_id"] == comment_parent_id

        assert inserted_comment["text"] == mock_youtube_comment_with_parent["text"]
        assert inserted_comment["votes"] == mock_youtube_comment_with_parent["votes"]
        assert (
            inserted_comment["replies"] == mock_youtube_comment_with_parent["replies"]
        )
        assert (
            inserted_comment["time_posted_raw"]
            == mock_youtube_comment_with_parent["time"]
        )
        assert (
            inserted_comment["time_posted"]
            == dateparser.parse(mock_youtube_comment_with_parent["time"]).isoformat()
        )

        assert inserted_comment["status"] == ProcessingStatus.pending

        mock_queue.enqueue.assert_called_once_with(
            calculate_single_video_comment_sentiment,
            mock_video_data["video_id"],
            inserted_comment["comment_id"],
        )


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
@patch("yt_thumbsense.tasks.YoutubeCommentDownloader")
@freeze_time(today_frozen_time)
async def test_pull_video_comments_from_youtube_valid_with_edited_comment(
    mock_youtube_downloader,
    mock_queue,
    mock_database,
    mock_video_data,
    mock_youtube_comment_with_edition,
):
    mock_youtube_downloader.return_value.get_comments.return_value = [
        mock_youtube_comment_with_edition
    ]

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await mock_database["videos"].insert_one(mock_video_data)

        await pull_video_comments_from_youtube(mock_video_data["video_id"])

        inserted_comment = await mock_database["comments"].find_one(
            {
                "video_id": mock_video_data["video_id"],
                "comment_id": mock_youtube_comment_with_edition["cid"],
            }
        )

        assert inserted_comment["video_id"] == mock_video_data["video_id"]
        assert (
            inserted_comment["comment_id"] == mock_youtube_comment_with_edition["cid"]
        )
        assert inserted_comment["comment_parent_id"] is None

        assert inserted_comment["text"] == mock_youtube_comment_with_edition["text"]
        assert inserted_comment["votes"] == mock_youtube_comment_with_edition["votes"]
        assert (
            inserted_comment["replies"] == mock_youtube_comment_with_edition["replies"]
        )
        assert (
            inserted_comment["time_posted_raw"]
            == mock_youtube_comment_with_edition["time"]
        )
        assert (
            inserted_comment["time_posted"]
            == dateparser.parse(
                mock_youtube_comment_with_edition["time"].replace("(edited)", "")
            ).isoformat()
        )

        assert inserted_comment["status"] == ProcessingStatus.pending


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
@patch("yt_thumbsense.tasks.YoutubeCommentDownloader")
@freeze_time(today_frozen_time)
async def test_pull_video_comments_from_youtube_invalid_with_edited_comment(
    mock_youtube_downloader,
    mock_queue,
    mock_database,
    mock_video_data,
    mock_youtube_comment_with_edition_wrong,
):
    mock_youtube_downloader.return_value.get_comments.return_value = [
        mock_youtube_comment_with_edition_wrong
    ]

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await mock_database["videos"].insert_one(mock_video_data)

        await pull_video_comments_from_youtube(mock_video_data["video_id"])

        inserted_comment = await mock_database["comments"].find_one(
            {
                "video_id": mock_video_data["video_id"],
                "comment_id": mock_youtube_comment_with_edition_wrong["cid"],
            }
        )

        assert inserted_comment["video_id"] == mock_video_data["video_id"]
        assert (
            inserted_comment["comment_id"]
            == mock_youtube_comment_with_edition_wrong["cid"]
        )
        assert inserted_comment["comment_parent_id"] is None

        assert (
            inserted_comment["text"] == mock_youtube_comment_with_edition_wrong["text"]
        )
        assert (
            inserted_comment["votes"]
            == mock_youtube_comment_with_edition_wrong["votes"]
        )
        assert (
            inserted_comment["replies"]
            == mock_youtube_comment_with_edition_wrong["replies"]
        )
        assert (
            inserted_comment["time_posted_raw"]
            == mock_youtube_comment_with_edition_wrong["time"]
        )
        assert inserted_comment["time_posted"] is None

        assert inserted_comment["status"] == ProcessingStatus.pending


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
@patch("yt_thumbsense.tasks.YoutubeCommentDownloader")
@freeze_time(today_frozen_time)
async def test_pull_video_comments_from_youtube_not_in_database(
    mock_youtube_downloader,
    mock_queue,
    mock_database,
):
    mock_youtube_downloader.return_value.get_comments.return_value = []

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await pull_video_comments_from_youtube("invalid-video-id")
        mock_queue.enqueue.assert_not_called()


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
@patch("yt_thumbsense.tasks.YoutubeCommentDownloader")
@freeze_time(today_frozen_time)
async def test_pull_video_comments_from_youtube_failed(
    mock_youtube_downloader, mock_queue, mock_database, mock_video_data
):
    mock_youtube_downloader.return_value.get_comments.side_effect = Exception

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await mock_database["videos"].insert_one(mock_video_data)

        await pull_video_comments_from_youtube(mock_video_data["video_id"])

        mock_queue.enqueue.assert_not_called()

        inserted_video = await mock_database["videos"].find_one(
            {
                "video_id": mock_video_data["video_id"],
            }
        )

        assert inserted_video["status"] == ProcessingStatus.failed


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.main_queue")
@patch("yt_thumbsense.tasks.YoutubeCommentDownloader")
@freeze_time(today_frozen_time)
async def test_max_comments_reached(
    mock_youtube_downloader,
    mock_queue,
    mock_database,
    mock_video_data,
    mock_youtube_comment_single,
):
    mock_youtube_downloader.return_value.get_comments.return_value = [
        mock_youtube_comment_single,
        mock_youtube_comment_single,
    ]

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        with patch("yt_thumbsense.tasks.get_settings") as mock_get_settings:
            mock_get_settings.return_value.max_comments_per_video = 1
            await mock_database["videos"].insert_one(mock_video_data)
            await pull_video_comments_from_youtube(mock_video_data["video_id"])

            inserted_video = await mock_database["videos"].find_one(
                {
                    "video_id": mock_video_data["video_id"],
                }
            )

            assert inserted_video["status"] == ProcessingStatus.processed

            inserted_video_comments = (
                await mock_database["comments"]
                .find(
                    {
                        "video_id": mock_video_data["video_id"],
                    }
                )
                .to_list(length=None)
            )

            assert len(inserted_video_comments) == 1
