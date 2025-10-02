from fastapi import APIRouter, Depends, HTTPException, Header
from app.clients.redis_client import redis_client
from app.clients.db import get_db_pool
from app.clients.jwt_handler import decode_jwt
from app.schemas.user import UserResponse, EditUserRequest

router = APIRouter()


async def get_current_user_async(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    # Reject if blacklisted
    if await redis_client.get(f"bl:{token}"):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
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
