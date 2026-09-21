import redis.asyncio as redis
import os
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Global singleton client
_redis_pool = None

async def get_redis() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        _redis_pool = redis.from_url(url, decode_responses=True)
        # Verify connection
        try:
            await _redis_pool.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {url}: {e}")
            raise
    return _redis_pool

async def publish_event(call_id: str, event_json: str):
    """Publish an event to the specific call's channel"""
    r = await get_redis()
    await r.publish(f"channel:call:{call_id}", event_json)

async def subscribe_events(call_id: str) -> AsyncGenerator[str, None]:
    """Yields events published to a call channel"""
    r = await get_redis()
    pubsub = r.pubsub()
    channel = f"channel:call:{call_id}"
    await pubsub.subscribe(channel)
    
    logger.info(f"Subscribed to {channel}")
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                yield message['data']
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        
async def set_state(key: str, value: str, expire_seconds: int = 3600):
    r = await get_redis()
    await r.setex(key, expire_seconds, value)
    
async def get_state(key: str) -> str:
    r = await get_redis()
    return await r.get(key)
