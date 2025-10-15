from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional
from api.clients.db import get_db_pool
from api.clients.redis_client import redis_client
from api.clients.jwt_handler import decode_jwt
from api.utils.user_validation import validate_user_active, validate_customer_role
from api.schemas.feed import (
    ListenerFeedResponse,
    ListenerFeedItem,
)


router = APIRouter(tags=["Feed System"])


async def get_current_user_async(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    user_id = payload.get("user_id")
    jti = payload.get("jti")
    if user_id and jti and await redis_client.get(f"access:{user_id}:{jti}"):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    # Validate user is active
    await validate_user_active(user_id)
    
    return payload


async def get_current_customer_user(authorization: str = Header(...)):
    """Get current user and validate they have customer role."""
    user = await get_current_user_async(authorization)
    user_id = user.get("user_id")
    
    # Validate user has customer role
    await validate_customer_role(user_id)
    
    return user


@router.get("/customer/feed/listeners", response_model=ListenerFeedResponse)
async def get_listeners_feed(
    online_only: bool = False,
    available_only: bool = False,
    language: Optional[str] = None,
    interests: Optional[str] = None,
    min_rating: Optional[int] = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_customer_user)
):
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    interest_list = None
    if interests:
        interest_list = [interest.strip() for interest in interests.split(",") if interest.strip()]

    pool = await get_db_pool()
    async with pool.acquire() as conn:
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
                array_agg(ur.role) AS roles,
                us.is_online,
                us.last_seen,
                us.is_busy,
                us.wait_time,
                (us.is_online AND NOT us.is_busy) AS is_available,
                lp.listener_allowed_call_type,
                lp.listener_audio_call_enable,
                lp.listener_video_call_enable
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE u.user_id != $1  -- Exclude current user
            AND ub.blocked_id IS NULL  -- Exclude users current user blocked
        """

        conditions = ["u.user_id != $1", "ub.blocked_id IS NULL"]
        params = [user["user_id"]]
        param_count = 1

        # Must be active users with listener role and verified
        conditions.append("us.is_active = true")  # User account must be active
        conditions.append("EXISTS (SELECT 1 FROM user_roles r WHERE r.user_id = u.user_id AND r.role = 'listener')")
        conditions.append("lp.verification_status = true")

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

        # Also exclude users who have blocked the current user
        conditions.append("NOT EXISTS (SELECT 1 FROM user_blocks ub2 WHERE ub2.blocker_id = u.user_id AND ub2.blocked_id = $1)")

        if len(conditions) > 1:
            base_query += " AND " + " AND ".join(conditions[1:])

        base_query += """
            GROUP BY u.user_id, us.is_online, us.last_seen, us.is_busy, us.wait_time, 
                     lp.listener_allowed_call_type, lp.listener_audio_call_enable, lp.listener_video_call_enable
            ORDER BY 
                us.is_online DESC,
                us.is_busy ASC,
                u.rating DESC NULLS LAST,
                us.last_seen DESC
        """

        count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE {' AND '.join(conditions)}
        """
        total_count = await conn.fetchval(count_query, *params)

        online_count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE {' AND '.join(conditions)} AND us.is_online = true
        """
        online_count = await conn.fetchval(online_count_query, *params)

        available_count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN user_blocks ub ON u.user_id = ub.blocked_id AND ub.blocker_id = $1
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE {' AND '.join(conditions)} AND us.is_online = true AND us.is_busy = false
        """
        available_count = await conn.fetchval(available_count_query, *params)

        paginated_query = base_query + f" LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([per_page, offset])
        listeners_data = await conn.fetch(paginated_query, *params)

        listeners = []
        for row in listeners_data:
            listeners.append(ListenerFeedItem(
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
                is_available=row["is_available"],
                listener_allowed_call_type=row["listener_allowed_call_type"],
                listener_audio_call_enable=row["listener_audio_call_enable"],
                listener_video_call_enable=row["listener_video_call_enable"],
            ))

        has_next = offset + per_page < total_count
        has_previous = page > 1

        return ListenerFeedResponse(
            items=listeners,
            total_count=total_count,
            online_count=online_count,
            available_count=available_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )


@router.get("/both/feed/stats")
async def get_feed_stats(user=Depends(get_current_user_async)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        listeners_total = await conn.fetchval(
            """
            SELECT COUNT(*) FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE u.user_id != $1
              AND us.is_active = true
              AND EXISTS (
                SELECT 1 FROM user_roles r WHERE r.user_id = u.user_id AND r.role = 'listener'
              )
              AND lp.verification_status = true
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub1 WHERE ub1.blocker_id = $1 AND ub1.blocked_id = u.user_id
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub2 WHERE ub2.blocker_id = u.user_id AND ub2.blocked_id = $1
              )
            """,
            user["user_id"],
        )

        listeners_online = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE u.user_id != $1
              AND us.is_active = true
              AND us.is_online = true
              AND EXISTS (
                SELECT 1 FROM user_roles r WHERE r.user_id = u.user_id AND r.role = 'listener'
              )
              AND lp.verification_status = true
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub1 WHERE ub1.blocker_id = $1 AND ub1.blocked_id = u.user_id
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub2 WHERE ub2.blocker_id = u.user_id AND ub2.blocked_id = $1
              )
            """,
            user["user_id"],
        )

        listeners_available = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE u.user_id != $1
              AND us.is_active = true
              AND us.is_online = true AND us.is_busy = false
              AND EXISTS (
                SELECT 1 FROM user_roles r WHERE r.user_id = u.user_id AND r.role = 'listener'
              )
              AND lp.verification_status = true
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub1 WHERE ub1.blocker_id = $1 AND ub1.blocked_id = u.user_id
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub2 WHERE ub2.blocker_id = u.user_id AND ub2.blocked_id = $1
              )
            """,
            user["user_id"],
        )

        users_total = await conn.fetchval(
            """
            SELECT COUNT(*) FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id != $1
              AND us.is_active = true
              AND NOT EXISTS (
                SELECT 1 FROM user_roles r WHERE r.user_id = u.user_id AND r.role = 'listener'
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub1 WHERE ub1.blocker_id = $1 AND ub1.blocked_id = u.user_id
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub2 WHERE ub2.blocker_id = u.user_id AND ub2.blocked_id = $1
              )
            """,
            user["user_id"],
        )

        users_online = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id != $1
              AND us.is_active = true
              AND us.is_online = true
              AND NOT EXISTS (
                SELECT 1 FROM user_roles r WHERE r.user_id = u.user_id AND r.role = 'listener'
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub1 WHERE ub1.blocker_id = $1 AND ub1.blocked_id = u.user_id
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub2 WHERE ub2.blocker_id = u.user_id AND ub2.blocked_id = $1
              )
            """,
            user["user_id"],
        )

        users_available = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id != $1
              AND us.is_active = true
              AND us.is_online = true AND us.is_busy = false
              AND NOT EXISTS (
                SELECT 1 FROM user_roles r WHERE r.user_id = u.user_id AND r.role = 'listener'
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub1 WHERE ub1.blocker_id = $1 AND ub1.blocked_id = u.user_id
              )
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks ub2 WHERE ub2.blocker_id = u.user_id AND ub2.blocked_id = $1
              )
            """,
            user["user_id"],
        )

        return {
            "listeners": {
                "total": listeners_total,
                "online": listeners_online,
                "available": listeners_available,
                "busy": listeners_online - listeners_available,
            },
            "users": {
                "total": users_total,
                "online": users_online,
                "available": users_available,
                "busy": users_online - users_available,
            },
        }

