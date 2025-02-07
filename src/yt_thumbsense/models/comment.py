from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel

from yt_thumbsense.models.request import ProcessingStatus


class CommentItem(BaseModel):
    video_id: str
    comment_id: str
    comment_parent_id: Union[str, None]
    text: str
    votes: int
    replies: int
    time_posted: Union[datetime, None]
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    vader_sentiment: Optional[dict] = {}
