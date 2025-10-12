"""
Presence-related background services
"""
import logging
from datetime import datetime, timedelta
from api.clients.db import get_db_pool

logger = logging.getLogger(__name__)

async def mark_inactive_users_offline(inactive_minutes: int = 5):
    """
    Mark users as offline if they haven't been seen for more than inactive_minutes
    This should be called periodically (e.g., every minute via a background task)
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        cutoff_time = datetime.utcnow() - timedelta(minutes=inactive_minutes)
        
        result = await conn.execute(
            """
            UPDATE user_status 
            SET is_online = FALSE, updated_at = now()
            WHERE is_online = TRUE 
            AND last_seen < $1
            """,
            cutoff_time
        )
        
        logger.info(f"Marked {result} users as offline")
        return result

async def cleanup_expired_busy_status():
    """
    Clear busy status for users whose wait_time has expired
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_status 
            SET is_busy = FALSE, wait_time = NULL, updated_at = now()
            WHERE is_busy = TRUE 
            AND wait_time IS NOT NULL 
            AND wait_time <= 0
            """,
        )
        
        logger.info(f"Cleared {result} expired busy statuses")
        return result

async def get_online_users_count() -> int:
    """Get count of currently online users"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM user_status WHERE is_online = TRUE")
        return count or 0
