from motor.motor_asyncio import AsyncIOMotorClient

from yt_thumbsense.config import get_settings


async def use_database():
    settings = get_settings()
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_url)
    return client[settings.mongodb_db]
