from unittest.mock import patch

import pandas as pd
import pytest

from yt_thumbsense.models.request import ProcessingStatus


@pytest.fixture
def mock_processed_comments():
    return [
        {
            "video_id": "abc123",
            "comment_id": "1",
            "status": ProcessingStatus.processed,
            "vader_sentiment": {"compound": 0.5, "pos": 0.6, "neu": 0.4, "neg": 0.0},
        },
        {
            "video_id": "abc123",
            "comment_id": "2",
            "status": ProcessingStatus.processed,
            "vader_sentiment": {"compound": -0.2, "pos": 0.2, "neu": 0.5, "neg": 0.3},
        },
    ]


@pytest.mark.asyncio
@patch("yt_thumbsense.routers.score.is_valid_youtube_video", return_value=True)
async def test_get_score_valid(
    mock_is_valid_youtube_video, api_client, mock_database, mock_processed_comments
):
    # Arrange
    await mock_database.comments.insert_many(mock_processed_comments)

    # Act
    response = api_client.get("/score/video/abc123")

    # Assert
    assert response.status_code == 200

    assert response.json()["video_id"] == "abc123"
    assert response.json()["comment_count"] == 2

    expected_score = pd.DataFrame(
        [comment["vader_sentiment"] for comment in mock_processed_comments]
    )

    assert response.json()["sentiment_score"] == expected_score["compound"].mean()
    assert response.json()["sentiment_score_std"] == expected_score["compound"].std()
    assert response.json()["sentiment_score_min"] == expected_score["compound"].min()
    assert response.json()["sentiment_score_max"] == expected_score["compound"].max()


@pytest.mark.asyncio
@patch("yt_thumbsense.routers.score.is_valid_youtube_video", return_value=False)
async def test_get_score_invalid_video_id(
    mock_is_valid_youtube_video, api_client, mock_database
):
    response = api_client.get("/score/video/invalid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid YouTube video ID"


@pytest.mark.asyncio
@patch("yt_thumbsense.routers.score.is_valid_youtube_video", return_value=True)
async def test_get_score_no_comments(
    mock_is_valid_youtube_video, api_client, mock_database
):
    response = api_client.get("/score/video/video123")
    assert response.status_code == 404
    assert response.json()["detail"] == "Comments not found"


@pytest.mark.asyncio
@patch("yt_thumbsense.routers.score.is_valid_youtube_video", return_value=True)
async def test_get_score_unprocessed_comments(
    mock_is_valid_youtube_video, api_client, mock_database, mock_processed_comments
):
    mock_processed_comments[0]["vader_sentiment"] = None

    await mock_database.comments.insert_many(mock_processed_comments)

    response = api_client.get("/score/video/abc123")
    assert response.status_code == 500
    assert response.json()["detail"] == "Sentiment not calculated for all comments"
