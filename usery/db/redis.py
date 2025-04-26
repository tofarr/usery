import redis
from usery.config.settings import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)


def get_redis():
    """Dependency for getting Redis client."""
    try:
        yield redis_client
    finally:
        # No need to close Redis connection as it's managed by the client
        pass