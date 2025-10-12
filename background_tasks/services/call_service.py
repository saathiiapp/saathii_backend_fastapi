"""
Call-related background services
"""
import asyncio
import logging
from datetime import datetime, timedelta
from api.clients.db import get_db_pool
from api.clients.redis_client import redis_client
from api.utils.badge_manager import get_listener_earning_rate
from api.schemas.call import DEFAULT_CALL_RATES, CallType

logger = logging.getLogger(__name__)

async def cleanup_expired_calls():
    """Background task to cleanup expired calls and update presence status"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Find calls that should have ended (busy_until < now)
        expired_calls = await conn.fetch(
            """
            SELECT call_id, user_id, listener_id, call_type, start_time, coins_spent
            FROM user_calls uc
            JOIN user_status us1 ON uc.user_id = us1.user_id
            JOIN user_status us2 ON uc.listener_id = us2.user_id
            WHERE uc.status = 'ongoing' 
            AND (us1.busy_until < now() OR us2.busy_until < now())
            """
        )
        
        for call in expired_calls:
            try:
                logger.info(f"🧹 Cleaning up expired call {call['call_id']}")
                
                # Calculate duration and proper settlement
                start_time = call['start_time']
                end_time = datetime.utcnow()
                duration_seconds = int((end_time - start_time).total_seconds())
                duration_minutes = max(1, duration_seconds // 60)
                
                # Calculate proper costs based on actual duration
                call_type = CallType(call['call_type'])
                total_cost = calculate_call_cost(call_type, duration_minutes)
                
                # Calculate listener earnings based on actual duration and badge
                listener_rupees_per_minute = await get_listener_earning_rate(call['listener_id'], call_type.value)
                listener_earnings = int(listener_rupees_per_minute * duration_minutes)
                
                # Check if user has already paid enough
                coins_already_spent = call['coins_spent']
                additional_cost = total_cost - coins_already_spent
                
                # If user needs to pay more, deduct additional coins
                if additional_cost > 0:
                    current_balance = await get_user_coin_balance(call['user_id'])
                    if current_balance >= additional_cost:
                        await update_user_coin_balance(call['user_id'], additional_cost, "subtract", "spend")
                        final_coins_spent = total_cost
                    else:
                        # User doesn't have enough coins, use what they already paid
                        final_coins_spent = coins_already_spent
                        # Recalculate listener earnings based on what user actually paid
                        actual_duration_paid = coins_already_spent // DEFAULT_CALL_RATES[call_type].rate_per_minute
                        listener_earnings = listener_rupees_per_minute * actual_duration_paid
                else:
                    # User has already paid enough or more than needed
                    final_coins_spent = coins_already_spent
                
                # Use transaction to ensure atomicity
                async with conn.transaction():
                    # Update call as dropped with proper settlement
                    await conn.execute(
                        """
                        UPDATE user_calls 
                        SET end_time = $1, duration_seconds = $2, duration_minutes = $3,
                            coins_spent = $4, user_money_spend = $4, listener_money_earned = $5,
                            status = 'dropped', updated_at = now()
                        WHERE call_id = $6 AND status = 'ongoing'
                        """,
                        end_time, duration_seconds, duration_minutes, final_coins_spent, 
                        listener_earnings, call['call_id']
                    )
                    
                    # Add earnings to listener (only if call was actually updated)
                    if conn.get_cursor().rowcount > 0 and listener_earnings > 0:
                        await update_user_coin_balance(call['listener_id'], listener_earnings, "add", "earn")
                
                # Set both users as not busy (outside transaction to avoid deadlocks)
                await update_both_users_presence(call['user_id'], call['listener_id'], False)
                
                # Remove from Redis
                await redis_client.delete(f"call:{call['call_id']}")
                
                logger.info(f"✅ Expired call {call['call_id']} cleaned up successfully - User paid: {final_coins_spent} coins, Listener earned: ₹{listener_earnings}")
                
            except Exception as e:
                logger.error(f"❌ Error cleaning up call {call['call_id']}: {e}")
                # Continue with other calls even if one fails
                continue

def calculate_call_cost(call_type: CallType, duration_minutes: int) -> int:
    """Calculate call cost based on type and duration"""
    rate_config = DEFAULT_CALL_RATES[call_type]
    cost = max(rate_config.minimum_charge, duration_minutes * rate_config.rate_per_minute)
    return cost

async def get_user_coin_balance(user_id: int) -> int:
    """Get user's current coin balance"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        balance = await conn.fetchval(
            "SELECT balance_coins FROM user_wallets WHERE user_id = $1",
            user_id
        )
        return balance or 0

async def update_user_coin_balance(user_id: int, amount: int, operation: str = "subtract", tx_type: str = "spend"):
    """Update user's coin balance in wallet and create transaction record"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
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

async def update_both_users_presence(user_id: int, listener_id: int, is_busy: bool, busy_until: datetime = None):
    """Update presence status for both caller and listener simultaneously"""
    logger.info(f"🔄 Updating presence for both users: {user_id} and {listener_id}, busy={is_busy}")
    
    # Update both users' status in parallel
    await asyncio.gather(
        set_user_busy_status(user_id, is_busy, busy_until),
        set_user_busy_status(listener_id, is_busy, busy_until)
    )
    
    logger.info(f"✅ Both users' presence status updated successfully")

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
        from api.utils.realtime import get_user_status_for_broadcast, broadcast_user_status_update
        status_data = await get_user_status_for_broadcast(user_id)
        if status_data:
            # Broadcast to all connected clients
            await broadcast_user_status_update(user_id, status_data)
