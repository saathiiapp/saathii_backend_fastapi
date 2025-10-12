"""
Per-minute coin deduction service for ongoing calls
Runs every minute to deduct coins from users during active calls
"""
import asyncio
import logging
from datetime import datetime
from api.clients.db import get_db_pool
from api.clients.redis_client import redis_client
from api.schemas.call import DEFAULT_CALL_RATES, CallType
from api.utils.badge_manager import get_listener_earning_rate

logger = logging.getLogger(__name__)

async def deduct_per_minute_coins():
    """Background task to deduct coins every minute for ongoing calls"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get all ongoing calls
        ongoing_calls = await conn.fetch(
            """
            SELECT call_id, user_id, listener_id, call_type, start_time, coins_spent
            FROM user_calls 
            WHERE status = 'ongoing'
            ORDER BY start_time ASC
            """
        )
        
        if not ongoing_calls:
            logger.info("📞 No ongoing calls found for coin deduction")
            return
        
        logger.info(f"💰 Processing {len(ongoing_calls)} ongoing calls for per-minute coin deduction")
        
        for call in ongoing_calls:
            try:
                await process_call_coin_deduction(conn, call)
            except Exception as e:
                logger.error(f"❌ Error processing call {call['call_id']} for coin deduction: {e}")
                # Continue with other calls even if one fails
                continue

async def process_call_coin_deduction(conn, call):
    """Process coin deduction for a single ongoing call - deduct rate_per_minute"""
    call_id = call['call_id']
    user_id = call['user_id']
    listener_id = call['listener_id']
    call_type = CallType(call['call_type'])
    start_time = call['start_time']
    coins_already_spent = call['coins_spent']
    
    # Calculate current call duration
    current_time = datetime.utcnow()
    duration_seconds = int((current_time - start_time).total_seconds())
    duration_minutes = duration_seconds // 60
    
    # Get the rate per minute for this call type
    rate_per_minute = DEFAULT_CALL_RATES[call_type]["rate_per_minute"]
    
    # Check if user has enough coins for this minute
    current_balance = await get_user_coin_balance(user_id)
    
    if current_balance < rate_per_minute:
        # User doesn't have enough coins - end the call
        logger.warning(f"💰 Call {call_id}: User {user_id} has insufficient coins. Balance: {current_balance}, Needed: {rate_per_minute}")
        await end_call_due_to_insufficient_coins(conn, call, current_balance)
        return
    
    # Deduct the rate_per_minute
    try:
        await update_user_coin_balance(conn, user_id, rate_per_minute, "subtract", "spend")
        
        # Update the call record with new coins_spent
        new_total_coins_spent = coins_already_spent + rate_per_minute
        await conn.execute(
            """
            UPDATE user_calls 
            SET coins_spent = $1, updated_at = now()
            WHERE call_id = $2 AND status = 'ongoing'
            """,
            new_total_coins_spent, call_id
        )
        
        # Update Redis cache
        call_key = f"call:{call_id}"
        await redis_client.hset(call_key, "coins_spent", str(new_total_coins_spent))
        
        logger.info(f"💰 Call {call_id}: Deducted {rate_per_minute} coins from user {user_id}. Total spent: {new_total_coins_spent}, Duration: {duration_minutes} minutes")
        
    except Exception as e:
        logger.error(f"❌ Failed to deduct coins for call {call_id}: {e}")
        # If coin deduction fails, end the call
        await end_call_due_to_insufficient_coins(conn, call, current_balance)

async def end_call_due_to_insufficient_coins(conn, call, current_balance):
    """End a call due to insufficient coins and settle properly"""
    call_id = call['call_id']
    user_id = call['user_id']
    listener_id = call['listener_id']
    call_type = CallType(call['call_type'])
    start_time = call['start_time']
    coins_already_spent = call['coins_spent']
    
    # Calculate final duration
    end_time = datetime.utcnow()
    duration_seconds = int((end_time - start_time).total_seconds())
    duration_minutes = max(1, duration_seconds // 60)
    
    # Calculate listener earnings based on what user actually paid
    listener_rupees_per_minute = await get_listener_earning_rate(listener_id, call_type.value)
    actual_duration_paid = coins_already_spent // DEFAULT_CALL_RATES[call_type]["rate_per_minute"]
    listener_earnings = int(listener_rupees_per_minute * actual_duration_paid)
    
    try:
        # Use transaction to ensure atomicity
        async with conn.transaction():
            # Update call as dropped
            await conn.execute(
                """
                UPDATE user_calls 
                SET end_time = $1, duration_seconds = $2, duration_minutes = $3,
                    listener_money_earned = $4, status = 'dropped', updated_at = now()
                WHERE call_id = $5 AND status = 'ongoing'
                """,
                end_time, duration_seconds, duration_minutes, listener_earnings, call_id
            )
            
            # Add earnings to listener (only if call was actually updated)
            if conn.get_cursor().rowcount > 0 and listener_earnings > 0:
                await update_user_coin_balance(conn, listener_id, listener_earnings, "add", "earn")
        
        # Set both users as not busy
        await update_both_users_presence(user_id, listener_id, False)
        
        # Remove from Redis
        await redis_client.delete(f"call:{call_id}")
        
        logger.info(f"📞 Call {call_id} ended due to insufficient coins. User paid: {coins_already_spent} coins, Listener earned: ₹{listener_earnings}")
        
    except Exception as e:
        logger.error(f"❌ Error ending call {call_id} due to insufficient coins: {e}")

async def get_user_coin_balance(user_id: int) -> int:
    """Get user's current coin balance"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        balance = await conn.fetchval(
            "SELECT balance_coins FROM user_wallets WHERE user_id = $1",
            user_id
        )
        return balance or 0

async def update_user_coin_balance(conn, user_id: int, amount: int, operation: str = "subtract", tx_type: str = "spend"):
    """Update user's coin balance in wallet and create transaction record"""
    if operation == "subtract":
        # Check if user has enough coins
        current_balance = await get_user_coin_balance(user_id)
        if current_balance < amount:
            raise ValueError("Insufficient coins")
        
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

async def update_both_users_presence(user_id: int, listener_id: int, is_busy: bool, wait_time: int = None):
    """Update presence status for both caller and listener simultaneously"""
    logger.info(f"🔄 Updating presence for both users: {user_id} and {listener_id}, busy={is_busy}")
    
    # Update both users' status in parallel
    await asyncio.gather(
        set_user_busy_status(user_id, is_busy, wait_time),
        set_user_busy_status(listener_id, is_busy, wait_time)
    )
    
    logger.info(f"✅ Both users' presence status updated successfully")

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
        
        # Get updated status for broadcasting
        from api.utils.realtime import get_user_status_for_broadcast, broadcast_user_status_update
        status_data = await get_user_status_for_broadcast(user_id)
        if status_data:
            # Broadcast to all connected clients
            await broadcast_user_status_update(user_id, status_data)
