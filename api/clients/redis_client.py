import os
import redis.asyncio as aioredis
import redis.exceptions
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Create Redis client with proper configuration
redis_client = aioredis.from_url(
    REDIS_URL, 
    decode_responses=True,
    retry_on_timeout=True,
    socket_keepalive=True,
    socket_keepalive_options={},
    health_check_interval=30,
    retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],
    socket_connect_timeout=5,
    socket_timeout=5
)

async def test_redis_connection():
    """Test Redis connection and verify it's not read-only"""
    import asyncio
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Test basic connectivity
            await redis_client.ping()
            
            # Test write capability by trying to set a test key
            test_key = "test_write_capability"
            await redis_client.set(test_key, "test", ex=1)  # Expires in 1 second
            await redis_client.delete(test_key)
            
            logger.info("Redis connection successful and write-enabled")
            return True
        except redis.exceptions.ReadOnlyError:
            logger.error("Redis is in read-only mode. Check if connected to a replica instead of master.")
            raise
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Redis connection failed after {max_retries} attempts: {e}")
                raise
