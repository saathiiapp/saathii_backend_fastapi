from fastapi import APIRouter, Depends, HTTPException, Header, Body, Query
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
    DeleteUserResponse,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserStatusUpdateRequest,
    AdminUserStatusUpdateResponse
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


# Admin User Management Routes (Customers & Listeners)
@router.get("/admin/users", response_model=AdminUserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role (customer, listener)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by username or phone"),
    sort_by: str = Query("created_at", description="Sort by field (created_at, updated_at, user_id, username)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)")
):
    """
    Get all users (customers and listeners) for admin with pagination and filters.
    
    This endpoint provides comprehensive filtering and sorting options for administrators
    to manage both customers and listeners. No authentication required.
    
    Filters available:
    - role: Filter by user role (customer, listener)
    - is_active: Filter by active status (true/false)
    - search: Search by username or phone number (partial match)
    
    Sorting options:
    - sort_by: created_at, updated_at, user_id, username
    - sort_order: asc, desc
    """
    offset = (page - 1) * per_page
    
    # Validate sort parameters
    valid_sort_fields = ["created_at", "updated_at", "user_id", "username"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Must be one of: {valid_sort_fields}")
    
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Must be 'asc' or 'desc'")
    
    if role and role not in ["customer", "listener"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'customer' or 'listener'")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build WHERE clause
        where_conditions = []
        params = []
        param_count = 0
        
        if role:
            param_count += 1
            where_conditions.append(f"ur.role = ${param_count}")
            params.append(role)
        
        if is_active is not None:
            param_count += 1
            where_conditions.append(f"us.is_active = ${param_count}")
            params.append(is_active)
        
        if search:
            param_count += 1
            where_conditions.append(f"(u.username ILIKE ${param_count} OR u.phone ILIKE ${param_count})")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN user_status us ON u.user_id = us.user_id
            WHERE {where_clause}
        """
        total_count = await conn.fetchval(count_query, *params)
        
        # Get users with pagination
        param_count += 1
        offset_param = param_count
        params.append(offset)
        
        param_count += 1
        limit_param = param_count
        params.append(per_page)
        
        users_query = f"""
            SELECT 
                u.user_id,
                u.username,
                u.phone,
                u.sex,
                u.dob,
                u.bio,
                u.interests,
                u.profile_image_url,
                u.preferred_language,
                u.rating,
                u.country,
                array_agg(ur.role) as roles,
                us.is_active,
                us.is_online,
                us.last_seen,
                lp.verification_status as is_verified,
                u.created_at,
                u.updated_at
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN user_status us ON u.user_id = us.user_id
            LEFT JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE {where_clause}
            GROUP BY u.user_id, us.is_active, us.is_online, us.last_seen, lp.verification_status, u.created_at, u.updated_at
            ORDER BY u.{sort_by} {sort_order.upper()}
            OFFSET ${offset_param} LIMIT ${limit_param}
        """
        
        users_rows = await conn.fetch(users_query, *params)
        
        # Convert to response format
        users = []
        for row in users_rows:
            users.append(AdminUserResponse(
                user_id=row["user_id"],
                username=row["username"],
                phone=row["phone"],
                sex=row["sex"],
                dob=row["dob"],
                bio=row["bio"],
                interests=row["interests"],
                profile_image_url=row["profile_image_url"],
                preferred_language=row["preferred_language"],
                rating=row["rating"],
                country=row["country"],
                roles=row["roles"],
                is_active=row["is_active"],
                is_online=row["is_online"],
                last_seen=row["last_seen"],
                is_verified=row["is_verified"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            ))
        
        # Calculate pagination info
        has_next = offset + per_page < total_count
        has_previous = page > 1
        
        return AdminUserListResponse(
            users=users,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )


@router.put("/admin/users/status", response_model=AdminUserStatusUpdateResponse)
async def update_user_status(request: AdminUserStatusUpdateRequest):
    """
    Update user active/inactive status for both customers and listeners.
    
    This endpoint allows administrators to activate or deactivate user accounts.
    No authentication required.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user exists and get their roles
        user_check = await conn.fetchrow(
            """
            SELECT u.user_id, u.username, us.is_active, array_agg(ur.role) as roles
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN user_status us ON u.user_id = us.user_id
            WHERE u.user_id = $1
            GROUP BY u.user_id, u.username, us.is_active
            """,
            request.user_id
        )
        
        if not user_check:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update the status
        await conn.execute(
            """
            UPDATE user_status 
            SET is_active = $2, updated_at = now()
            WHERE user_id = $1
            """,
            request.user_id,
            request.is_active
        )
        
        status_text = "activated" if request.is_active else "deactivated"
        username = user_check["username"] or f"User {request.user_id}"
        roles = user_check["roles"]
        
        # Determine user type for response
        if "customer" in roles and "listener" in roles:
            user_type = "both"
            type_text = "User (Customer & Listener)"
        elif "customer" in roles:
            user_type = "customer"
            type_text = "Customer"
        elif "listener" in roles:
            user_type = "listener"
            type_text = "Listener"
        else:
            user_type = "unknown"
            type_text = "User"
        
        return AdminUserStatusUpdateResponse(
            success=True,
            message=f"{type_text} {username} has been {status_text} successfully",
            user_id=request.user_id,
            is_active=request.is_active,
            user_type=user_type
        )
    