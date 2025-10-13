from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List

from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.clients.redis_client import redis_client
from api.utils.realtime import broadcast_user_status_update, get_user_status_for_broadcast
from api.schemas.status import (
    UserStatusResponse,
    UpdateStatusRequest,
    UserPresenceResponse,
)


router = APIRouter(tags=["Status"])


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


@router.get("/users/me/status", response_model=UserStatusResponse)
async def get_my_status(user=Depends(get_current_user_async)):
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
    pool = await get_db_pool()
    async with pool.acquire() as conn:
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

        status_data = await get_user_status_for_broadcast(user["user_id"])
        if status_data:
            await broadcast_user_status_update(user["user_id"], status_data)

        return dict(status)


@router.post("/users/me/heartbeat")
async def heartbeat(user=Depends(get_current_user_async)):
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

        status_data = await get_user_status_for_broadcast(user["user_id"])
        if status_data:
            await broadcast_user_status_update(user["user_id"], status_data)

    return {"message": "Heartbeat received"}


@router.get("/users/{user_id}/presence", response_model=UserPresenceResponse)
async def get_user_presence(user_id: int, user=Depends(get_current_user_async)):
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
    user_ids: str,
    user=Depends(get_current_user_async)
):
    try:
        ids = [int(id.strip()) for id in user_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user IDs format")

    if len(ids) > 50:
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


