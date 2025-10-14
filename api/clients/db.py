import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")
_pool = None  # global variable to reuse the pool


async def get_db_pool():
    """
    Returns a shared asyncpg connection pool.
    Initializes it once on first call.
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            statement_cache_size=0
        )
    return _pool


async def close_db_pool():
    """Gracefully close the pool during shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
