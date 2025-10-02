from fastapi import APIRouter, HTTPException
from app.clients.redis_client import redis_client
from app.clients.jwt_handler import create_jwt
from app.clients.db import get_db_pool
from app.schemas.auth import OTPRequest, VerifyRequest, TokenResponse
from app.utils.otp import generate_otp, send_otp_message

router = APIRouter()


@router.post("/auth/request_otp")
async def request_otp(data: OTPRequest):
    otp = generate_otp()
    await redis_client.setex(f"otp:{data.phone}", 300, otp)
    send_otp_message(data.phone, otp)
    return {"message": "OTP sent"}


@router.post("/auth/verify", response_model=TokenResponse)
async def verify_otp(data: VerifyRequest):
    stored_otp = await redis_client.get(f"otp:{data.phone}")
    if not stored_otp or stored_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await redis_client.delete(f"otp:{data.phone}")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE phone=$1", data.phone)

        if not user:
            if not data.username or not data.dob:
                raise HTTPException(
                    status_code=400, detail="Missing registration fields"
                )

            user = await conn.fetchrow(
                """
                INSERT INTO users 
                (username, phone, sex, dob, bio, interests, preferred_language, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                RETURNING *;
                """,
                data.username,
                data.phone,
                data.sex,
                data.dob,
                data.bio,
                data.interests,
                data.preferred_language,
            )

            await conn.execute(
                "INSERT INTO user_roles (user_id, role) VALUES ($1,$2)",
                user["user_id"],
                data.role,
            )

        token = create_jwt({"user_id": user["user_id"], "phone": user["phone"]})
        return TokenResponse(token=token)
