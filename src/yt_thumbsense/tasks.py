from datetime import datetime

import dateparser
from libretranslatepy import LibreTranslateAPI
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from youtube_comment_downloader import SORT_BY_POPULAR, YoutubeCommentDownloader

from yt_thumbsense.config import get_settings
from yt_thumbsense.database import use_database
from yt_thumbsense.models.request import ProcessingStatus
from yt_thumbsense.worker import main_queue


async def start_single_video(video_id: str):
    db: AsyncIOMotorClient = await use_database()

    video = await db["videos"].find_one({"video_id": video_id})

    if not video:
        logger.error(f"Video {video_id} not found on database.")
        return

    if video["status"] == ProcessingStatus.pending:
        await db["videos"].update_one(
            {"video_id": video_id},
            {
                "$set": {
                    "status": ProcessingStatus.processing,
                    "updated_at": datetime.now().isoformat(),
                }
            },
        )
        main_queue.enqueue(pull_video_comments_from_youtube, video_id)
    else:
        logger.info(
            f"Video {video_id} is not able to be processed. Status is {video['status']}."
        )


async def start_pending_videos():
    logger.info("Started looking for pending videos")
    db: AsyncIOMotorClient = await use_database()
    pending_videos = (
        await db["videos"].find({"status": ProcessingStatus.pending}).to_list(None)
    )

    if not pending_videos:
        logger.info("No pending videos found")
        return

    logger.info(f"{len(pending_videos)} pending video(s) found")

    for pending_video in pending_videos:
        logger.info(f"Processing video {pending_video['video_id']}")
        await db["videos"].update_one(
            {"video_id": pending_video["video_id"]},
            {
                "$set": {
                    "status": ProcessingStatus.processing,
                    "updated_at": datetime.now().isoformat(),
                }
            },
        )
        main_queue.enqueue(pull_video_comments_from_youtube, pending_video["video_id"])


async def pull_video_comments_from_youtube(video_id: str):
    logger.info(f"Processing video {video_id}")
    settings = get_settings()
    current_time = datetime.now()

    db: AsyncIOMotorClient = await use_database()

    existing_video = await db["videos"].find_one({"video_id": video_id})
    if existing_video is None:
        logger.error(f"Video {video_id} not found on database.")
        return

    try:
        youtube_downloader = YoutubeCommentDownloader()
        comments = youtube_downloader.get_comments(video_id, sort_by=SORT_BY_POPULAR)
        amount_loaded: int = 0
        for comment in comments:
            if amount_loaded >= settings.max_comments_per_video:
                logger.debug(
                    f"Reached max comments per video {settings.max_comments_per_video}"
                )
                break

            comment_parent_id = None
            if comment.get("reply", False):
                comment_parent_id, comment_id = comment.get("cid", "").split(".", 1)
            else:
                comment_id = comment.get("cid", "")

            try:
                if "edited" in comment.get("time", ""):
                    time_posted = dateparser.parse(
                        comment.get("time", "").replace("(edited)", "")
                    ).isoformat()  # type: ignore
                else:
                    time_posted = dateparser.parse(comment.get("time", "")).isoformat()  # type: ignore
            except Exception as e:
                logger.error(
                    f"Error parsing date `{comment.get('time','')}` from comment {comment_id}. Error: {e}"
                )
                time_posted = None

            try:
                votes = int(comment.get("votes", 0))
            except Exception:
                votes = 0

            try:
                replies = int(comment.get("replies", 0))
            except Exception:
                replies = 0

            existing_comment = await db["comments"].find_one(
                {"video_id": video_id, "comment_id": comment_id}
            )
            if existing_comment is not None:
                logger.debug(f"Updating comment {comment_id} for video {video_id}")
                await db["comments"].update_one(
                    {"video_id": video_id, "comment_id": comment_id},
                    {
                        "$set": {
                            "text": comment.get("text", ""),
                            "votes": votes,
                            "replies": replies,
                            "time_posted_raw": comment.get("time", ""),
                            "time_posted": time_posted,
                            "status": ProcessingStatus.pending,
                            "updated_at": current_time.isoformat(),
                        }
                    },
                )
                continue
            else:
                logger.debug(f"Inserting comment {comment_id} for video {video_id}")
                await db["comments"].insert_one(
                    {
                        "video_id": video_id,
                        "comment_id": comment_id,
                        "comment_parent_id": comment_parent_id,
                        "text": comment.get("text", ""),
                        "votes": votes,
                        "replies": replies,
                        "time_posted_raw": comment.get("time", ""),
                        "time_posted": time_posted,
                        "status": ProcessingStatus.pending,
                        "created_at": current_time.isoformat(),
                        "updated_at": current_time.isoformat(),
                    }
                )

            amount_loaded += 1

            main_queue.enqueue(
                calculate_single_video_comment_sentiment, video_id, comment_id
            )

        await db["videos"].update_one(
            {"video_id": video_id},
            {"$set": {"status": ProcessingStatus.processed}},
        )
        logger.info(f"Finished pulling comments for video {video_id}")
    except Exception as e:
        logger.error(f"Error pulling comments for video {video_id}: {e}")
        await db["videos"].update_one(
            {"video_id": video_id},
            {"$set": {"status": ProcessingStatus.failed}},
        )


async def calculate_single_video_comment_sentiment(video_id: str, comment_id: str):
    logger.info(f"Processing comment {comment_id} for video {video_id}")
    settings = get_settings()
    db: AsyncIOMotorClient = await use_database()

    video = await db["videos"].find_one({"video_id": video_id})
    if not video:
        logger.error(f"Video {video_id} not found on database.")
        # We need to clean up the DB if the video doesn't exist anymore
        await db["comments"].delete_one(
            {"video_id": video_id, "comment_id": comment_id}
        )
        return

    comment = await db["comments"].find_one(
        {"video_id": video_id, "comment_id": comment_id}
    )

    if not comment:
        logger.error(f"Comment {comment_id} for video {video_id} not found")
        return

    if comment["status"] != ProcessingStatus.pending:
        logger.error(
            f"Comment {comment_id} for video {video_id} is not pending, is {comment['status']}"
        )
        return

    try:
        libre_translate = LibreTranslateAPI(settings.libretranslate_url)

        detection = libre_translate.detect(comment["text"])
        translation: str = comment["text"]
        if detection[0]["language"] != "en":
            translation = libre_translate.translate(
                comment["text"], detection[0]["language"], "en"
            )

        analyzer = SentimentIntensityAnalyzer()
        vader_sentiment = analyzer.polarity_scores(translation)

        await db["comments"].update_one(
            {"video_id": video_id, "comment_id": comment_id},
            {
                "$set": {
                    "vader_sentiment": vader_sentiment,
                    "status": ProcessingStatus.processed,
                }
            },
        )

    except Exception as e:
        logger.error(f"Error processing comment {comment_id} for video {video_id}: {e}")
        await db["comments"].update_one(
            {"video_id": video_id, "comment_id": comment_id},
            {"$set": {"status": ProcessingStatus.failed}},
        )
    else:
        logger.info(f"Finished processing comment {comment_id} for video {video_id}")
