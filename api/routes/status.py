from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List

from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.clients.redis_client import redis_client
from api.utils.user_validation import validate_user_active
"""Realtime broadcasting removed."""
from api.schemas.status import (
    UserStatusResponse,
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
    
    # Validate user is active
    await validate_user_active(user_id)
    
    return payload


@router.get("/both/status/me", response_model=UserStatusResponse)
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


@router.post("/both/status/heartbeat")
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

    return {"message": "Heartbeat received"}
