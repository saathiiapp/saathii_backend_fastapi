from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional
import time
import asyncio
from datetime import datetime, timedelta
from api.clients.redis_client import redis_client
from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.utils.badge_manager import get_listener_earning_rate
from api.schemas.call import (
    StartCallRequest,
    StartCallResponse,
    EndCallRequest,
    EndCallResponse,
    CallInfo,
    CallHistoryResponse,
    CallType,
    CallStatus,
    DEFAULT_CALL_RATES
)

router = APIRouter(tags=["Call Management"])

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
    return payload

async def get_user_coin_balance(user_id: int) -> int:
    """Get user's current coin balance"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT balance_coins FROM user_wallets WHERE user_id = $1",
            user_id
        )
        return result or 0

async def check_user_availability(user_id: int) -> bool:
    """Check if user is available for calls (not busy)"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user has any ongoing calls
        ongoing_calls = await conn.fetchval(
            "SELECT COUNT(*) FROM user_calls WHERE (user_id = $1 OR listener_id = $1) AND status = 'ongoing'",
            user_id
        )
        return ongoing_calls == 0

# API ENDPOINTS ONLY

@router.post("/customer/calls/start", response_model=StartCallResponse)
async def start_call(data: StartCallRequest, user=Depends(get_current_user_async)):
    """Start a new call with a listener"""
    user_id = user["user_id"]
    
    # Validate listener exists and is available
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Enforce that only customers can start calls
        has_customer_role = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM user_roles 
                WHERE user_id = $1 AND role = 'customer' AND active = true
            )
            """,
            user_id,
        )
        if not has_customer_role:
            raise HTTPException(status_code=403, detail="Only customers can start calls")

        listener = await conn.fetchrow(
            "SELECT user_id, username FROM users WHERE user_id = $1",
            data.listener_id
        )
        if not listener:
            raise HTTPException(status_code=404, detail="Listener not found")
        
        # Check if listener is available
        if not await check_user_availability(data.listener_id):
            raise HTTPException(status_code=409, detail="Listener is currently busy")
        
        # Check if caller is available
        if not await check_user_availability(user_id):
            raise HTTPException(status_code=409, detail="You are already on a call")
        
        # Ensure user has a wallet
        await conn.execute(
            """
            INSERT INTO user_wallets (user_id, balance_coins, created_at)
            VALUES ($1, 0, now())
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id
        )
        
        # Get user's current coin balance
        current_balance = await get_user_coin_balance(user_id)
        
        # Get rate per minute
        rate_per_minute = DEFAULT_CALL_RATES[data.call_type]["rate_per_minute"]
        
        if current_balance < rate_per_minute:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient coins. Required: {rate_per_minute}, Available: {current_balance}"
            )
        
        # Calculate maximum call duration based on available coins
        max_duration_minutes = current_balance // rate_per_minute
        
        # Reserve coins for the first minute
        await update_user_coin_balance(user_id, rate_per_minute, "subtract", "spend")
        
        # Create call record
        call = await conn.fetchrow(
            """
            INSERT INTO user_calls 
            (user_id, listener_id, call_type, status, coins_spent, listener_money_earned)
            VALUES ($1, $2, $3, 'ongoing', $4, 0)
            RETURNING call_id, coins_spent
            """,
            user_id, data.listener_id, data.call_type.value, rate_per_minute
        )
        
        # Set both users as busy simultaneously
        wait_time = max_duration_minutes  # Set wait time to max call duration
        await update_both_users_presence(user_id, data.listener_id, True, wait_time)
        
        # Store call info in Redis for real-time tracking
        call_key = f"call:{call['call_id']}"
        await redis_client.hset(call_key, mapping={
            "user_id": str(user_id),
            "listener_id": str(data.listener_id),
            "call_type": data.call_type.value,
            "start_time": str(int(time.time())),
            "coins_spent": str(rate_per_minute)
        })
        await redis_client.expire(call_key, 7200)  # 2 hours expiry
        
        return StartCallResponse(
            call_id=call['call_id'],
            message="Call started successfully",
            call_duration=max_duration_minutes,
            remaining_coins=await get_user_coin_balance(user_id),
            call_type=data.call_type,
            listener_id=data.listener_id,
            status=CallStatus.ONGOING
        )

@router.post("/both/calls/end", response_model=EndCallResponse)
async def end_call(data: EndCallRequest, user=Depends(get_current_user_async)):
    """End an ongoing call"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get call details
        call = await conn.fetchrow(
            """
            SELECT * FROM user_calls 
            WHERE call_id = $1 AND (user_id = $2 OR listener_id = $2) AND status = 'ongoing'
            """,
            data.call_id, user_id
        )
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found or already ended")
        
        # Calculate final duration
        start_time = call['start_time']
        end_time = datetime.utcnow()
        duration_seconds = int((end_time - start_time).total_seconds())
        duration_minutes = max(1, duration_seconds // 60)  # Minimum 1 minute
        
        # With per-minute deduction, coins are already deducted every minute
        # So we just use the current coins_spent value
        total_coins_spent = call['coins_spent']
        
        # Calculate listener earnings based on actual duration and coins spent
        call_type = CallType(call['call_type'])
        rate_per_minute = DEFAULT_CALL_RATES[call_type]["rate_per_minute"]
        actual_duration_paid = total_coins_spent // rate_per_minute
        listener_rupees_per_minute = await get_listener_earning_rate(call['listener_id'], call_type.value)
        listener_earnings = int(listener_rupees_per_minute * actual_duration_paid)
        
        # Update call record
        await conn.execute(
            """
            UPDATE user_calls 
            SET end_time = $1, duration_seconds = $2, duration_minutes = $3,
                listener_money_earned = $4, status = $5, updated_at = now()
            WHERE call_id = $6
            """,
            end_time, duration_seconds, duration_minutes, 
            listener_earnings, data.reason or "completed", data.call_id
        )
        
        # Add earnings to listener
        await update_user_coin_balance(call['listener_id'], listener_earnings, "add", "earn")
        
        # Set both users as not busy
        await update_both_users_presence(call['user_id'], call['listener_id'], False)
        
        # Remove from Redis
        await redis_client.delete(f"call:{data.call_id}")
        
        return EndCallResponse(
            call_id=data.call_id,
            message="Call ended successfully",
            duration_seconds=duration_seconds,
            duration_minutes=duration_minutes,
            coins_spent=total_coins_spent,
            listener_money_earned=listener_earnings,
            status=CallStatus.COMPLETED if data.reason != "dropped" else CallStatus.DROPPED
        )

@router.get("/both/calls/history", response_model=CallHistoryResponse)
async def get_call_history(
    page: int = 1,
    per_page: int = 20,
    call_type: str = None,
    status: str = None,
    user=Depends(get_current_user_async)
):
    """Get user's call history with pagination and filtering"""
    user_id = user["user_id"]
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build WHERE conditions
        conditions = ["(user_id = $1 OR listener_id = $1)"]
        params = [user_id]
        param_count = 1
        
        if call_type and call_type in ['audio', 'video']:
            param_count += 1
            conditions.append(f"call_type = ${param_count}")
            params.append(call_type)
        
        if status and status in ['ongoing', 'completed', 'dropped']:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status)
        
        where_clause = " AND ".join(conditions)
        
        # Get calls with pagination and filtering
        calls = await conn.fetch(
            f"""
            SELECT uc.*, 
                   u1.username as caller_username,
                   u2.username as listener_username
            FROM user_calls uc
            LEFT JOIN users u1 ON uc.user_id = u1.user_id
            LEFT JOIN users u2 ON uc.listener_id = u2.user_id
            WHERE {where_clause}
            ORDER BY uc.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """,
            *params, per_page, offset
        )
        
        # Get total count with same filters
        total_calls = await conn.fetchval(
            f"SELECT COUNT(*) FROM user_calls WHERE {where_clause}",
            *params
        )
        
        # Get total coins spent (as caller)
        total_coins_spent = await conn.fetchval(
            f"""
            SELECT COALESCE(SUM(coins_spent), 0) 
            FROM user_calls 
            WHERE user_id = $1 AND {where_clause.replace('(user_id = $1 OR listener_id = $1)', 'user_id = $1')}
            """,
            user_id, *params[1:]
        )
        
        
        # Get total earnings (as listener)
        total_earnings = await conn.fetchval(
            f"""
            SELECT COALESCE(SUM(listener_money_earned), 0) 
            FROM user_calls 
            WHERE listener_id = $1 AND {where_clause.replace('(user_id = $1 OR listener_id = $1)', 'listener_id = $1')}
            """,
            user_id, *params[1:]
        )
        
        # Convert to CallInfo objects
        call_infos = []
        for call in calls:
            call_info = CallInfo(
                call_id=call['call_id'],
                user_id=call['user_id'],
                listener_id=call['listener_id'],
                call_type=CallType(call['call_type']),
                start_time=call['start_time'],
                end_time=call['end_time'],
                duration_seconds=call['duration_seconds'],
                duration_minutes=call['duration_minutes'],
                coins_spent=call['coins_spent'],
                listener_money_earned=call['listener_money_earned'],
                status=CallStatus(call['status']),
                updated_at=call['updated_at'],
                created_at=call['created_at']
            )
            call_infos.append(call_info)
        
        return CallHistoryResponse(
            calls=call_infos,
            total_calls=total_calls,
            total_coins_spent=total_coins_spent,
            total_earnings=total_earnings,
            page=page,
            per_page=per_page,
            has_next=len(calls) > per_page,
            has_previous=page > 1
        )

async def update_user_coin_balance(user_id: int, coins: int, operation: str = "subtract", tx_type: str = "spend"):
    """Update user's coin balance in wallet and create transaction record"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        if operation == "subtract":
            # Check if user has enough coins
            current_balance = await get_user_coin_balance(user_id)
            if current_balance < coins:
                raise HTTPException(status_code=400, detail="Insufficient coins")
            
            # Update wallet balance
            await conn.execute(
                "UPDATE user_wallets SET balance_coins = balance_coins - $1, updated_at = now() WHERE user_id = $2",
                coins, user_id
            )
            
            # Create transaction record
            wallet_id = await conn.fetchval("SELECT wallet_id FROM user_wallets WHERE user_id = $1", user_id)
            if wallet_id:
                await conn.execute(
                    """
                    INSERT INTO user_transactions (wallet_id, tx_type, coins_change, created_at)
                    VALUES ($1, $2, $3, now())
                    """,
                    wallet_id, tx_type, -coins
                )
        elif operation == "add":
            # Update wallet balance
            await conn.execute(
                "UPDATE user_wallets SET balance_coins = balance_coins + $1, updated_at = now() WHERE user_id = $2",
                coins, user_id
            )
            
            # Create transaction record
            wallet_id = await conn.fetchval("SELECT wallet_id FROM user_wallets WHERE user_id = $1", user_id)
            if wallet_id:
                await conn.execute(
                    """
                    INSERT INTO user_transactions (wallet_id, tx_type, coins_change, created_at)
                    VALUES ($1, $2, $3, now())
                    """,
                    wallet_id, "earn", coins
                )

async def update_both_users_presence(user_id: int, listener_id: int, is_busy: bool, wait_time: int = None):
    """Update presence status for both caller and listener simultaneously"""
    print(f"🔄 Updating presence for both users: {user_id} and {listener_id}, busy={is_busy}")
    
    # Update both users' status in parallel
    await asyncio.gather(
        set_user_busy_status(user_id, is_busy, wait_time),
        set_user_busy_status(listener_id, is_busy, wait_time)
    )
    
    print(f"✅ Both users' presence status updated successfully")

async def set_user_busy_status(user_id: int, is_busy: bool, wait_time: int = None):
    """Set user's busy status during calls and broadcast to all connected clients"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Update user status in database
        await conn.execute(
            """
            UPDATE user_status 
            SET is_busy = $1, wait_time = $2, updated_at = now()
            WHERE user_id = $3
            """,
            is_busy, wait_time, user_id
        )
        
        # Also update is_online to true when starting a call
        if is_busy:
            await conn.execute(
                """
                UPDATE user_status 
                SET is_online = TRUE, last_seen = now(), updated_at = now()
                WHERE user_id = $1
                """,
                user_id
            )

