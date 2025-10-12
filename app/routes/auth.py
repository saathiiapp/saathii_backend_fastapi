from fastapi import APIRouter, HTTPException, Header
import time
from app.clients.redis_client import redis_client
from app.clients.jwt_handler import (
    create_access_token,
    create_refresh_token,
    create_registration_token,
    decode_jwt,
)
from app.clients.db import get_db_pool
from app.schemas.auth import (
    OTPRequest,
    VerifyRequest,
    TokenPairResponse,
    RefreshRequest,
    VerifyResponse,
    RegisterRequest,
)
from app.utils.otp import generate_otp, send_otp_message

router = APIRouter(tags=["Authentication"])


@router.post("/auth/request_otp")
async def request_otp(data: OTPRequest):
    # Simple rate limiting: 5 requests per 15 minutes per phone
    rl_key = f"otp_rl:{data.phone}"
    count = await redis_client.incr(rl_key)
    if count == 1:
        await redis_client.expire(rl_key, 900)
    if count > 5:
        raise HTTPException(status_code=429, detail="Too many OTP requests. Please try later.")

    otp = generate_otp()
    await redis_client.setex(f"otp:{data.phone}", 300, otp)
    send_otp_message(data.phone, otp)
    return {"message": "OTP sent"}


@router.post("/auth/resend_otp")
async def resend_otp(data: OTPRequest):
    # Short throttle: allow one resend every 60 seconds per phone
    throttle_key = f"otp_resend:{data.phone}"
    if await redis_client.get(throttle_key):
        raise HTTPException(status_code=429, detail="Please wait before requesting another OTP")
    await redis_client.setex(throttle_key, 60, "1")

    otp_key = f"otp:{data.phone}"
    current_otp = await redis_client.get(otp_key)
    if current_otp:
        # Re-send the same OTP without changing TTL
        send_otp_message(data.phone, current_otp)
        return {"message": "OTP re-sent"}

    # No active OTP; generate a new one
    otp = generate_otp()
    await redis_client.setex(otp_key, 300, otp)
    send_otp_message(data.phone, otp)
    return {"message": "OTP sent"}


@router.post("/auth/verify", response_model=VerifyResponse)
async def verify_otp(data: VerifyRequest):
    stored_otp = await redis_client.get(f"otp:{data.phone}")
    if not stored_otp or stored_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await redis_client.delete(f"otp:{data.phone}")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE phone=$1", data.phone)

        if not user:
            # Issue a short-lived registration token to allow client to call /auth/register
            reg_token = create_registration_token({"phone": data.phone})
            return VerifyResponse(status="needs_registration", registration_token=reg_token)

        # Set user online when they log in
        await conn.execute(
            """
            UPDATE user_status 
            SET is_online = TRUE, last_seen = now(), updated_at = now()
            WHERE user_id = $1
            """,
            user["user_id"]
        )

        subject = {"user_id": user["user_id"], "phone": user["phone"]}
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)
        refresh_payload = decode_jwt(refresh_token)
        if not refresh_payload or not refresh_payload.get("jti"):
            raise HTTPException(status_code=500, detail="Failed to issue refresh token")
        refresh_ttl = int(refresh_payload["exp"] - time.time())
        await redis_client.setex(f"refresh:{user['user_id']}:{refresh_payload['jti']}", refresh_ttl, "1")
        return VerifyResponse(status="registered", access_token=access_token, refresh_token=refresh_token)


@router.post("/auth/register", response_model=TokenPairResponse)
async def register_user(data: RegisterRequest):
    reg = decode_jwt(data.registration_token)
    if not reg or reg.get("type") != "registration":
        raise HTTPException(status_code=401, detail="Invalid registration token")
    phone = reg.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Invalid registration payload")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # prevent duplicate users for same phone
        existing = await conn.fetchrow("SELECT * FROM users WHERE phone=$1", phone)
        if existing:
            raise HTTPException(status_code=409, detail="User already exists")

        user = await conn.fetchrow(
            """
            INSERT INTO users 
            (username, phone, sex, dob, bio, interests, preferred_language, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, now())
            RETURNING *;
            """,
            data.username,
            phone,
            data.sex,
            data.dob,
            data.bio,
            data.interests,
            data.preferred_language,
        )

        if data.role:
            await conn.execute(
                "INSERT INTO user_roles (user_id, role) VALUES ($1,$2)",
                user["user_id"],
                data.role,
            )

        # Create user status record (user starts online after registration)
        await conn.execute(
            """
            INSERT INTO user_status (user_id, is_online, last_seen, is_busy, updated_at, created_at)
            VALUES ($1, $2, $3, $4, now(), now())
            """,
            user["user_id"],
            True,  # is_online - user is online after registration
            "now()",  # last_seen
            False,  # is_busy
        )

    subject = {"user_id": user["user_id"], "phone": user["phone"]}
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)
    refresh_payload = decode_jwt(refresh_token)
    if not refresh_payload or not refresh_payload.get("jti"):
        raise HTTPException(status_code=500, detail="Failed to issue refresh token")
    refresh_ttl = int(refresh_payload["exp"] - time.time())
    await redis_client.setex(f"refresh:{user['user_id']}:{refresh_payload['jti']}", refresh_ttl, "1")
    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/auth/refresh", response_model=TokenPairResponse)
async def refresh_tokens(data: RefreshRequest):
    payload = decode_jwt(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("user_id")
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not user_id or not jti or not exp:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")
    # must exist and then rotate (delete old, issue new)
    key = f"refresh:{user_id}:{jti}"
    exists = await redis_client.get(key)
    if not exists:
        raise HTTPException(status_code=401, detail="Refresh token revoked or reused")
    # invalidate old refresh token to enforce rotation
    await redis_client.delete(key)

    subject = {"user_id": user_id, "phone": payload.get("phone")}
    new_access = create_access_token(subject)
    new_refresh = create_refresh_token(subject)
    new_payload = decode_jwt(new_refresh)
    if not new_payload or not new_payload.get("jti"):
        raise HTTPException(status_code=500, detail="Failed to rotate refresh token")
    new_ttl = int(new_payload["exp"] - time.time())
    await redis_client.setex(f"refresh:{user_id}:{new_payload['jti']}", new_ttl, "1")
    return TokenPairResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/auth/logout")
async def logout(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]
    payload = decode_jwt(token)

    if not payload:
        # Token already invalid/expired
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    exp = payload.get("exp")
    if not exp:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    ttl_seconds = int(exp - time.time())
    if ttl_seconds <= 0:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Blacklist access token by jti and revoke all active refresh tokens for the user
    user_id = payload.get('user_id')
    jti = payload.get('jti')
    if user_id and jti:
        await redis_client.setex(f"access:{user_id}:{jti}", ttl_seconds, "1")
    # revoke any refresh tokens for this user by scanning keys
    # Note: if Redis is large, consider tracking a user session version instead
    pattern = f"refresh:{user_id}:*"
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)
    
    # Set user offline when they log out
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE user_status 
            SET is_online = FALSE, last_seen = now(), updated_at = now()
            WHERE user_id = $1
            """,
            user_id
        )
    
    return {"message": "Logged out"}
