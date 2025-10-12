"""
Badge-related background services
"""
import logging
from datetime import date, timedelta
from api.clients.db import get_db_pool
from api.utils.badge_manager import assign_badges_for_all_listeners

logger = logging.getLogger(__name__)

async def assign_daily_badges():
    """Assign badges for today based on yesterday's performance"""
    try:
        today = date.today()
        logger.info(f"🏆 Starting badge assignment for {today}")
        
        stats = await assign_badges_for_all_listeners(today)
        
        logger.info(f"✅ Badge assignment completed for {today}:")
        logger.info(f"   Total listeners: {stats['total_listeners']}")
        logger.info(f"   Basic: {stats['basic_assigned']}")
        logger.info(f"   Bronze: {stats['bronze_assigned']}")
        logger.info(f"   Silver: {stats['silver_assigned']}")
        logger.info(f"   Gold: {stats['gold_assigned']}")
        logger.info(f"   Errors: {stats['errors']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to assign badges for {today}: {e}")
        raise
