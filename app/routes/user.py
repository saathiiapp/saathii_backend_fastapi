from fastapi import APIRouter, Depends, HTTPException, Header
from app.clients.db import get_db_pool
from app.clients.jwt_handler import decode_jwt
from app.schemas.user import UserResponse, EditUserRequest

router = APIRouter()


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


@router.get("/users/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id=$1", user["user_id"]
        )
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(db_user)


@router.put("/users/me", response_model=UserResponse)
async def edit_me(data: EditUserRequest, user=Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        db_user = await conn.fetchrow(
            """
            UPDATE users
            SET username=COALESCE($2, username),
                bio=COALESCE($3, bio),
                interests=COALESCE($4, interests),
                profile_photo=COALESCE($5, profile_photo),
                preferred_language=COALESCE($6, preferred_language),
                updated_at=now()
            WHERE user_id=$1
            RETURNING *;
        """,
            user["user_id"],
            data.username,
            data.bio,
            data.interests,
            data.profile_photo,
            data.preferred_language,
        )
        return dict(db_user)
