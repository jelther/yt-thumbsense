from fastapi import APIRouter
from starlette.requests import Request

from yt_thumbsense.config import get_settings
from yt_thumbsense.core import limiter

router = APIRouter()


@router.get("/", tags=["root"])
@limiter.exempt
async def root_path():
    """Return the app name and version."""
    settings = get_settings()
    return {"app_name": settings.app_name, "version": settings.version}


@router.get("/health", tags=["root"])
@limiter.exempt
async def health_check(request: Request):
    return {"status": "ok"}
