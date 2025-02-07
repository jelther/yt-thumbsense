from pydantic import BaseModel, Field


class SentimentScoreItem(BaseModel):
    video_id: str = Field(
        description="A valid YouTube video ID. It must be exactly 11 characters long and can include letters, numbers, '-' and '_'."
    )

    comment_count: int

    sentiment_score: float
    sentiment_score_std: float
    sentiment_score_min: float
    sentiment_score_max: float
