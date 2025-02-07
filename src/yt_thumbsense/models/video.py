from datetime import datetime

from pydantic import BaseModel, Field

from yt_thumbsense.models.request import ProcessingStatus


class VideoItem(BaseModel):
    video_id: str = Field(
        description="A valid YouTube video ID. It must be exactly 11 characters long and can include letters, numbers, '-' and '_'."
    )

    class Config:
        schema_extra = {"example": {"id": "A1b2C3d4EfG"}}


class DetailedVideoItem(VideoItem):
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": "A1b2C3d4EfG",
                "status": "pending",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            }
        }
