from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List
import time
from app.clients.redis_client import redis_client
from app.clients.db import get_db_pool
from app.clients.jwt_handler import decode_jwt
from app.utils.presence import mark_inactive_users_offline, cleanup_expired_busy_status
from app.utils.realtime import broadcast_user_status_update, get_user_status_for_broadcast
from app.schemas.user import (
    UserResponse, 
    EditUserRequest, 
    UserStatusResponse, 
    UpdateStatusRequest, 
    HeartbeatRequest, 
    UserPresenceResponse,
    ListenerFeedItem,
    FeedResponse,
    FeedFilters
)

router = APIRouter(tags=["User Management"])


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


@router.get("/users/me", response_model=UserResponse, tags=["User Management", "Profile"])
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


@router.put("/users/me", response_model=UserResponse, tags=["User Management", "Profile"])
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


@router.delete("/users/me", tags=["User Management", "Profile"])
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
@router.get("/users/me/status", response_model=UserStatusResponse, tags=["User Management", "Presence"])
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


@router.put("/users/me/status", response_model=UserStatusResponse, tags=["User Management", "Presence"])
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
        
        # Broadcast status update to all connected clients
        status_data = await get_user_status_for_broadcast(user["user_id"])
        if status_data:
            await broadcast_user_status_update(user["user_id"], status_data)
        
        return dict(status)


@router.post("/users/me/heartbeat", tags=["User Management", "Presence"])
async def heartbeat(user=Depends(get_current_user_async)):
    """Send heartbeat to keep user online and update last_seen"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Update last_seen timestamp
        await conn.execute(
            """
            UPDATE user_status 
            SET last_seen = now(), updated_at = now()
            WHERE user_id = $1
            """,
            user["user_id"]
        )
        
        # Get updated status for broadcasting
        status_data = await get_user_status_for_broadcast(user["user_id"])
        if status_data:
            # Broadcast status update to all connected clients
            await broadcast_user_status_update(user["user_id"], status_data)
    
    return {"message": "Heartbeat received"}


@router.get("/users/{user_id}/presence", response_model=UserPresenceResponse, tags=["User Management", "Presence"])
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


@router.get("/users/presence", response_model=List[UserPresenceResponse], tags=["User Management", "Presence"])
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


@router.post("/admin/cleanup-presence", tags=["User Management", "Admin"])
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


@router.get("/feed/listeners", response_model=FeedResponse, tags=["User Management", "Feed"])
async def get_listeners_feed(
    online_only: bool = False,
    available_only: bool = False,
    language: str = None,
    interests: str = None,  # Comma-separated string
    min_rating: int = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """
    Get all listeners for the feed page with their details and status.
    
    - **online_only**: Show only online users
    - **available_only**: Show only available users (online and not busy)
    - **language**: Filter by preferred language
    - **interests**: Filter by interests (comma-separated)
    - **min_rating**: Minimum rating filter
    - **page**: Page number for pagination
    - **per_page**: Number of items per page
    """
    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    # Parse interests if provided
    interest_list = None
    if interests:
        interest_list = [interest.strip() for interest in interests.split(",") if interest.strip()]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build the base query
        base_query = """
            SELECT 
                u.user_id,
                u.username,
                u.sex,
                u.bio,
                u.interests,
                u.profile_image_url,
                u.preferred_language,
                u.rating,
                u.country,
                array_agg(ur.role) FILTER (WHERE ur.active = TRUE) AS roles,
                us.is_online,
                us.last_seen,
                us.is_busy,
                us.busy_until,
                (us.is_online AND NOT us.is_busy) AS is_available
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id != $1  -- Exclude current user
        """
        
        # Build WHERE conditions
        conditions = ["u.user_id != $1"]
        params = [user["user_id"]]
        param_count = 1
        
        if online_only:
            param_count += 1
            conditions.append(f"us.is_online = ${param_count}")
            params.append(True)
        
        if available_only:
            param_count += 1
            conditions.append(f"us.is_online = ${param_count}")
            params.append(True)
            param_count += 1
            conditions.append(f"us.is_busy = ${param_count}")
            params.append(False)
        
        if language:
            param_count += 1
            conditions.append(f"u.preferred_language = ${param_count}")
            params.append(language)
        
        if interest_list:
            param_count += 1
            conditions.append(f"u.interests && ${param_count}")
            params.append(interest_list)
        
        if min_rating is not None:
            param_count += 1
            conditions.append(f"u.rating >= ${param_count}")
            params.append(min_rating)
        
        # Add WHERE clause
        if len(conditions) > 1:  # More than just the user_id exclusion
            base_query += " AND " + " AND ".join(conditions[1:])
        
        # Add GROUP BY and ORDER BY
        base_query += """
            GROUP BY u.user_id, us.is_online, us.last_seen, us.is_busy, us.busy_until
            ORDER BY 
                us.is_online DESC,  -- Online users first
                us.is_busy ASC,     -- Available users first
                u.rating DESC NULLS LAST,  -- Higher rated users first
                us.last_seen DESC   -- Recently active users first
        """
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE {' AND '.join(conditions)}
        """
        
        total_count = await conn.fetchval(count_query, *params)
        
        # Get online and available counts
        online_count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE {' AND '.join(conditions)} AND us.is_online = true
        """
        online_count = await conn.fetchval(online_count_query, *params)
        
        available_count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE {' AND '.join(conditions)} AND us.is_online = true AND us.is_busy = false
        """
        available_count = await conn.fetchval(available_count_query, *params)
        
        # Add pagination to the main query
        paginated_query = base_query + f" LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([per_page, offset])
        
        # Execute the main query
        listeners_data = await conn.fetch(paginated_query, *params)
        
        # Convert to response models
        listeners = []
        for row in listeners_data:
            listener = ListenerFeedItem(
                user_id=row["user_id"],
                username=row["username"],
                sex=row["sex"],
                bio=row["bio"],
                interests=row["interests"],
                profile_image_url=row["profile_image_url"],
                preferred_language=row["preferred_language"],
                rating=row["rating"],
                country=row["country"],
                roles=row["roles"],
                is_online=row["is_online"],
                last_seen=row["last_seen"],
                is_busy=row["is_busy"],
                busy_until=row["busy_until"],
                is_available=row["is_available"]
            )
            listeners.append(listener)
        
        # Calculate pagination info
        has_next = offset + per_page < total_count
        has_previous = page > 1
        
        return FeedResponse(
            listeners=listeners,
            total_count=total_count,
            online_count=online_count,
            available_count=available_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )


@router.get("/feed/stats", tags=["User Management", "Feed"])
async def get_feed_stats(user=Depends(get_current_user_async)):
    """
    Get listener statistics for the feed page.
    Returns counts of total, online, and available listeners.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get total listeners (excluding current user)
        total_count = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE user_id != $1",
            user["user_id"]
        )
        
        # Get online listeners
        online_count = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id != $1 AND us.is_online = true
            """,
            user["user_id"]
        )
        
        # Get available listeners (online and not busy)
        available_count = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id != $1 AND us.is_online = true AND us.is_busy = false
            """,
            user["user_id"]
        )
        
        return {
            "total_listeners": total_count,
            "online_listeners": online_count,
            "available_listeners": available_count,
            "busy_listeners": online_count - available_count
        }
