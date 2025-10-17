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


async def enforce_listener_verified(user_id: int) -> None:
    """Require user to have listener role AND be verified to proceed."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        has_listener_role = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM user_roles 
                WHERE user_id = $1 AND role = 'listener'
            )
            """,
            user_id,
        )
        
        if not has_listener_role:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Listener role required to access this endpoint."
            )
        
        is_verified = await conn.fetchval(
            "SELECT verification_status FROM listener_profile WHERE listener_id = $1",
            user_id,
        )
        if not is_verified:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Listener verification is pending. Please wait for admin approval.",
            )


async def validate_customer_role(user_id: int) -> bool:
    """
    Validate if a user has the customer role. Raises HTTPException if user doesn't have customer role.
    Returns True if user has customer role.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        has_customer_role = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM user_roles 
                WHERE user_id = $1 AND role = 'customer'
            )
            """,
            user_id,
        )
        
        if not has_customer_role:
            raise HTTPException(
                status_code=403, 
                detail="Access denied. Customer role required to access this endpoint."
            )
        
        return True


async def validate_customer_or_verified_listener(user_id: int) -> str:
    """
    Validate user for /both/ endpoints:
    - Customers: must be active
    - Listeners: must be active AND verified
    
    Returns the user's role ('customer' or 'listener')
    Raises HTTPException if validation fails
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get user roles
        user_roles = await conn.fetchval(
            "SELECT array_agg(role) FROM user_roles WHERE user_id = $1", 
            user_id
        )
        
        if not user_roles:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is active
        user_status = await conn.fetchrow(
            "SELECT is_active FROM user_status WHERE user_id = $1",
            user_id
        )
        
        if not user_status or not user_status["is_active"]:
            raise HTTPException(status_code=403, detail="User account is inactive")
        
        # Determine primary role and validate accordingly
        if "listener" in user_roles:
            # For listeners, check verification status
            is_verified = await conn.fetchval(
                "SELECT verification_status FROM listener_profile WHERE listener_id = $1",
                user_id,
            )
            if not is_verified:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied. Listener verification is pending. Please wait for admin approval.",
                )
            return "listener"
        elif "customer" in user_roles:
            # For customers, just need to be active (already checked above)
            return "customer"
        else:
            raise HTTPException(
                status_code=403,
                detail="Access denied. User must have either customer or listener role."
            )
