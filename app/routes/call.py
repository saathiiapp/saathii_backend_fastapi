from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List
import time
import asyncio
from datetime import datetime, timedelta
from app.clients.redis_client import redis_client
from app.clients.db import get_db_pool
from app.clients.jwt_handler import decode_jwt
from app.utils.realtime import broadcast_user_status_update, get_user_status_for_broadcast
from app.schemas.call import (
    StartCallRequest,
    StartCallResponse,
    EndCallRequest,
    EndCallResponse,
    CallInfo,
    CallHistoryResponse,
    CoinBalanceResponse,
    CallType,
    CallStatus,
    DEFAULT_CALL_RATES,
    RECHARGE_RATES,
    RechargeRequest,
    RechargeResponse,
    RechargeHistoryResponse
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
    """Get user's current coin balance from wallet"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT balance_coins FROM user_wallets WHERE user_id = $1",
            user_id
        )
        return result or 0

async def update_user_coin_balance(user_id: int, amount: int, operation: str = "subtract", tx_type: str = "spend"):
    """Update user's coin balance in wallet and create transaction record"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        if operation == "subtract":
            # Check if user has enough coins
            current_balance = await get_user_coin_balance(user_id)
            if current_balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient coins")
            
            # Update wallet balance
            await conn.execute(
                "UPDATE user_wallets SET balance_coins = balance_coins - $1, updated_at = now() WHERE user_id = $2",
                amount, user_id
            )
            
            # Create transaction record
            wallet_id = await conn.fetchval("SELECT wallet_id FROM user_wallets WHERE user_id = $1", user_id)
            if wallet_id:
                await conn.execute(
                    """
                    INSERT INTO user_transactions (wallet_id, tx_type, coins_change, created_at)
                    VALUES ($1, $2, $3, now())
                    """,
                    wallet_id, tx_type, -amount
                )
        elif operation == "add":
            # Update wallet balance
            await conn.execute(
                "UPDATE user_wallets SET balance_coins = balance_coins + $1, updated_at = now() WHERE user_id = $2",
                amount, user_id
            )
            
            # Create transaction record
            wallet_id = await conn.fetchval("SELECT wallet_id FROM user_wallets WHERE user_id = $1", user_id)
            if wallet_id:
                await conn.execute(
                    """
                    INSERT INTO user_transactions (wallet_id, tx_type, coins_change, created_at)
                    VALUES ($1, $2, $3, now())
                    """,
                    wallet_id, "earn", amount
                )

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

async def set_user_busy_status(user_id: int, is_busy: bool, busy_until: datetime = None):
    """Set user's busy status during calls and broadcast to all connected clients"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Update user status in database
        await conn.execute(
            """
            UPDATE user_status 
            SET is_busy = $1, busy_until = $2, updated_at = now()
            WHERE user_id = $3
            """,
            is_busy, busy_until, user_id
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
        
        # Get updated status for broadcasting
        status_data = await get_user_status_for_broadcast(user_id)
        if status_data:
            # Broadcast to all connected clients
            await broadcast_user_status_update(user_id, status_data)
            print(f"📞 User {user_id} status updated: busy={is_busy}, broadcasted to all clients")

async def update_both_users_presence(user_id: int, listener_id: int, is_busy: bool, busy_until: datetime = None):
    """Update presence status for both caller and listener simultaneously"""
    print(f"🔄 Updating presence for both users: {user_id} and {listener_id}, busy={is_busy}")
    
    # Update both users' status in parallel
    await asyncio.gather(
        set_user_busy_status(user_id, is_busy, busy_until),
        set_user_busy_status(listener_id, is_busy, busy_until)
    )
    
    print(f"✅ Both users' presence status updated successfully")

async def cleanup_expired_calls():
    """Background task to cleanup expired calls and update presence status"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Find calls that should have ended (busy_until < now)
        expired_calls = await conn.fetch(
            """
            SELECT call_id, user_id, listener_id 
            FROM user_calls uc
            JOIN user_status us1 ON uc.user_id = us1.user_id
            JOIN user_status us2 ON uc.listener_id = us2.user_id
            WHERE uc.status = 'ongoing' 
            AND (us1.busy_until < now() OR us2.busy_until < now())
            """
        )
        
        for call in expired_calls:
            print(f"🧹 Cleaning up expired call {call['call_id']}")
            
            # Update call as dropped
            await conn.execute(
                """
                UPDATE user_calls 
                SET status = 'dropped', end_time = now(), updated_at = now()
                WHERE call_id = $1
                """,
                call['call_id']
            )
            
            # Set both users as not busy
            await update_both_users_presence(call['user_id'], call['listener_id'], False)
            
            # Remove from Redis
            await redis_client.delete(f"call:{call['call_id']}")
            
            print(f"✅ Expired call {call['call_id']} cleaned up successfully")

def calculate_call_cost(call_type: CallType, duration_minutes: int) -> int:
    """Calculate call cost based on type and duration"""
    rate_config = DEFAULT_CALL_RATES[call_type]
    cost = max(rate_config.minimum_charge, duration_minutes * rate_config.rate_per_minute)
    return cost

@router.post("/calls/start", response_model=StartCallResponse, tags=["Call Management"])
async def start_call(data: StartCallRequest, user=Depends(get_current_user_async)):
    """Start a new call with a listener"""
    user_id = user["user_id"]
    
    # Validate listener exists and is available
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        listener = await conn.fetchrow(
            "SELECT user_id, username FROM users WHERE user_id = $1",
            data.listener_id
        )
        if not listener:
            raise HTTPException(status_code=404, detail="Listener not found")
        
        # Check if listener is available
        listener_available = await check_user_availability(data.listener_id)
        if not listener_available:
            raise HTTPException(status_code=409, detail="Listener is currently busy")
        
        # Check if user is available
        user_available = await check_user_availability(user_id)
        if not user_available:
            raise HTTPException(status_code=409, detail="You are already in a call")
        
        # Get user's current coin balance
        current_balance = await get_user_coin_balance(user_id)
        
        # Calculate maximum possible duration based on available coins
        rate_per_minute = DEFAULT_CALL_RATES[data.call_type].rate_per_minute
        max_duration_minutes = current_balance // rate_per_minute
        
        if max_duration_minutes < 1:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient coins. Need at least {rate_per_minute} coins for 1 minute {data.call_type.value} call. Available: {current_balance}"
            )
        
        # Use estimated duration if provided, otherwise use maximum possible
        estimated_duration = min(data.estimated_duration_minutes or max_duration_minutes, max_duration_minutes)
        estimated_cost = calculate_call_cost(data.call_type, estimated_duration)
        
        # Ensure user has a wallet
        await conn.execute(
            """
            INSERT INTO user_wallets (user_id, balance_coins, created_at)
            VALUES ($1, 0, now())
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id
        )
        
        # Reserve coins for the call (subtract minimum charge)
        minimum_charge = DEFAULT_CALL_RATES[data.call_type].minimum_charge
        await update_user_coin_balance(user_id, minimum_charge, "subtract", "spend")
        
        # Create call record
        call = await conn.fetchrow(
            """
            INSERT INTO user_calls 
            (user_id, listener_id, call_type, status, coins_spent, user_money_spend, listener_money_earned)
            VALUES ($1, $2, $3, 'ongoing', $4, $4, 0)
            RETURNING call_id, coins_spent
            """,
            user_id, data.listener_id, data.call_type.value, minimum_charge
        )
        
        # Set both users as busy simultaneously
        busy_until = datetime.utcnow() + timedelta(hours=2)  # Max 2 hours
        await update_both_users_presence(user_id, data.listener_id, True, busy_until)
        
        # Store call info in Redis for real-time tracking
        call_key = f"call:{call['call_id']}"
        await redis_client.hset(call_key, mapping={
            "user_id": str(user_id),
            "listener_id": str(data.listener_id),
            "call_type": data.call_type.value,
            "start_time": str(int(time.time())),
            "coins_spent": str(minimum_charge)
        })
        await redis_client.expire(call_key, 7200)  # 2 hours expiry
        
        return StartCallResponse(
            call_id=call['call_id'],
            message=f"Call started successfully. Maximum duration: {max_duration_minutes} minutes",
            estimated_cost=estimated_cost,
            remaining_coins=current_balance - minimum_charge,
            call_type=data.call_type,
            listener_id=data.listener_id,
            status=CallStatus.ONGOING
        )

@router.post("/calls/end", response_model=EndCallResponse, tags=["Call Management"])
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
        
        # Calculate final duration and cost
        start_time = call['start_time']
        end_time = datetime.utcnow()
        duration_seconds = int((end_time - start_time).total_seconds())
        duration_minutes = max(1, duration_seconds // 60)  # Minimum 1 minute
        
        # Calculate additional cost beyond minimum charge
        call_type = CallType(call['call_type'])
        total_cost = calculate_call_cost(call_type, duration_minutes)
        additional_cost = total_cost - call['coins_spent']
        
        # Check if user has enough coins for additional cost
        if additional_cost > 0:
            current_balance = await get_user_coin_balance(user_id)
            if current_balance < additional_cost:
                # Handle coin empty scenario
                await conn.execute(
                    """
                    UPDATE user_calls 
                    SET end_time = $1, duration_seconds = $2, duration_minutes = $3, 
                        status = 'dropped', updated_at = now()
                    WHERE call_id = $4
                    """,
                    end_time, duration_seconds, duration_minutes, data.call_id
                )
                
                # Set both users as not busy
                await update_both_users_presence(call['user_id'], call['listener_id'], False)
                
                # Remove from Redis
                await redis_client.delete(f"call:{data.call_id}")
                
                return EndCallResponse(
                    call_id=data.call_id,
                    message="Call ended due to insufficient coins",
                    duration_seconds=duration_seconds,
                    duration_minutes=duration_minutes,
                    coins_spent=call['coins_spent'],
                    user_money_spend=call['user_money_spend'],
                    listener_money_earned=0,
                    status=CallStatus.DROPPED
                )
            
            # Deduct additional cost
            await update_user_coin_balance(user_id, additional_cost, "subtract", "spend")
        
        # Calculate listener earnings (1.5x the rate per minute)
        call_type = CallType(call['call_type'])
        rate_per_minute = DEFAULT_CALL_RATES[call_type].rate_per_minute
        listener_rate_per_minute = int(rate_per_minute * 1.5)
        listener_earnings = listener_rate_per_minute * duration_minutes
        
        # Update call record
        await conn.execute(
            """
            UPDATE user_calls 
            SET end_time = $1, duration_seconds = $2, duration_minutes = $3,
                coins_spent = $4, user_money_spend = $4, listener_money_earned = $5,
                status = $6, updated_at = now()
            WHERE call_id = $7
            """,
            end_time, duration_seconds, duration_minutes, total_cost, 
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
            coins_spent=total_cost,
            user_money_spend=total_cost,
            listener_money_earned=listener_earnings,
            status=CallStatus.COMPLETED if data.reason != "dropped" else CallStatus.DROPPED
        )

@router.get("/calls/ongoing", response_model=CallInfo, tags=["Call Management"])
async def get_ongoing_call(user=Depends(get_current_user_async)):
    """Get current ongoing call for the user"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        call = await conn.fetchrow(
            """
            SELECT * FROM user_calls 
            WHERE (user_id = $1 OR listener_id = $1) AND status = 'ongoing'
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id
        )
        
        if not call:
            raise HTTPException(status_code=404, detail="No ongoing call found")
        
        return CallInfo(**dict(call))

@router.get("/calls/history", response_model=CallHistoryResponse, tags=["Call Management"])
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
            f"SELECT COALESCE(SUM(coins_spent), 0) FROM user_calls WHERE user_id = $1 AND {where_clause.replace('(user_id = $1 OR listener_id = $1)', 'user_id = $1')}",
            user_id, *params[1:]
        )
        
        # Get total money spent (as caller)
        total_money_spent = await conn.fetchval(
            f"SELECT COALESCE(SUM(user_money_spend), 0) FROM user_calls WHERE user_id = $1 AND {where_clause.replace('(user_id = $1 OR listener_id = $1)', 'user_id = $1')}",
            user_id, *params[1:]
        )
        
        # Get total earnings (as listener)
        total_earnings = await conn.fetchval(
            f"SELECT COALESCE(SUM(listener_money_earned), 0) FROM user_calls WHERE listener_id = $1 AND {where_clause.replace('(user_id = $1 OR listener_id = $1)', 'listener_id = $1')}",
            user_id, *params[1:]
        )
        
        call_list = [CallInfo(**dict(call)) for call in calls]
        
        return CallHistoryResponse(
            calls=call_list,
            total_calls=total_calls,
            total_coins_spent=total_coins_spent,
            total_money_spent=total_money_spent,
            total_earnings=total_earnings,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total_calls,
            has_previous=page > 1
        )

@router.get("/calls/history/summary", tags=["Call Management"])
async def get_call_history_summary(user=Depends(get_current_user_async)):
    """Get call history summary with statistics"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get call statistics
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_calls,
                COUNT(CASE WHEN user_id = $1 THEN 1 END) as calls_made,
                COUNT(CASE WHEN listener_id = $1 THEN 1 END) as calls_received,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_calls,
                COUNT(CASE WHEN status = 'dropped' THEN 1 END) as dropped_calls,
                COUNT(CASE WHEN status = 'ongoing' THEN 1 END) as ongoing_calls,
                COUNT(CASE WHEN call_type = 'audio' THEN 1 END) as audio_calls,
                COUNT(CASE WHEN call_type = 'video' THEN 1 END) as video_calls,
                COALESCE(SUM(coins_spent), 0) as total_coins_spent,
                COALESCE(SUM(user_money_spend), 0) as total_money_spent,
                COALESCE(SUM(listener_money_earned), 0) as total_earnings,
                COALESCE(SUM(duration_seconds), 0) as total_duration_seconds,
                COALESCE(AVG(duration_seconds), 0) as avg_duration_seconds
            FROM user_calls 
            WHERE user_id = $1 OR listener_id = $1
            """,
            user_id
        )
        
        # Get recent calls (last 5)
        recent_calls = await conn.fetch(
            """
            SELECT uc.*, 
                   u1.username as caller_username,
                   u2.username as listener_username
            FROM user_calls uc
            LEFT JOIN users u1 ON uc.user_id = u1.user_id
            LEFT JOIN users u2 ON uc.listener_id = u2.user_id
            WHERE uc.user_id = $1 OR uc.listener_id = $1
            ORDER BY uc.created_at DESC
            LIMIT 5
            """,
            user_id
        )
        
        # Get monthly statistics (last 6 months)
        monthly_stats = await conn.fetch(
            """
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                COUNT(*) as calls_count,
                COALESCE(SUM(coins_spent), 0) as coins_spent,
                COALESCE(SUM(listener_money_earned), 0) as earnings
            FROM user_calls 
            WHERE (user_id = $1 OR listener_id = $1) 
            AND created_at >= NOW() - INTERVAL '6 months'
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month DESC
            """,
            user_id
        )
        
        return {
            "summary": dict(stats),
            "recent_calls": [dict(call) for call in recent_calls],
            "monthly_stats": [dict(month) for month in monthly_stats]
        }

@router.get("/calls/balance", response_model=CoinBalanceResponse, tags=["Call Management"])
async def get_coin_balance(user=Depends(get_current_user_async)):
    """Get user's coin balance and spending history"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Ensure user has a wallet
        await conn.execute(
            """
            INSERT INTO user_wallets (user_id, balance_coins, created_at)
            VALUES ($1, 0, now())
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id
        )
        
        # Get current balance
        current_balance = await get_user_coin_balance(user_id)
        
        # Get total spent from transactions
        total_spent = await conn.fetchval(
            """
            SELECT COALESCE(SUM(ABS(coins_change)), 0) 
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'spend'
            """,
            user_id
        )
        
        # Get total earned from transactions
        total_earned = await conn.fetchval(
            """
            SELECT COALESCE(SUM(coins_change), 0) 
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'earn'
            """,
            user_id
        )
        
        return CoinBalanceResponse(
            user_id=user_id,
            current_balance=current_balance,
            total_earned=total_earned,
            total_spent=total_spent
        )

@router.post("/calls/emergency-end/{call_id}", response_model=EndCallResponse, tags=["Call Management"])
async def emergency_end_call(call_id: int, user=Depends(get_current_user_async)):
    """Emergency end call (for dropped calls, technical issues, etc.)"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get call details
        call = await conn.fetchrow(
            """
            SELECT * FROM user_calls 
            WHERE call_id = $1 AND (user_id = $2 OR listener_id = $2) AND status = 'ongoing'
            """,
            call_id, user_id
        )
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found or already ended")
        
        # Calculate duration
        start_time = call['start_time']
        end_time = datetime.utcnow()
        duration_seconds = int((end_time - start_time).total_seconds())
        duration_minutes = max(1, duration_seconds // 60)
        
        # Update call as dropped
        await conn.execute(
            """
            UPDATE user_calls 
            SET end_time = $1, duration_seconds = $2, duration_minutes = $3,
                status = 'dropped', updated_at = now()
            WHERE call_id = $4
            """,
            end_time, duration_seconds, duration_minutes, call_id
        )
        
        # Set both users as not busy
        await update_both_users_presence(call['user_id'], call['listener_id'], False)
        
        # Remove from Redis
        await redis_client.delete(f"call:{call_id}")
        
        return EndCallResponse(
            call_id=call_id,
            message="Call ended due to technical issues",
            duration_seconds=duration_seconds,
            duration_minutes=duration_minutes,
            coins_spent=call['coins_spent'],
            user_money_spend=call['user_money_spend'],
            listener_money_earned=0,
            status=CallStatus.DROPPED
        )

@router.post("/calls/recharge", response_model=RechargeResponse, tags=["Call Management"])
async def recharge_coins(data: RechargeRequest, user=Depends(get_current_user_async)):
    """Recharge coins with real money"""
    user_id = user["user_id"]
    
    # Validate recharge amount
    if str(data.amount_rupees) not in RECHARGE_RATES:
        available_amounts = list(RECHARGE_RATES.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid recharge amount. Available amounts: {available_amounts}"
        )
    
    coins_to_add = RECHARGE_RATES[str(data.amount_rupees)]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Ensure user has a wallet
        await conn.execute(
            """
            INSERT INTO user_wallets (user_id, balance_coins, created_at)
            VALUES ($1, 0, now())
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id
        )
        
        # Add coins to wallet
        await conn.execute(
            "UPDATE user_wallets SET balance_coins = balance_coins + $1, updated_at = now() WHERE user_id = $2",
            coins_to_add, user_id
        )
        
        # Create transaction record
        wallet_id = await conn.fetchval("SELECT wallet_id FROM user_wallets WHERE user_id = $1", user_id)
        if wallet_id:
            await conn.execute(
                """
                INSERT INTO user_transactions (wallet_id, tx_type, coins_change, money_change, created_at)
                VALUES ($1, 'purchase', $2, $3, now())
                """,
                wallet_id, coins_to_add, data.amount_rupees
            )
        
        # Get new balance
        new_balance = await get_user_coin_balance(user_id)
        
        # Generate transaction ID
        transaction_id = f"RCH_{user_id}_{int(time.time())}"
        
        return RechargeResponse(
            transaction_id=transaction_id,
            amount_rupees=data.amount_rupees,
            coins_added=coins_to_add,
            new_balance=new_balance,
            message=f"Successfully recharged {coins_to_add} coins for ₹{data.amount_rupees}"
        )

@router.get("/calls/recharge/history", response_model=RechargeHistoryResponse, tags=["Call Management"])
async def get_recharge_history(
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """Get user's recharge history"""
    user_id = user["user_id"]
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get recharge transactions
        transactions = await conn.fetch(
            """
            SELECT ut.*, uw.user_id
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'purchase'
            ORDER BY ut.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id, per_page, offset
        )
        
        # Get total count
        total_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'purchase'
            """,
            user_id
        )
        
        # Get total recharged
        total_recharged = await conn.fetchval(
            """
            SELECT COALESCE(SUM(ut.money_change), 0)
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'purchase'
            """,
            user_id
        )
        
        # Get total coins added
        total_coins_added = await conn.fetchval(
            """
            SELECT COALESCE(SUM(ut.coins_change), 0)
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'purchase'
            """,
            user_id
        )
        
        transaction_list = [dict(transaction) for transaction in transactions]
        
        return RechargeHistoryResponse(
            transactions=transaction_list,
            total_recharged=total_recharged,
            total_coins_added=total_coins_added,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total_count,
            has_previous=page > 1
        )

@router.post("/calls/bill-minute/{call_id}", tags=["Call Management"])
async def bill_call_minute(call_id: int, user=Depends(get_current_user_async)):
    """Bill for one minute of call (called every minute during call)"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get call details
        call = await conn.fetchrow(
            """
            SELECT * FROM user_calls 
            WHERE call_id = $1 AND (user_id = $2 OR listener_id = $2) AND status = 'ongoing'
            """,
            call_id, user_id
        )
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found or already ended")
        
        # Get current balance
        current_balance = await get_user_coin_balance(user_id)
        
        # Calculate cost for one minute
        call_type = CallType(call['call_type'])
        rate_per_minute = DEFAULT_CALL_RATES[call_type].rate_per_minute
        
        if current_balance < rate_per_minute:
            # Not enough coins, end the call
            await conn.execute(
                """
                UPDATE user_calls 
                SET status = 'dropped', updated_at = now()
                WHERE call_id = $1
                """,
                call_id
            )
            
            # Set both users as not busy
            await update_both_users_presence(call['user_id'], call['listener_id'], False)
            
            # Remove from Redis
            await redis_client.delete(f"call:{call_id}")
            
            raise HTTPException(
                status_code=400, 
                detail="Call ended due to insufficient coins"
            )
        
        # Deduct coins for one minute
        await update_user_coin_balance(user_id, rate_per_minute, "subtract", "spend")
        
        # Update call record
        await conn.execute(
            """
            UPDATE user_calls 
            SET coins_spent = coins_spent + $1, user_money_spend = user_money_spend + $1, updated_at = now()
            WHERE call_id = $2
            """,
            rate_per_minute, call_id
        )
        
        # Update Redis with new total
        call_key = f"call:{call_id}"
        current_total = await redis_client.hget(call_key, "coins_spent")
        new_total = int(current_total or 0) + rate_per_minute
        await redis_client.hset(call_key, "coins_spent", str(new_total))
        
        return {
            "call_id": call_id,
            "coins_deducted": rate_per_minute,
            "remaining_coins": current_balance - rate_per_minute,
            "total_coins_spent": new_total,
            "message": "Successfully billed for 1 minute"
        }

@router.post("/calls/cleanup", tags=["Call Management"])
async def cleanup_calls(user=Depends(get_current_user_async)):
    """Manually trigger cleanup of expired calls"""
    await cleanup_expired_calls()
    return {"message": "Call cleanup completed successfully"}

@router.get("/calls/status", tags=["Call Management"])
async def get_call_system_status(user=Depends(get_current_user_async)):
    """Get call system status and ongoing calls count"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get ongoing calls count
        ongoing_calls = await conn.fetchval(
            "SELECT COUNT(*) FROM user_calls WHERE status = 'ongoing'"
        )
        
        # Get busy users count
        busy_users = await conn.fetchval(
            "SELECT COUNT(*) FROM user_status WHERE is_busy = TRUE"
        )
        
        # Get Redis call keys count
        redis_calls = len([key async for key in redis_client.scan_iter(match="call:*")])
        
        return {
            "ongoing_calls": ongoing_calls,
            "busy_users": busy_users,
            "redis_call_keys": redis_calls,
            "system_status": "healthy" if ongoing_calls == redis_calls else "warning"
        }

@router.get("/calls/rates", tags=["Call Management"])
async def get_call_rates():
    """Get current call rates and recharge options"""
    return {
        "call_rates": {
            "audio": {
                "rate_per_minute": DEFAULT_CALL_RATES[CallType.AUDIO].rate_per_minute,
                "minimum_charge": DEFAULT_CALL_RATES[CallType.AUDIO].minimum_charge
            },
            "video": {
                "rate_per_minute": DEFAULT_CALL_RATES[CallType.VIDEO].rate_per_minute,
                "minimum_charge": DEFAULT_CALL_RATES[CallType.VIDEO].minimum_charge
            }
        },
        "recharge_options": RECHARGE_RATES,
        "listener_earnings": {
            "audio": int(DEFAULT_CALL_RATES[CallType.AUDIO].rate_per_minute * 1.5),
            "video": int(DEFAULT_CALL_RATES[CallType.VIDEO].rate_per_minute * 1.5)
        }
    }
