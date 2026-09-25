import os
import redis.asyncio as redis

# Uses Render's Redis in production, falls back to Docker Desktop locally
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)