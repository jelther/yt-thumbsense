import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from yt_thumbsense.config import get_settings
from yt_thumbsense.core import limiter
from yt_thumbsense.routers import request, root, score, video
from yt_thumbsense.scheduler import init_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


@asynccontextmanager
async def lifespan(current_app: FastAPI):
    init_scheduler()
    yield
    pass


settings = get_settings()

# API
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    contact=(
        {
            "name": settings.api_contact_name,
            "url": settings.api_contact_url,
            "email": settings.api_contact_email,
        }
        if settings.api_contact_name
        else None
    ),
    license_info={"name": settings.api_license_name, "url": settings.api_license_url},
    lifespan=lifespan,
)

# Routers
app.include_router(video.router)
app.include_router(root.router)
app.include_router(request.router)
app.include_router(score.router)


# Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

if __name__ == "__main__":
    uvicorn.run(app)
