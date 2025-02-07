from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from yt_thumbsense.database import use_database
from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.models.score import SentimentScoreItem
from yt_thumbsense.utils import is_valid_youtube_video

router = APIRouter()


@router.get(
    "/score/video/{video_id}", tags=["score"], response_model=SentimentScoreItem
)
async def get_score(video_id: str, db: AsyncIOMotorDatabase = Depends(use_database)):
    """
    Get the sentiment score for a video

    Args:
        video_id: YouTube video ID
        db: Database connection

    Returns:
        SentimentScoreItem with sentiment analysis results

    Raises:
        HTTPException: If video_id is invalid or comments are not found/processed
    """
    if not is_valid_youtube_video(video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID")

    cursor = db.comments.find(
        {"video_id": video_id, "status": ProcessingStatus.processed}
    )
    comments: List[Dict[str, Any]] = await cursor.to_list(length=None)

    if not comments:
        raise HTTPException(status_code=404, detail="Comments not found")

    if any(comment.get("vader_sentiment") is None for comment in comments):
        raise HTTPException(
            status_code=500, detail="Sentiment not calculated for all comments"
        )

    try:
        vader_sentiment_dataframe: pd.DataFrame = pd.DataFrame(
            [
                comment["vader_sentiment"]
                for comment in comments
                if comment.get("vader_sentiment")
            ]
        )

        compound_sentiment_score: float = float(
            vader_sentiment_dataframe["compound"].mean()
        )
        compound_sentiment_score_std: float = float(
            vader_sentiment_dataframe["compound"].std()
        )
        compound_sentiment_score_min: float = float(
            vader_sentiment_dataframe["compound"].min()
        )
        compound_sentiment_score_max: float = float(
            vader_sentiment_dataframe["compound"].max()
        )

        comment_count: int = len(comments)

        return SentimentScoreItem(
            video_id=video_id,
            comment_count=comment_count,
            sentiment_score=compound_sentiment_score,
            sentiment_score_std=compound_sentiment_score_std,
            sentiment_score_min=compound_sentiment_score_min,
            sentiment_score_max=compound_sentiment_score_max,
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing sentiment data: {str(e)}"
        )
