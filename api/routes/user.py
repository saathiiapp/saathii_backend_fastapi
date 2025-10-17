from fastapi import APIRouter, Depends, HTTPException, Header, Body
from typing import List, Optional
import time
from datetime import datetime
from api.clients.redis_client import redis_client
from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.utils.user_validation import validate_user_active, enforce_listener_verified, validate_customer_or_verified_listener
from api.schemas.user import (
    UserResponse, 
    EditUserRequest,
    DeleteUserRequest,
    DeleteUserResponse
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
    
    # Validate user is active
    await validate_user_active(user_id)
    
    return payload


@router.get("/both/users/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user_async)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow(
            """
            SELECT 
                u.*,
                array_agg(ur.role) AS roles,
                us.is_active
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id = $1
            GROUP BY u.user_id, us.is_active
            """,
            user["user_id"],
        )
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(db_user)


@router.put("/both/users/me", response_model=UserResponse)
async def edit_me(data: EditUserRequest, user=Depends(get_current_user_async)):
    # Validate user role: customers (active), listeners (active + verified)
    user_role = await validate_customer_or_verified_listener(user["user_id"])
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


@router.delete("/both/users/me", response_model=DeleteUserResponse)
async def delete_me(
    data: Optional[DeleteUserRequest] = Body(default=None), 
    authorization: str = Header(...), 
    user=Depends(get_current_user_async)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]

    # Validate user role: customers (active), listeners (active + verified)
    user_role = await validate_customer_or_verified_listener(user["user_id"])

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get user details before deletion
        user_details = await conn.fetchrow(
            "SELECT username, phone FROM users WHERE user_id = $1",
            user["user_id"]
        )
        
        if not user_details:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Store delete request with reason and user details before deleting user
        reason = data.reason if data else None
        print(f"DEBUG: user_id={user['user_id']}, username={user_details['username']}, phone={user_details['phone']}, reason={reason}, user_role={user_role}")
        request_id = await conn.fetchval(
            """
            INSERT INTO user_delete_requests (user_id, username, phone, reason, user_role, deleted_at, created_at)
            VALUES ($1, $2, $3, $4, $5, now(), now())
            RETURNING request_id
            """,
            user["user_id"],
            user_details["username"],
            user_details["phone"],
            reason,
            user_role
        )
        print(f"DEBUG: Inserted into user_delete_requests with request_id={request_id}")

        # Remove dependent rows first to satisfy FK constraints
        # Remove wallet transactions and wallet explicitly (defensive even if CASCADE exists)
        wallet_id = await conn.fetchval("SELECT wallet_id FROM user_wallets WHERE user_id=$1", user["user_id"])
        if wallet_id:
            await conn.execute("DELETE FROM user_transactions WHERE wallet_id=$1", wallet_id)
        await conn.execute("DELETE FROM user_wallets WHERE user_id=$1", user["user_id"])
        
        # Note: All dependent data (user_roles, user_status, listener_profile, 
        # listener_payout, listener_badges, user_calls, etc.) will be automatically 
        # deleted due to CASCADE DELETE constraints when the user is deleted.
        # This applies to both customers and listeners.
        
        await conn.execute("DELETE FROM users WHERE user_id=$1", user["user_id"])
        print(f"DEBUG: User {user['user_id']} deleted successfully, request_id={request_id}")

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

    return DeleteUserResponse(
        message="User deleted successfully",
        request_id=request_id
    )
    