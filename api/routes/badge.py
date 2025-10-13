from fastapi import APIRouter, Depends, HTTPException, Header

from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.utils.badge_manager import get_current_listener_badge
from api.schemas.badge import BadgeCurrentResponse


router = APIRouter(tags=["Badge"])


async def get_current_user_async(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    return payload


@router.get("/listener/badge/current", response_model=BadgeCurrentResponse)
async def get_current_badge(user=Depends(get_current_user_async)):
    """Get current badge for the authenticated listener for today (listeners only)."""
    user_id = user["user_id"]

    # Check if user is a listener
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_info = await conn.fetchrow(
            "SELECT user_id, username, is_listener FROM users WHERE user_id = $1",
            user_id
        )

        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")

        if not user_info['is_listener']:
            raise HTTPException(status_code=403, detail="Only listeners can have badges")

    # Get current badge for today
    badge_info = await get_current_listener_badge(user_id)

    return {
        "listener_id": user_id,
        "username": user_info['username'],
        "current_badge": badge_info['badge'],
        "audio_rate_per_minute": badge_info['audio_rate_per_minute'],
        "video_rate_per_minute": badge_info['video_rate_per_minute'],
        "assigned_date": badge_info['assigned_date'],
        "assigned_at": badge_info['assigned_at']
    }


