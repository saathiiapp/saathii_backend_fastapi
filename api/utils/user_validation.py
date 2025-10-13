from fastapi import HTTPException
from api.clients.db import get_db_pool


async def validate_user_active(user_id: int) -> bool:
    """
    Validate if a user is active. Raises HTTPException if user is not active.
    Returns True if user is active.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_status = await conn.fetchrow(
            "SELECT is_active FROM user_status WHERE user_id = $1",
            user_id
        )
        
        if not user_status:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user_status["is_active"]:
            raise HTTPException(status_code=403, detail="User account is inactive")
        
        return True
