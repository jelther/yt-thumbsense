import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from yt_thumbsense.config import Settings, get_settings
from yt_thumbsense.database import use_database
from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.models.video import DetailedVideoItem, VideoItem
from yt_thumbsense.tasks import start_single_video
from yt_thumbsense.utils import is_valid_youtube_video
from yt_thumbsense.worker import main_queue

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/request/", response_model=DetailedVideoItem, tags=["request"])
async def request_by_video_id(
    video_to_process: VideoItem,
    settings: Annotated[Settings, Depends(get_settings)],
    db=Depends(use_database),
):
    """Request processing the comments for a video."""
    logger.info(f"Processing video {video_to_process.video_id}")

    current_time: datetime = datetime.now()

    if not is_valid_youtube_video(video_to_process.video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID.")

    existing_video = await db.videos.find_one({"video_id": video_to_process.video_id})
    if not existing_video:
        new_video = {
            "video_id": video_to_process.video_id,
            "status": ProcessingStatus.pending,
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
        }
        await db.videos.insert_one(new_video)
        main_queue.enqueue(
            start_single_video,
            video_to_process.video_id,
        )

        logger.info(f"Enqueued video {video_to_process.video_id} for processing.")
        return new_video

    elif existing_video["status"] != ProcessingStatus.pending:
        # Check if we should reprocess based on status and last update time
        last_updated = existing_video["updated_at"]
        reprocess_after = timedelta(hours=settings.reprocess_after_hours)

        if current_time - datetime.fromisoformat(last_updated) > reprocess_after:
            # Reset to pending and update timestamp
            await db.videos.update_one(
                {"video_id": video_to_process.video_id},
                {
                    "$set": {
                        "status": ProcessingStatus.pending,
                        "updated_at": current_time,
                    }
                },
            )
            existing_video["status"] = ProcessingStatus.pending
            existing_video["updated_at"] = current_time

            main_queue.enqueue(
                start_single_video,
                video_to_process.video_id,
            )

            logger.info(f"Enqueued video {video_to_process.video_id} for processing.")
        else:
            logger.info(
                f"Video {video_to_process.video_id} has already been processed "
                f"within the last {settings.reprocess_after_hours} hours."
            )
    else:
        logger.info(f"Video {video_to_process.video_id} is already pending.")

    return existing_video
