from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.schemas.block import (
    BlockUserRequest,
    UnblockUserRequest,
    BlockActionResponse,
    BlockedUser,
    BlockedUsersResponse,
)


router = APIRouter(tags=["Blocking"])


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


@router.post("/block", response_model=BlockActionResponse)
async def block_user(
    data: BlockUserRequest,
    user=Depends(get_current_user_async)
):
    """Block a user (customer or listener)."""
    user_id = user["user_id"]
    blocked_id = data.blocked_id
    action_type = data.action_type
    reason = data.reason

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
    """Unblock a user (customer or listener)."""
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
    """Get list of users blocked by current user (customer or listener)."""
    user_id = user["user_id"]

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        base_query = """
            FROM user_blocks ub
            JOIN users u ON ub.blocked_id = u.user_id
            WHERE ub.blocker_id = $1
        """
        params = [user_id]
        param_count = 1

        if action_type:
            param_count += 1
            base_query += f" AND ub.action_type = ${param_count}"
            params.append(action_type)

        count_query = f"SELECT COUNT(*) {base_query}"
        total_count = await conn.fetchval(count_query, *params)

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


