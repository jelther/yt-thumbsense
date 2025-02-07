from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from yt_thumbsense import __VERSION__


class Settings(BaseSettings):
    # App
    app_name: str = "yt-thumbsense"
    version: str = __VERSION__

    # API Documentation
    api_title: str = "yt-thumbsense"
    api_description: str = "An API for analyzing YouTube video likes and comments"
    api_version: str = version
    api_contact_name: str | None = None
    api_contact_url: str | None = None
    api_contact_email: str | None = None
    api_license_name: str = "MIT"
    api_license_url: str = "https://opensource.org/licenses/MIT"

    # Database
    mongodb_db: str = "yt_thumbsense"
    mongodb_uri: str = (
        "mongodb://admin:password@localhost:27019/yt_thumbsense?authSource=admin"
    )

    # Redis
    redis_url: str = "redis://localhost:6381"

    # LibreTranslate
    libretranslate_url: str = "http://localhost:6000/"

    # Schedules
    process_pending_videos_interval_minutes: int = 5

    # Processing
    reprocess_after_hours: int = 24

    # Comments
    max_comments_per_video: int = 1000

    # Rate Limits
    rate_limits: list[str] = ["30/minute"]

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()
