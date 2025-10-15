from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime

from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.utils.user_validation import validate_user_active
from api.schemas.favorites import (
    AddFavoriteRequest,
    FavoriteUser,
    FavoritesResponse,
    FavoriteActionResponse,
)


router = APIRouter(tags=["Favorites"])


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


@router.post("/customer/favorites", response_model=FavoriteActionResponse)
async def add_favorite(
    data: AddFavoriteRequest,
    user=Depends(get_current_user_async)
):
    """Add a listener to favorites (customer only)."""
    user_id = user["user_id"]
    listener_id = data.listener_id

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
            WHERE u.user_id = $1 AND ur.role = 'listener'
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


@router.get("/customer/favorites", response_model=FavoritesResponse)
async def get_favorites(
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """Get customer's favorite listeners (customer only)."""
    user_id = user["user_id"]

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        base_query = """
            FROM user_favorites uf
            JOIN users u ON uf.favoritee_id = u.user_id
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE uf.favoriter_id = $1
        """
        params = [user_id]

        count_query = f"SELECT COUNT(*) {base_query}"
        total_count = await conn.fetchval(count_query, *params)

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
            LIMIT $2 OFFSET $3
        """
        params_with_pagination = [*params, per_page, offset]

        favorites = await conn.fetch(favorites_query, *params_with_pagination)

        favorite_list = []
        for fav in favorites:
            is_available = (fav['is_online'] or False) and not (fav['is_busy'] or False)
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

        # Compute online/available counts
        online_count_query = f"""
            SELECT COUNT(*) 
            {base_query}
            AND us.is_online = true
        """
        online_count = await conn.fetchval(online_count_query, *params)

        available_count_query = f"""
            SELECT COUNT(*) 
            {base_query}
            AND us.is_online = true AND us.is_busy = false
        """
        available_count = await conn.fetchval(available_count_query, *params)

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


