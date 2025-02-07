from yt_thumbsense.main import get_settings
from yt_thumbsense.tasks import start_pending_videos
from yt_thumbsense.worker import scheduler


def init_scheduler():
    settings = get_settings()

    scheduler.cron(
        cron_string=f"*/{settings.process_pending_videos_interval_minutes} * * * *",
        func=start_pending_videos,
    )
