import asyncio
from datetime import datetime
from typing import Dict, Any
from api.clients.websocket_manager import manager
from api.clients.db import get_db_pool
import logging

logger = logging.getLogger(__name__)


async def broadcast_user_status_update(user_id: int, status_data: Dict[str, Any]):
    """
    Broadcast user status update to all connected clients
    
    Args:
        user_id: ID of the user whose status changed
        status_data: Dictionary containing the status information
    """
    try:
        # Add timestamp to the status data
        status_data["timestamp"] = datetime.utcnow().isoformat()
        status_data["user_id"] = user_id
        
        # Create the message to broadcast
        message = {
            "type": "user_status_update",
            "user_id": user_id,
            "status": status_data
        }
        
        # Broadcast to all feed page connections
        await manager.broadcast_to_feed(message)
        
        # Publish to Redis for other server instances
        await manager.publish_status_update(user_id, status_data)
        
        logger.info(f"Broadcasted status update for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast status update for user {user_id}: {e}")


async def get_user_status_for_broadcast(user_id: int) -> Dict[str, Any]:
    """
    Get current user status data for broadcasting
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary containing status information
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get user basic info and status
            result = await conn.fetchrow(
                """
                SELECT 
                    u.user_id,
                    u.username,
                    u.profile_image_url,
                    us.is_online,
                    us.last_seen,
                    us.is_busy,
                    us.wait_time,
                    (us.is_online AND NOT us.is_busy) AS is_available
                FROM users u
                LEFT JOIN user_status us ON u.user_id = us.user_id
                WHERE u.user_id = $1
                """,
                user_id
            )
            
            if result:
                return {
                    "user_id": result["user_id"],
                    "username": result["username"],
                    "profile_image_url": result["profile_image_url"],
                    "is_online": result["is_online"],
                    "last_seen": result["last_seen"].isoformat() if result["last_seen"] else None,
                    "is_busy": result["is_busy"],
                    "wait_time": result["wait_time"],
                    "is_available": result["is_available"]
                }
            else:
                logger.warning(f"User {user_id} not found for status broadcast")
                return {}
                
    except Exception as e:
        logger.error(f"Failed to get user status for broadcast: {e}")
        return {}


async def broadcast_user_joined(user_id: int):
    """Broadcast when a user comes online"""
    status_data = await get_user_status_for_broadcast(user_id)
    if status_data:
        await broadcast_user_status_update(user_id, status_data)


async def broadcast_user_left(user_id: int):
    """Broadcast when a user goes offline"""
    status_data = {
        "user_id": user_id,
        "is_online": False,
        "is_available": False,
        "is_busy": False
    }
    await broadcast_user_status_update(user_id, status_data)


async def broadcast_user_busy_status_change(user_id: int, is_busy: bool, wait_time=None):
    """Broadcast when a user's busy status changes"""
    status_data = await get_user_status_for_broadcast(user_id)
    if status_data:
        status_data["is_busy"] = is_busy
        status_data["wait_time"] = wait_time
        status_data["is_available"] = status_data["is_online"] and not is_busy
        await broadcast_user_status_update(user_id, status_data)
