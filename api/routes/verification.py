from fastapi import APIRouter, Depends, HTTPException, Header
from api.clients.jwt_handler import decode_jwt
from api.clients.redis_client import redis_client
from api.clients.db import get_db_pool
from api.utils.user_validation import validate_user_active
from api.schemas.verification import VerificationStatusResponse

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
