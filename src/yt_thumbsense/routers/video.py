from fastapi import APIRouter, Depends, HTTPException

from yt_thumbsense.database import use_database
from yt_thumbsense.models.comment import CommentItem
from yt_thumbsense.models.video import DetailedVideoItem

router = APIRouter()


@router.get("/video/{video_id}", tags=["videos"], response_model=DetailedVideoItem)
async def get_video(video_id: str, db=Depends(use_database)):
    """Return a single video from the database."""
    video = await db.videos.find_one({"video_id": video_id})
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.delete("/video/{video_id}", tags=["videos"])
async def delete_video(video_id: str, db=Depends(use_database)):
    """Delete a single video from the database."""
    result = await db.videos.delete_one({"video_id": video_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete comments as well if the video is deleted
    await db.comments.delete_many({"video_id": video_id})

    return {"message": "Video deleted"}


@router.get("/videos", tags=["videos"], response_model=list[DetailedVideoItem])
async def list_videos(skip: int = 0, limit: int = 10, db=Depends(use_database)):
    """Return a paginated list of videos from the database.

    Args:
        skip: Number of videos to skip (offset)
        limit: Maximum number of videos to return
    """
    cursor = db.videos.find({}).skip(skip).limit(limit)
    videos = await cursor.to_list(length=None)
    return videos


@router.get(
    "/video/{video_id}/comments", tags=["videos"], response_model=list[CommentItem]
)
async def get_video_comments(
    video_id: str, skip: int = 0, limit: int = 10, db=Depends(use_database)
):
    """Return a paginated list of comments for a video.

    Args:
        video_id: ID of the video to get comments for
        skip: Number of comments to skip (offset)
        limit: Maximum number of comments to return
    """
    cursor = db.comments.find({"video_id": video_id}).skip(skip).limit(limit)
    comments = await cursor.to_list(length=None)
    return comments
