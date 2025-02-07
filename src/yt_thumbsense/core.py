from slowapi import Limiter
from slowapi.util import get_remote_address

from yt_thumbsense.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=settings.rate_limits)
