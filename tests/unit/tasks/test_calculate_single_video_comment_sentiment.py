from unittest.mock import patch

import pytest

from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.tasks import calculate_single_video_comment_sentiment


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.LibreTranslateAPI")
async def test_calculate_single_video_comment_sentiment_valid(
    mock_libre_translation, mock_database, mock_comment, mock_video_data
):
    await mock_database["videos"].insert_one(mock_video_data)
    await mock_database["comments"].insert_one(mock_comment)

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await calculate_single_video_comment_sentiment(
            mock_comment["video_id"], mock_comment["comment_id"]
        )

    comment = await mock_database["comments"].find_one(
        {"video_id": mock_comment["video_id"], "comment_id": mock_comment["comment_id"]}
    )

    assert comment["status"] == ProcessingStatus.processed
    assert comment.get("vader_sentiment") is not None

    mock_libre_translation.assert_called_once()

    inserted_comment = await mock_database["comments"].find_one(
        {"video_id": mock_comment["video_id"], "comment_id": mock_comment["comment_id"]}
    )

    assert inserted_comment["status"] == ProcessingStatus.processed


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.LibreTranslateAPI")
async def test_calculate_single_video_comment_sentiment_not_found(
    mock_libre_translation, mock_database, mock_comment
):
    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await calculate_single_video_comment_sentiment(
            mock_comment["video_id"], mock_comment["comment_id"]
        )

    mock_libre_translation.assert_not_called()


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.LibreTranslateAPI")
async def test_calculate_single_video_comment_sentiment_not_pending(
    mock_libre_translation, mock_database, mock_comment
):
    mock_comment["status"] = ProcessingStatus.processed
    await mock_database["comments"].insert_one(mock_comment)

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await calculate_single_video_comment_sentiment(
            mock_comment["video_id"], mock_comment["comment_id"]
        )

    mock_libre_translation.assert_not_called()


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.LibreTranslateAPI")
async def test_calculate_single_video_comment_sentiment_not_english(
    mock_libre_translation, mock_database, mock_comment, mock_video_data
):
    await mock_database["videos"].insert_one(mock_video_data)
    await mock_database["comments"].insert_one(mock_comment)

    mock_libre_translation.return_value.detect.return_value = [
        {
            "language": "es",
        }
    ]

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await calculate_single_video_comment_sentiment(
            mock_comment["video_id"], mock_comment["comment_id"]
        )

    assert mock_libre_translation.return_value.translate.call_count == 1


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.LibreTranslateAPI")
async def test_calculate_single_video_comment_sentiment_is_english(
    mock_libre_translation, mock_database, mock_comment
):
    await mock_database["comments"].insert_one(mock_comment)

    mock_libre_translation.return_value.detect.return_value = [
        {
            "language": "en",
        }
    ]

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await calculate_single_video_comment_sentiment(
            mock_comment["video_id"], mock_comment["comment_id"]
        )

    assert mock_libre_translation.return_value.translate.call_count == 0


@pytest.mark.asyncio
@patch("yt_thumbsense.tasks.LibreTranslateAPI")
async def test_calculate_single_video_comment_sentiment_failed(
    mock_libre_translation, mock_database, mock_comment, mock_video_data
):
    await mock_database["videos"].insert_one(mock_video_data)
    await mock_database["comments"].insert_one(mock_comment)

    mock_libre_translation.side_effect = Exception

    with patch("yt_thumbsense.tasks.use_database", return_value=mock_database):
        await calculate_single_video_comment_sentiment(
            mock_comment["video_id"], mock_comment["comment_id"]
        )

    comment = await mock_database["comments"].find_one(
        {"video_id": mock_comment["video_id"], "comment_id": mock_comment["comment_id"]}
    )

    assert comment["status"] == ProcessingStatus.failed
