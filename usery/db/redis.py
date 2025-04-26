from redis.asyncio import Redis
from fastapi import Request
from usery.config.settings import settings

# Create a Redis connection pool
async def create_redis_pool():
    """Create a Redis connection pool."""
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
    )

async def get_redis(request: Request):
    """Dependency for getting async Redis client."""
    try:
        # Get Redis from app state (initialized at startup)
        yield request.app.state.redis
    finally:
        # No need to close Redis connection as it's managed by the app lifecycle
        pass