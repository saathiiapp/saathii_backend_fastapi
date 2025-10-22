from fastapi import APIRouter, Depends, HTTPException, Header, Query
from api.clients.jwt_handler import decode_jwt
from api.clients.redis_client import redis_client
from api.clients.db import get_db_pool
from api.utils.user_validation import validate_user_active
from api.schemas.verification import VerificationStatusResponse, AdminVerificationListResponse, UnverifiedListenerResponse, VerifiedListenerResponse

router = APIRouter(tags=["Verification"])

async def get_current_user_async(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    # Reject if blacklisted
    user_id = payload.get("user_id")
    jti = payload.get("jti")
    if user_id and jti and await redis_client.get(f"access:{user_id}:{jti}"):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    # Validate user is active
    await validate_user_active(user_id)
    
    return payload

@router.get("/listener/verification/status", response_model=VerificationStatusResponse)
async def get_verification_status(user=Depends(get_current_user_async)):
    """Get listener verification status"""
    user_id = user["user_id"]
    
    # Check if user is a listener
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        listener_role = await conn.fetchrow(
            """
            SELECT role FROM user_roles 
            WHERE user_id = $1 AND role = 'listener'
            """,
            user_id
        )
        if not listener_role:
            raise HTTPException(
                status_code=403, 
                detail="Only users with listener role can access this endpoint"
            )
        
        # Get verification status
        verification = await conn.fetchrow(
            """
            SELECT verification_status, verified_on, verification_message, audio_file_url
            FROM listener_profile 
            WHERE listener_id = $1
            """,
            user_id
        )
        
        if not verification:
            return VerificationStatusResponse(
                verification_status=False,
                verification_message="Listener profile not found. Please complete registration.",
                verified_on=None
            )
        
        return VerificationStatusResponse(
            verification_status=verification["verification_status"],
            verification_message=verification["verification_message"],
            verified_on=verification["verified_on"]
        )


@router.get("/admin/verification/pending", response_model=AdminVerificationListResponse)
async def get_unverified_listeners(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get list of unverified and verified listeners for admin review"""
    
    # Calculate offset for pagination
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get total count of unverified listeners
        total_unverified_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE ur.role = 'listener' 
            AND lp.verification_status = FALSE
            AND u.user_id IN (
                SELECT user_id FROM user_status WHERE is_active = TRUE
            )
            """
        )
        
        # Get total count of verified listeners
        total_verified_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE ur.role = 'listener' 
            AND lp.verification_status = TRUE
            AND u.user_id IN (
                SELECT user_id FROM user_status WHERE is_active = TRUE
            )
            """
        )

        # Get unverified listeners with pagination
        unverified_rows = await conn.fetch(
            """
            SELECT 
                u.user_id,
                u.username,
                u.sex,
                u.bio,
                u.interests,
                u.profile_image_url,
                u.preferred_language,
                u.country,
                lp.verification_status,
                lp.verification_message,
                lp.audio_file_url,
                lp.created_at,
                lp.updated_at
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE ur.role = 'listener' 
            AND lp.verification_status = FALSE
            AND u.user_id IN (
                SELECT user_id FROM user_status WHERE is_active = TRUE
            )
            ORDER BY lp.created_at ASC
            LIMIT $1 OFFSET $2
            """,
            per_page, offset
        )

        # Get verified listeners with pagination
        verified_rows = await conn.fetch(
            """
            SELECT 
                u.user_id,
                u.username,
                u.sex,
                u.bio,
                u.interests,
                u.profile_image_url,
                u.preferred_language,
                u.country,
                lp.verification_status,
                lp.verification_message,
                lp.audio_file_url,
                lp.verified_on,
                lp.created_at,
                lp.updated_at
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN listener_profile lp ON u.user_id = lp.listener_id
            WHERE ur.role = 'listener' 
            AND lp.verification_status = TRUE
            AND u.user_id IN (
                SELECT user_id FROM user_status WHERE is_active = TRUE
            )
            ORDER BY lp.verified_on DESC NULLS LAST
            LIMIT $1 OFFSET $2
            """,
            per_page, offset
        )

        # Convert to response format
        unverified_listeners = []
        for listener in unverified_rows:
            unverified_listeners.append(UnverifiedListenerResponse(
                user_id=listener["user_id"],
                username=listener["username"],
                sex=listener["sex"],
                bio=listener["bio"],
                interests=listener["interests"],
                profile_image_url=listener["profile_image_url"],
                preferred_language=listener["preferred_language"],
                country=listener["country"],
                verification_status=listener["verification_status"],
                verification_message=listener["verification_message"],
                audio_file_url=listener["audio_file_url"],
                created_at=listener["created_at"],
                updated_at=listener["updated_at"]
            ))

        verified_listeners = []
        for listener in verified_rows:
            verified_listeners.append(VerifiedListenerResponse(
                user_id=listener["user_id"],
                username=listener["username"],
                sex=listener["sex"],
                bio=listener["bio"],
                interests=listener["interests"],
                profile_image_url=listener["profile_image_url"],
                preferred_language=listener["preferred_language"],
                country=listener["country"],
                verification_status=listener["verification_status"],
                verification_message=listener["verification_message"],
                audio_file_url=listener["audio_file_url"],
                verified_on=listener["verified_on"],
                created_at=listener["created_at"],
                updated_at=listener["updated_at"]
            ))

        # Calculate pagination info for both lists
        has_next_unverified = (offset + per_page) < total_unverified_count
        has_previous_unverified = page > 1
        has_next_verified = (offset + per_page) < total_verified_count
        has_previous_verified = page > 1
        
        return AdminVerificationListResponse(
            unverified_listeners=unverified_listeners,
            verified_listeners=verified_listeners,
            total_unverified_count=total_unverified_count,
            total_verified_count=total_verified_count,
            page=page,
            per_page=per_page,
            has_next_unverified=has_next_unverified,
            has_previous_unverified=has_previous_unverified,
            has_next_verified=has_next_verified,
            has_previous_verified=has_previous_verified
        )
