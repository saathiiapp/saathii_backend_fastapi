from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List
import time
from app.clients.redis_client import redis_client
from app.clients.db import get_db_pool
from app.clients.jwt_handler import decode_jwt
from app.utils.presence import mark_inactive_users_offline, cleanup_expired_busy_status
from app.schemas.user import (
    UserResponse, 
    EditUserRequest, 
    UserStatusResponse, 
    UpdateStatusRequest, 
    HeartbeatRequest, 
    UserPresenceResponse
)

router = APIRouter()


async def get_current_user_async(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    # Reject if blacklisted (scoped by user id and access jti)
    user_id = payload.get("user_id")
    jti = payload.get("jti")
    if user_id and jti and await redis_client.get(f"access:{user_id}:{jti}"):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    return payload


@router.get("/users/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user_async)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow(
            """
            SELECT 
                u.*,
                array_agg(ur.role) FILTER (WHERE ur.active = TRUE) AS roles
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE u.user_id = $1
            GROUP BY u.user_id
            """,
            user["user_id"],
        )
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(db_user)


@router.put("/users/me", response_model=UserResponse)
async def edit_me(data: EditUserRequest, user=Depends(get_current_user_async)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow(
            """
            UPDATE users
            SET username=COALESCE($2, username),
                bio=COALESCE($3, bio),
                rating=COALESCE($4, rating),
                interests=COALESCE($5, interests),
                profile_image_url=COALESCE($6, profile_image_url),
                preferred_language=COALESCE($7, preferred_language),
                updated_at=now()
            WHERE user_id=$1
            RETURNING *;
        """,
            user["user_id"],
            data.username,
            data.bio,
            data.rating,
            data.interests,
            data.profile_image_url,
            data.preferred_language,
        )
        return dict(db_user)


@router.delete("/users/me")
async def delete_me(authorization: str = Header(...), user=Depends(get_current_user_async)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Remove dependent rows first to satisfy FK constraints
        await conn.execute("DELETE FROM user_roles WHERE user_id=$1", user["user_id"])
        await conn.execute("DELETE FROM users WHERE user_id=$1", user["user_id"])

    # Revoke all refresh tokens for the user
    pattern = f"refresh:{user['user_id']}:*"
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)

    # Blacklist current access token by jti until expiry
    jti = user.get("jti")
    exp = user.get("exp")
    if jti and exp:
        ttl_seconds = int(exp - time.time())
        if ttl_seconds > 0:
            await redis_client.setex(f"access:{user['user_id']}:{jti}", ttl_seconds, "1")

    return {"message": "User deleted"}


# Status/Presence endpoints for React Native
@router.get("/users/me/status", response_model=UserStatusResponse)
async def get_my_status(user=Depends(get_current_user_async)):
    """Get current user's online status"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        status = await conn.fetchrow(
            "SELECT * FROM user_status WHERE user_id = $1",
            user["user_id"]
        )
        if not status:
            raise HTTPException(status_code=404, detail="User status not found")
        return dict(status)


@router.put("/users/me/status", response_model=UserStatusResponse)
async def update_my_status(data: UpdateStatusRequest, user=Depends(get_current_user_async)):
    """Update current user's online status (online/offline, busy status)"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build dynamic update query
        updates = []
        params = [user["user_id"]]
        param_count = 1
        
        if data.is_online is not None:
            param_count += 1
            updates.append(f"is_online = ${param_count}")
            params.append(data.is_online)
            
        if data.is_busy is not None:
            param_count += 1
            updates.append(f"is_busy = ${param_count}")
            params.append(data.is_busy)
            
        if data.busy_until is not None:
            param_count += 1
            updates.append(f"busy_until = ${param_count}")
            params.append(data.busy_until)
        
        # Always update last_seen and updated_at
        param_count += 1
        updates.append(f"last_seen = ${param_count}")
        params.append("now()")
        
        param_count += 1
        updates.append(f"updated_at = ${param_count}")
        params.append("now()")
        
        if not updates:
            raise HTTPException(status_code=400, detail="No status fields to update")
            
        query = f"""
            UPDATE user_status 
            SET {', '.join(updates)}
            WHERE user_id = $1
            RETURNING *
        """
        
        status = await conn.fetchrow(query, *params)
        if not status:
            raise HTTPException(status_code=404, detail="User status not found")
        return dict(status)


@router.post("/users/me/heartbeat")
async def heartbeat(user=Depends(get_current_user_async)):
    """Send heartbeat to keep user online and update last_seen"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE user_status 
            SET last_seen = now(), updated_at = now()
            WHERE user_id = $1
            """,
            user["user_id"]
        )
    return {"message": "Heartbeat received"}


@router.get("/users/{user_id}/presence", response_model=UserPresenceResponse)
async def get_user_presence(user_id: int, user=Depends(get_current_user_async)):
    """Get another user's presence status"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        presence = await conn.fetchrow(
            """
            SELECT 
                us.user_id,
                u.username,
                us.is_online,
                us.last_seen,
                us.is_busy,
                us.busy_until
            FROM user_status us
            JOIN users u ON us.user_id = u.user_id
            WHERE us.user_id = $1
            """,
            user_id
        )
        if not presence:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(presence)


@router.get("/users/presence", response_model=List[UserPresenceResponse])
async def get_multiple_users_presence(
    user_ids: str,  # Comma-separated user IDs
    user=Depends(get_current_user_async)
):
    """Get presence status for multiple users"""
    try:
        ids = [int(id.strip()) for id in user_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user IDs format")
    
    if len(ids) > 50:  # Limit to prevent abuse
        raise HTTPException(status_code=400, detail="Too many user IDs requested")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        presences = await conn.fetch(
            """
            SELECT 
                us.user_id,
                u.username,
                us.is_online,
                us.last_seen,
                us.is_busy,
                us.busy_until
            FROM user_status us
            JOIN users u ON us.user_id = u.user_id
            WHERE us.user_id = ANY($1)
            ORDER BY us.user_id
            """,
            ids
        )
        return [dict(presence) for presence in presences]


@router.post("/admin/cleanup-presence")
async def cleanup_presence(user=Depends(get_current_user_async)):
    """Admin endpoint to manually trigger presence cleanup"""
    # Note: In production, you might want to add admin role checking here
    
    # Mark inactive users as offline (5 minutes threshold)
    offline_result = await mark_inactive_users_offline(inactive_minutes=5)
    
    # Clean up expired busy status
    busy_result = await cleanup_expired_busy_status()
    
    return {
        "message": "Presence cleanup completed",
        "users_marked_offline": offline_result,
        "busy_status_cleared": busy_result
    }
