from fastapi import APIRouter, Depends, HTTPException, Header

from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.utils.badge_manager import get_current_listener_badge, assign_basic_badge_for_today
from api.utils.user_validation import validate_user_active, enforce_listener_verified
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
    
    # Validate user is active
    user_id = payload.get("user_id")
    await validate_user_active(user_id)
    
    return payload


@router.get("/listener/badge/current", response_model=BadgeCurrentResponse)
async def get_current_badge(user=Depends(get_current_user_async)):
    """Get current badge for the authenticated verified listener for today. 
    If no badge exists for today, assigns a basic badge automatically (verified listeners only)."""
    user_id = user["user_id"]
    
    # Ensure user is a verified listener
    await enforce_listener_verified(user_id)

    # Get current badge for today
    badge_info = await get_current_listener_badge(user_id)
    
    # If no badge exists for today, assign a basic badge
    if not badge_info:
        badge_info = await assign_basic_badge_for_today(user_id)
    
    # If still no badge (shouldn't happen), return error
    if not badge_info:
        raise HTTPException(status_code=500, detail="Unable to retrieve or assign badge")

    return {
        "listener_id": user_id,
        "current_badge": badge_info['badge'],
        "audio_rate_per_minute": badge_info['audio_rate_per_minute'],
        "video_rate_per_minute": badge_info['video_rate_per_minute'],
        "assigned_date": badge_info['assigned_date'],
        "assigned_at": badge_info['assigned_at']
    }


