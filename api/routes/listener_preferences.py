from fastapi import APIRouter, Depends, HTTPException, Header
from api.clients.jwt_handler import decode_jwt
from api.clients.redis_client import redis_client
from api.clients.db import get_db_pool
from api.utils.user_validation import validate_user_active, enforce_listener_verified
from api.schemas.listener_preferences import ListenerPreferencesResponse, UpdateListenerPreferencesRequest

router = APIRouter(tags=["Listener Preferences"])

async def get_current_user_async(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    # Reject if blacklisted
    user_id = payload.get("user_id")
    jti = payload.get("jti")
    if user_id and jti and await redis_client.get(f"access:{user_id}:{jti}"):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    # Validate user is active
    await validate_user_active(user_id)
    
    return payload

@router.get("/listener/preferences", response_model=ListenerPreferencesResponse)
async def get_listener_preferences(user=Depends(get_current_user_async)):
    """Get listener call preferences"""
    user_id = user["user_id"]
    
    # Check if user is a listener
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        listener_role = await conn.fetchrow(
            """
            SELECT role FROM user_roles 
            WHERE user_id = $1 AND role = 'listener' AND active = true
            """,
            user_id
        )
        if not listener_role:
            raise HTTPException(
                status_code=403, 
                detail="Only users with listener role can access this endpoint"
            )
        
        # Enforce listener verification
        await enforce_listener_verified(user_id)
        
        # Get listener preferences
        preferences = await conn.fetchrow(
            """
            SELECT listener_id, listener_allowed_call_type, listener_audio_call_enable, 
                   listener_video_call_enable
            FROM listener_profile 
            WHERE listener_id = $1
            """,
            user_id
        )
        
        if not preferences:
            raise HTTPException(
                status_code=404,
                detail="Listener preferences not found. Please complete registration."
            )
        
        return ListenerPreferencesResponse(
            listener_id=preferences["listener_id"],
            listener_allowed_call_type=preferences["listener_allowed_call_type"],
            listener_audio_call_enable=preferences["listener_audio_call_enable"],
            listener_video_call_enable=preferences["listener_video_call_enable"]
        )

@router.put("/listener/preferences", response_model=ListenerPreferencesResponse)
async def update_listener_preferences(
    data: UpdateListenerPreferencesRequest, 
    user=Depends(get_current_user_async)
):
    """Update listener call preferences"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        listener_role = await conn.fetchrow(
            """
            SELECT role FROM user_roles 
            WHERE user_id = $1 AND role = 'listener' AND active = true
            """,
            user_id
        )
        if not listener_role:
            raise HTTPException(
                status_code=403, 
                detail="Only users with listener role can access this endpoint"
            )

        await enforce_listener_verified(user_id)
        
        update_fields = []
        update_values = []
        param_count = 0
        
        if data.listener_audio_call_enable is not None:
            param_count += 1
            update_fields.append(f"listener_audio_call_enable = ${param_count}")
            update_values.append(data.listener_audio_call_enable)
        
        if data.listener_video_call_enable is not None:
            param_count += 1
            update_fields.append(f"listener_video_call_enable = ${param_count}")
            update_values.append(data.listener_video_call_enable)

        if not update_fields:
            raise HTTPException(
                status_code=400,
                detail="At least one preference field must be provided for update"
            )

        update_fields.append("updated_at = now()")

        # WHERE listener_id
        param_count += 1
        update_values.append(user_id)

        await conn.execute(
            f"""
            UPDATE listener_profile 
            SET {', '.join(update_fields)}
            WHERE listener_id = ${param_count}
            """,
            *update_values
        )
        
        preferences = await conn.fetchrow(
            """
            SELECT listener_id, listener_allowed_call_type, listener_audio_call_enable, 
                   listener_video_call_enable
            FROM listener_profile 
            WHERE listener_id = $1
            """,
            user_id
        )
        
        return ListenerPreferencesResponse(
            listener_id=preferences["listener_id"],
            listener_allowed_call_type=preferences["listener_allowed_call_type"],
            listener_audio_call_enable=preferences["listener_audio_call_enable"],
            listener_video_call_enable=preferences["listener_video_call_enable"]
        )
