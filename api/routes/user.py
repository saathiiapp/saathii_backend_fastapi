from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from typing import List, Optional
import time
from datetime import datetime
from api.clients.redis_client import redis_client
from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.clients.s3_client import s3_client
from api.utils.realtime import broadcast_user_status_update, get_user_status_for_broadcast
from api.utils.badge_manager import get_current_listener_badge
from api.schemas.user import (
    UserResponse, 
    EditUserRequest, 
    UserStatusResponse, 
    UpdateStatusRequest, 
    HeartbeatRequest, 
    UserPresenceResponse,
    ListenerFeedItem,
    FeedResponse,
    FeedFilters,
    AddFavoriteRequest,
    RemoveFavoriteRequest,
    FavoriteUser,
    FavoritesResponse,
    FavoriteActionResponse,
    BlockUserRequest,
    UnblockUserRequest,
    BlockActionResponse,
    BlockedUser,
    BlockedUsersResponse,
    UploadAudioRequest,
    ListenerVerificationResponse,
    VerificationStatusResponse,
    AdminReviewRequest,
    AdminReviewResponse,
    ListenerVerificationStatus
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
            
        if data.wait_time is not None:
            param_count += 1
            updates.append(f"wait_time = ${param_count}")
            params.append(data.wait_time)
        
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


@router.post("/users/me/heartbeat")
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
                us.wait_time
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
                us.wait_time
            FROM user_status us
            JOIN users u ON us.user_id = u.user_id
            WHERE us.user_id = ANY($1)
            ORDER BY us.user_id
            """,
            ids
        )
        return [dict(presence) for presence in presences]


# Removed: /admin/cleanup-presence - redundant with background job


@router.get("/feed/listeners", response_model=FeedResponse)
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
                us.wait_time,
                (us.is_online AND NOT us.is_busy) AS is_available
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            WHERE u.user_id != $1  -- Exclude current user
            AND ub.blocked_id IS NULL  -- Exclude blocked users
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
            GROUP BY u.user_id, us.is_online, us.last_seen, us.is_busy, us.wait_time
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
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            WHERE {' AND '.join(conditions)} AND ub.blocked_id IS NULL
        """
        
        total_count = await conn.fetchval(count_query, *params)
        
        # Get online and available counts
        online_count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            WHERE {' AND '.join(conditions)} AND ub.blocked_id IS NULL AND us.is_online = true
        """
        online_count = await conn.fetchval(online_count_query, *params)
        
        available_count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            WHERE {' AND '.join(conditions)} AND ub.blocked_id IS NULL AND us.is_online = true AND us.is_busy = false
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
                wait_time=row["wait_time"],
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


@router.get("/feed/stats")
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

@router.post("/favorites/add", response_model=FavoriteActionResponse)
async def add_favorite(
    data: AddFavoriteRequest,
    user=Depends(get_current_user_async)
):
    """Add a listener to favorites"""
    user_id = user["user_id"]
    listener_id = data.listener_id
    
    # Prevent self-favorite
    if user_id == listener_id:
        raise HTTPException(status_code=400, detail="Cannot favorite yourself")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if listener exists and has listener role
        listener = await conn.fetchrow(
            """
            SELECT u.user_id, u.username
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE u.user_id = $1 AND ur.role = 'listener' AND ur.active = true
            """,
            listener_id
        )
        
        if not listener:
            raise HTTPException(status_code=404, detail="Listener not found")
        
        # Check if already favorited
        existing = await conn.fetchrow(
            "SELECT favoriter_id FROM user_favorites WHERE favoriter_id = $1 AND favoritee_id = $2",
            user_id, listener_id
        )
        
        if existing:
            return FavoriteActionResponse(
                success=True,
                message=f"Already favorited {listener['username'] or 'this listener'}",
                listener_id=listener_id,
                is_favorited=True
            )
        
        # Add to favorites
        await conn.execute(
            """
            INSERT INTO user_favorites (favoriter_id, favoritee_id, created_at, updated_at)
            VALUES ($1, $2, now(), now())
            """,
            user_id, listener_id
        )
        
        return FavoriteActionResponse(
            success=True,
            message=f"Successfully added {listener['username'] or 'listener'} to favorites",
            listener_id=listener_id,
            is_favorited=True
        )

@router.delete("/favorites/remove", response_model=FavoriteActionResponse)
async def remove_favorite(
    data: RemoveFavoriteRequest,
    user=Depends(get_current_user_async)
):
    """Remove a listener from favorites"""
    user_id = user["user_id"]
    listener_id = data.listener_id
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if listener exists
        listener = await conn.fetchrow(
            "SELECT username FROM users WHERE user_id = $1",
            listener_id
        )
        
        if not listener:
            raise HTTPException(status_code=404, detail="Listener not found")
        
        # Check if favorited
        existing = await conn.fetchrow(
            "SELECT favoriter_id FROM user_favorites WHERE favoriter_id = $1 AND favoritee_id = $2",
            user_id, listener_id
        )
        
        if not existing:
            return FavoriteActionResponse(
                success=True,
                message=f"{listener['username'] or 'Listener'} was not in favorites",
                listener_id=listener_id,
                is_favorited=False
            )
        
        # Remove from favorites
        await conn.execute(
            "DELETE FROM user_favorites WHERE favoriter_id = $1 AND favoritee_id = $2",
            user_id, listener_id
        )
        
        return FavoriteActionResponse(
            success=True,
            message=f"Successfully removed {listener['username'] or 'listener'} from favorites",
            listener_id=listener_id,
            is_favorited=False
        )

@router.get("/favorites", response_model=FavoritesResponse)
async def get_favorites(
    page: int = 1,
    per_page: int = 20,
    online_only: bool = False,
    available_only: bool = False,
    user=Depends(get_current_user_async)
):
    """Get user's favorite listeners"""
    user_id = user["user_id"]
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build base query
        base_query = """
            FROM user_favorites uf
            JOIN users u ON uf.favoritee_id = u.user_id
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE uf.favoriter_id = $1
        """
        params = [user_id]
        param_count = 1
        
        # Add filters
        if online_only:
            param_count += 1
            base_query += f" AND us.is_online = ${param_count}"
            params.append(True)
        
        if available_only:
            param_count += 1
            base_query += f" AND us.is_online = ${param_count} AND us.is_busy = ${param_count + 1}"
            params.extend([True, False])
            param_count += 1
        
        # Get total count
        count_query = f"SELECT COUNT(*) {base_query}"
        total_count = await conn.fetchval(count_query, *params)
        
        # Get favorites with pagination
        favorites_query = f"""
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
                us.is_online,
                us.last_seen,
                us.is_busy,
                us.wait_time,
                uf.created_at as favorited_at
            {base_query}
            ORDER BY uf.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([per_page, offset])
        
        favorites = await conn.fetch(favorites_query, *params)
        
        # Get online count
        online_count_query = f"""
            SELECT COUNT(*) 
            {base_query}
            AND us.is_online = true
        """
        online_count = await conn.fetchval(online_count_query, *params[:param_count])
        
        # Get available count (online and not busy)
        available_count_query = f"""
            SELECT COUNT(*) 
            {base_query}
            AND us.is_online = true AND us.is_busy = false
        """
        available_count = await conn.fetchval(available_count_query, *params[:param_count])
        
        # Format favorites
        favorite_list = []
        for fav in favorites:
            is_available = fav['is_online'] and not fav['is_busy']
            favorite_list.append(FavoriteUser(
                user_id=fav['user_id'],
                username=fav['username'],
                sex=fav['sex'],
                bio=fav['bio'],
                interests=fav['interests'],
                profile_image_url=fav['profile_image_url'],
                preferred_language=fav['preferred_language'],
                rating=fav['rating'],
                country=fav['country'],
                is_online=fav['is_online'] or False,
                last_seen=fav['last_seen'] or datetime.now(),
                is_busy=fav['is_busy'] or False,
                wait_time=fav['wait_time'],
                is_available=is_available,
                favorited_at=fav['favorited_at']
            ))
        
        has_next = offset + per_page < total_count
        has_previous = page > 1
        
        return FavoritesResponse(
            favorites=favorite_list,
            total_count=total_count,
            online_count=online_count or 0,
            available_count=available_count or 0,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )

@router.get("/favorites/check/{listener_id}", response_model=FavoriteActionResponse)
async def check_favorite_status(
    listener_id: int,
    user=Depends(get_current_user_async)
):
    """Check if a listener is in user's favorites"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if favorited
        existing = await conn.fetchrow(
            "SELECT favoriter_id FROM user_favorites WHERE favoriter_id = $1 AND favoritee_id = $2",
            user_id, listener_id
        )
        
        # Get listener info
        listener = await conn.fetchrow(
            "SELECT username FROM users WHERE user_id = $1",
            listener_id
        )
        
        if not listener:
            raise HTTPException(status_code=404, detail="Listener not found")
        
        is_favorited = existing is not None
        
        return FavoriteActionResponse(
            success=True,
            message=f"{listener['username'] or 'Listener'} is {'in' if is_favorited else 'not in'} favorites",
            listener_id=listener_id,
            is_favorited=is_favorited
        )


# Blocking related endpoints
@router.post("/block", response_model=BlockActionResponse)
async def block_user(
    data: BlockUserRequest,
    user=Depends(get_current_user_async)
):
    """Block a user"""
    user_id = user["user_id"]
    blocked_id = data.blocked_id
    action_type = data.action_type
    reason = data.reason
    
    # Prevent self-blocking
    if user_id == blocked_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user to be blocked exists
        blocked_user = await conn.fetchrow(
            "SELECT user_id, username FROM users WHERE user_id = $1",
            blocked_id
        )
        
        if not blocked_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already blocked
        existing = await conn.fetchrow(
            "SELECT blocker_id FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2",
            user_id, blocked_id
        )
        
        if existing:
            return BlockActionResponse(
                success=True,
                message=f"Already blocked {blocked_user['username'] or 'this user'}",
                blocked_id=blocked_id,
                action_type=action_type,
                is_blocked=True
            )
        
        # Block the user
        await conn.execute(
            """
            INSERT INTO user_blocks (blocker_id, blocked_id, action_type, reason, created_at)
            VALUES ($1, $2, $3, $4, now())
            """,
            user_id, blocked_id, action_type, reason
        )
        
        return BlockActionResponse(
            success=True,
            message=f"Successfully blocked {blocked_user['username'] or 'user'}",
            blocked_id=blocked_id,
            action_type=action_type,
            is_blocked=True
        )

@router.delete("/block", response_model=BlockActionResponse)
async def unblock_user(
    data: UnblockUserRequest,
    user=Depends(get_current_user_async)
):
    """Unblock a user"""
    user_id = user["user_id"]
    blocked_id = data.blocked_id
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user exists
        blocked_user = await conn.fetchrow(
            "SELECT username FROM users WHERE user_id = $1",
            blocked_id
        )
        
        if not blocked_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if blocked
        existing = await conn.fetchrow(
            "SELECT action_type FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2",
            user_id, blocked_id
        )
        
        if not existing:
            return BlockActionResponse(
                success=True,
                message=f"{blocked_user['username'] or 'User'} was not blocked",
                blocked_id=blocked_id,
                action_type="unblock",
                is_blocked=False
            )
        
        # Unblock the user
        await conn.execute(
            "DELETE FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2",
            user_id, blocked_id
        )
        
        return BlockActionResponse(
            success=True,
            message=f"Successfully unblocked {blocked_user['username'] or 'user'}",
            blocked_id=blocked_id,
            action_type="unblock",
            is_blocked=False
        )

@router.get("/blocked", response_model=BlockedUsersResponse)
async def get_blocked_users(
    page: int = 1,
    per_page: int = 20,
    action_type: Optional[str] = None,
    user=Depends(get_current_user_async)
):
    """Get list of users blocked by current user"""
    user_id = user["user_id"]
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build base query
        base_query = """
            FROM user_blocks ub
            JOIN users u ON ub.blocked_id = u.user_id
            WHERE ub.blocker_id = $1
        """
        params = [user_id]
        param_count = 1
        
        # Add action type filter if specified
        if action_type:
            param_count += 1
            base_query += f" AND ub.action_type = ${param_count}"
            params.append(action_type)
        
        # Get total count
        count_query = f"SELECT COUNT(*) {base_query}"
        total_count = await conn.fetchval(count_query, *params)
        
        # Get blocked users with pagination
        blocked_query = f"""
            SELECT 
                u.user_id,
                u.username,
                u.sex,
                u.bio,
                u.profile_image_url,
                ub.action_type,
                ub.reason,
                ub.created_at as blocked_at
            {base_query}
            ORDER BY ub.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([per_page, offset])
        
        blocked_users = await conn.fetch(blocked_query, *params)
        
        # Format blocked users
        blocked_list = []
        for blocked in blocked_users:
            blocked_list.append(BlockedUser(
                user_id=blocked['user_id'],
                username=blocked['username'],
                sex=blocked['sex'],
                bio=blocked['bio'],
                profile_image_url=blocked['profile_image_url'],
                action_type=blocked['action_type'],
                reason=blocked['reason'],
                blocked_at=blocked['blocked_at']
            ))
        
        has_next = offset + per_page < total_count
        has_previous = page > 1
        
        return BlockedUsersResponse(
            blocked_users=blocked_list,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )

@router.get("/block/check/{user_id}", response_model=BlockActionResponse)
async def check_block_status(
    user_id: int,
    current_user=Depends(get_current_user_async)
):
    """Check if a user is blocked by current user"""
    current_user_id = current_user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if blocked
        existing = await conn.fetchrow(
            "SELECT action_type FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2",
            current_user_id, user_id
        )
        
        # Get user info
        user_info = await conn.fetchrow(
            "SELECT username FROM users WHERE user_id = $1",
            user_id
        )
        
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        is_blocked = existing is not None
        action_type = existing['action_type'] if existing else "none"
        
        return BlockActionResponse(
            success=True,
            message=f"{user_info['username'] or 'User'} is {'blocked' if is_blocked else 'not blocked'}",
            blocked_id=user_id,
            action_type=action_type,
            is_blocked=is_blocked
        )

# Listener Verification endpoints
@router.post("/verification/upload-audio-file", response_model=ListenerVerificationResponse)
async def upload_verification_audio_file(
    audio_file: UploadFile = File(..., description="Audio file to upload"),
    user=Depends(get_current_user_async)
):
    """Upload audio file for listener verification (direct file upload to S3)"""
    user_id = user["user_id"]
    
    # Check if user has listener role
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user has listener role
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
                detail="Only users with listener role can upload verification audio"
            )
        
        # Check if there's already a pending verification
        existing_pending = await conn.fetchrow(
            """
            SELECT sample_id, status FROM listener_verification 
            WHERE listener_id = $1 AND status = 'pending'
            ORDER BY uploaded_at DESC LIMIT 1
            """,
            user_id
        )
        
        if existing_pending:
            raise HTTPException(
                status_code=400,
                detail="You already have a pending verification. Please wait for it to be reviewed."
            )
        
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an audio file (mp3, wav, m4a, etc.)"
            )
        
        # Validate file size (max 10MB)
        file_content = await audio_file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 10MB"
            )
        
        # Check if S3 is configured
        if not s3_client.is_configured():
            raise HTTPException(
                status_code=500,
                detail="File upload service is not configured. Please contact support."
            )
        
        # Upload to S3
        s3_url = await s3_client.upload_audio_file(
            file_content=file_content,
            user_id=user_id,
            content_type=audio_file.content_type
        )
        
        if not s3_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file. Please try again."
            )
        
        # Insert new verification record
        verification = await conn.fetchrow(
            """
            INSERT INTO listener_verification (listener_id, audio_file_url, status, uploaded_at)
            VALUES ($1, $2, 'pending', now())
            RETURNING *
            """,
            user_id, s3_url
        )
        
        return ListenerVerificationResponse(
            sample_id=verification['sample_id'],
            listener_id=verification['listener_id'],
            audio_file_url=verification['audio_file_url'],
            status=ListenerVerificationStatus(verification['status']),
            remarks=verification['remarks'],
            uploaded_at=verification['uploaded_at'],
            reviewed_at=verification['reviewed_at']
        )

@router.post("/verification/upload-audio-url", response_model=ListenerVerificationResponse)
async def upload_verification_audio_url(
    data: UploadAudioRequest,
    user=Depends(get_current_user_async)
):
    """Upload audio sample for listener verification using S3 URL (for external uploads)"""
    user_id = user["user_id"]
    
    # Check if user has listener role
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user has listener role
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
                detail="Only users with listener role can upload verification audio"
            )
        
        # Check if there's already a pending verification
        existing_pending = await conn.fetchrow(
            """
            SELECT sample_id, status FROM listener_verification 
            WHERE listener_id = $1 AND status = 'pending'
            ORDER BY uploaded_at DESC LIMIT 1
            """,
            user_id
        )
        
        if existing_pending:
            raise HTTPException(
                status_code=400,
                detail="You already have a pending verification. Please wait for it to be reviewed."
            )
        
        # Validate S3 URL format
        if not data.audio_file_url.startswith('https://') or 's3' not in data.audio_file_url:
            raise HTTPException(
                status_code=400,
                detail="Invalid S3 URL format"
            )
        
        # Insert new verification record
        verification = await conn.fetchrow(
            """
            INSERT INTO listener_verification (listener_id, audio_file_url, status, uploaded_at)
            VALUES ($1, $2, 'pending', now())
            RETURNING *
            """,
            user_id, data.audio_file_url
        )
        
        return ListenerVerificationResponse(
            sample_id=verification['sample_id'],
            listener_id=verification['listener_id'],
            audio_file_url=verification['audio_file_url'],
            status=ListenerVerificationStatus(verification['status']),
            remarks=verification['remarks'],
            uploaded_at=verification['uploaded_at'],
            reviewed_at=verification['reviewed_at']
        )

@router.get("/verification/status", response_model=VerificationStatusResponse)
async def get_verification_status(user=Depends(get_current_user_async)):
    """Get listener's verification status"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user has listener role
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
                detail="Only users with listener role can check verification status"
            )
        
        # Get latest verification record
        verification = await conn.fetchrow(
            """
            SELECT * FROM listener_verification 
            WHERE listener_id = $1 
            ORDER BY uploaded_at DESC LIMIT 1
            """,
            user_id
        )
        
        if not verification:
            return VerificationStatusResponse(
                is_verified=False,
                verification_status=None,
                last_verification=None,
                message="No verification audio uploaded yet"
            )
        
        verification_response = ListenerVerificationResponse(
            sample_id=verification['sample_id'],
            listener_id=verification['listener_id'],
            audio_file_url=verification['audio_file_url'],
            status=ListenerVerificationStatus(verification['status']),
            remarks=verification['remarks'],
            uploaded_at=verification['uploaded_at'],
            reviewed_at=verification['reviewed_at']
        )
        
        is_verified = verification['status'] == 'approved'
        message = f"Verification status: {verification['status']}"
        
        if verification['status'] == 'rejected' and verification['remarks']:
            message += f" - {verification['remarks']}"
        
        return VerificationStatusResponse(
            is_verified=is_verified,
            verification_status=ListenerVerificationStatus(verification['status']),
            last_verification=verification_response,
            message=message
        )

@router.get("/verification/history", response_model=List[ListenerVerificationResponse])
async def get_verification_history(user=Depends(get_current_user_async)):
    """Get listener's verification history"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user has listener role
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
                detail="Only users with listener role can view verification history"
            )
        
        # Get all verification records
        verifications = await conn.fetch(
            """
            SELECT * FROM listener_verification 
            WHERE listener_id = $1 
            ORDER BY uploaded_at DESC
            """,
            user_id
        )
        
        verification_list = []
        for verification in verifications:
            verification_list.append(ListenerVerificationResponse(
                sample_id=verification['sample_id'],
                listener_id=verification['listener_id'],
                audio_file_url=verification['audio_file_url'],
                status=ListenerVerificationStatus(verification['status']),
                remarks=verification['remarks'],
                uploaded_at=verification['uploaded_at'],
                reviewed_at=verification['reviewed_at']
            ))
        
        return verification_list

# Admin endpoints for verification review
@router.get("/admin/verification/pending", response_model=List[ListenerVerificationResponse])
async def get_pending_verifications(
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """Get all pending verification requests (admin only)"""
    # Note: In production, add admin role checking here
    user_id = user["user_id"]
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get pending verifications with user info
        verifications = await conn.fetch(
            """
            SELECT 
                lv.*,
                u.username,
                u.phone
            FROM listener_verification lv
            JOIN users u ON lv.listener_id = u.user_id
            WHERE lv.status = 'pending'
            ORDER BY lv.uploaded_at ASC
            LIMIT $1 OFFSET $2
            """,
            per_page, offset
        )
        
        verification_list = []
        for verification in verifications:
            verification_list.append(ListenerVerificationResponse(
                sample_id=verification['sample_id'],
                listener_id=verification['listener_id'],
                audio_file_url=verification['audio_file_url'],
                status=ListenerVerificationStatus(verification['status']),
                remarks=verification['remarks'],
                uploaded_at=verification['uploaded_at'],
                reviewed_at=verification['reviewed_at']
            ))
        
        return verification_list

@router.post("/admin/verification/review", response_model=AdminReviewResponse)
async def review_verification(
    data: AdminReviewRequest,
    user=Depends(get_current_user_async)
):
    """Review and approve/reject verification request (admin only)"""
    # Note: In production, add admin role checking here
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if verification exists and is pending
        verification = await conn.fetchrow(
            """
            SELECT * FROM listener_verification 
            WHERE sample_id = $1 AND status = 'pending'
            """,
            data.sample_id
        )
        
        if not verification:
            raise HTTPException(
                status_code=404,
                detail="Verification request not found or already reviewed"
            )
        
        # Update verification status
        updated_verification = await conn.fetchrow(
            """
            UPDATE listener_verification 
            SET status = $1, remarks = $2, reviewed_at = now()
            WHERE sample_id = $3
            RETURNING *
            """,
            data.status.value, data.remarks, data.sample_id
        )
        
        verification_response = ListenerVerificationResponse(
            sample_id=updated_verification['sample_id'],
            listener_id=updated_verification['listener_id'],
            audio_file_url=updated_verification['audio_file_url'],
            status=ListenerVerificationStatus(updated_verification['status']),
            remarks=updated_verification['remarks'],
            uploaded_at=updated_verification['uploaded_at'],
            reviewed_at=updated_verification['reviewed_at']
        )
        
        message = f"Verification {data.status.value} successfully"
        if data.remarks:
            message += f" with remarks: {data.remarks}"
        
        return AdminReviewResponse(
            success=True,
            message=message,
            verification=verification_response
        )

@router.get("/badge/current")
async def get_current_badge(user=Depends(get_current_user_async)):
    """Get current badge for the authenticated listener for today"""
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
    from datetime import date
    today = date.today()
    badge_info = await get_current_listener_badge(user_id, today)
    
    return {
        "listener_id": user_id,
        "username": user_info['username'],
        "current_badge": badge_info['badge'],
        "audio_rate_per_minute": badge_info['audio_rate_per_minute'],
        "video_rate_per_minute": badge_info['video_rate_per_minute'],
        "assigned_date": badge_info['assigned_date'],
        "assigned_at": badge_info['assigned_at']
    }
