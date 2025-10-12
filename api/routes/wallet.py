from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional
from datetime import datetime
from api.clients.redis_client import redis_client
from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.schemas.wallet import (
    UserBalanceResponse,
    AddCoinRequest,
    AddCoinResponse,
    RechargeTransaction,
    RechargeHistoryResponse,
    ListenerBalanceResponse,
    ListenerEarning,
    ListenerEarningsResponse,
    WithdrawalRequest,
    WithdrawalResponse,
    WithdrawalHistoryItem,
    WithdrawalHistoryResponse,
    BankDetailsUpdate,
    BankDetailsResponse
)

router = APIRouter(tags=["Wallet Management"])

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
    return payload

async def check_listener_role(user_id: int):
    """Check if user has listener role"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        listener_role = await conn.fetchrow(
            """
            SELECT role FROM user_roles 
            WHERE user_id = $1 AND role = 'listener' AND active = true
            """,
            user_id
        )
        if not listener_role:
            raise HTTPException(
                status_code=403, 
                detail="Only users with listener role can access this endpoint"
            )

# USER WALLET APIs

@router.get("/balance", response_model=UserBalanceResponse)
async def get_user_balance(user=Depends(get_current_user_async)):
    """Get user's coin balance"""
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get or create wallet
        wallet = await conn.fetchrow(
            """
            SELECT balance_coins FROM user_wallets 
            WHERE user_id = $1
            """,
            user_id
        )
        
        if not wallet:
            # Create wallet if it doesn't exist
            await conn.execute(
                """
                INSERT INTO user_wallets (user_id, balance_coins, created_at, updated_at)
                VALUES ($1, 0, now(), now())
                """,
                user_id
            )
            balance_coins = 0
        else:
            balance_coins = wallet['balance_coins']
        
        return UserBalanceResponse(
            user_id=user_id,
            balance_coins=balance_coins
        )

@router.post("/add_coin", response_model=AddCoinResponse)
async def add_coin_to_wallet(
    data: AddCoinRequest,
    user=Depends(get_current_user_async)
):
    """Add coins to user's wallet"""
    user_id = user["user_id"]
    coins_to_add = data.coins
    tx_type = data.tx_type
    money_amount = data.money_amount
    
    # Validate transaction type
    valid_tx_types = ["purchase", "bonus", "referral_bonus"]
    if tx_type not in valid_tx_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transaction type. Must be one of: {', '.join(valid_tx_types)}"
        )
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get or create wallet
        wallet = await conn.fetchrow(
            "SELECT wallet_id, balance_coins FROM user_wallets WHERE user_id = $1",
            user_id
        )
        
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = await conn.fetchrow(
                """
                INSERT INTO user_wallets (user_id, balance_coins, created_at, updated_at)
                VALUES ($1, 0, now(), now())
                RETURNING wallet_id, balance_coins
                """,
                user_id
            )
        
        # Update wallet balance
        new_balance = wallet['balance_coins'] + coins_to_add
        await conn.execute(
            "UPDATE user_wallets SET balance_coins = $1, updated_at = now() WHERE wallet_id = $2",
            new_balance, wallet['wallet_id']
        )
        
        # Create transaction record
        transaction = await conn.fetchrow(
            """
            INSERT INTO user_transactions (wallet_id, tx_type, coins_change, money_change, created_at, updated_at)
            VALUES ($1, $2, $3, $4, now(), now())
            RETURNING transaction_id, created_at
            """,
            wallet['wallet_id'], tx_type, coins_to_add, money_amount
        )
        
        return AddCoinResponse(
            transaction_id=transaction['transaction_id'],
            coins_added=coins_to_add,
            new_balance=new_balance,
            message=f"Successfully added {coins_to_add} coins to wallet" + (f" (₹{money_amount:.2f})" if money_amount > 0 else ""),
            created_at=transaction['created_at']
        )

@router.get("/recharge/history", response_model=RechargeHistoryResponse)
async def get_recharge_history(
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """Get user's wallet recharge transaction history (only purchase transactions)"""
    user_id = user["user_id"]
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get only recharge transactions (purchase type only)
        transactions_query = """
            SELECT 
                ut.transaction_id,
                ut.coins_change,
                ut.money_change,
                ut.tx_type,
                ut.created_at
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'purchase'
            ORDER BY ut.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        transactions = await conn.fetch(transactions_query, user_id, per_page, offset)
        
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
        
        # Get total coins added and money spent
        stats = await conn.fetchrow(
            """
            SELECT 
                COALESCE(SUM(ut.coins_change), 0) as total_coins_added,
                COALESCE(SUM(ut.money_change), 0) as total_money_spent
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'purchase'
            """,
            user_id
        )
        
        # Format transactions
        transaction_list = []
        for tx in transactions:
            transaction_list.append(RechargeTransaction(
                transaction_id=tx['transaction_id'],
                coins_added=tx['coins_change'],
                money_amount=float(tx['money_change']),
                tx_type=tx['tx_type'],
                created_at=tx['created_at']
            ))
        
        has_next = offset + per_page < total_count
        has_previous = page > 1
        
        return RechargeHistoryResponse(
            transactions=transaction_list,
            total_coins_added=stats['total_coins_added'] or 0,
            total_money_spent=float(stats['total_money_spent'] or 0),
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )

# LISTENER WALLET APIs (Listener role required)

@router.get("/listener/balance", response_model=ListenerBalanceResponse)
async def get_listener_balance(user=Depends(get_current_user_async)):
    """Get listener's withdrawable money and total earnings"""
    user_id = user["user_id"]
    
    # Check listener role
    await check_listener_role(user_id)
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get wallet information
        wallet = await conn.fetchrow(
            """
            SELECT withdrawable_money FROM user_wallets 
            WHERE user_id = $1
            """,
            user_id
        )
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Get total earned from completed calls
        total_earned = await conn.fetchval(
            """
            SELECT COALESCE(SUM(listener_money_earned), 0)
            FROM user_calls 
            WHERE listener_id = $1 AND status = 'completed'
            """,
            user_id
        )
        
        return ListenerBalanceResponse(
            user_id=user_id,
            withdrawable_money=float(wallet['withdrawable_money']),
            total_earned=float(total_earned or 0)
        )

@router.get("/listener/earnings", response_model=ListenerEarningsResponse)
async def get_listener_earnings(
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """Get listener's earnings from completed calls"""
    user_id = user["user_id"]
    
    # Check listener role
    await check_listener_role(user_id)
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get call earnings with pagination
        earnings_query = """
            SELECT 
                uc.call_id,
                uc.user_id,
                uc.listener_id,
                uc.call_type,
                uc.start_time,
                uc.end_time,
                uc.duration_minutes,
                uc.listener_money_earned,
                uc.created_at
            FROM user_calls uc
            WHERE uc.listener_id = $1 AND uc.status = 'completed'
            ORDER BY uc.start_time DESC
            LIMIT $2 OFFSET $3
        """
        
        earnings = await conn.fetch(earnings_query, user_id, per_page, offset)
        
        # Get total count
        total_calls = await conn.fetchval(
            "SELECT COUNT(*) FROM user_calls WHERE listener_id = $1 AND status = 'completed'",
            user_id
        )
        
        # Get total earnings
        total_earnings = await conn.fetchval(
            "SELECT COALESCE(SUM(listener_money_earned), 0) FROM user_calls WHERE listener_id = $1 AND status = 'completed'",
            user_id
        )
        
        # Format earnings
        earnings_list = []
        for earning in earnings:
            earnings_list.append(ListenerEarning(
                call_id=earning['call_id'],
                user_id=earning['user_id'],
                listener_id=earning['listener_id'],
                call_type=earning['call_type'],
                start_time=earning['start_time'],
                end_time=earning['end_time'],
                duration_minutes=earning['duration_minutes'],
                money_earned=float(earning['listener_money_earned']),
                created_at=earning['created_at']
            ))
        
        has_next = offset + per_page < total_calls
        has_previous = page > 1
        
        return ListenerEarningsResponse(
            earnings=earnings_list,
            total_earned=float(total_earnings or 0),
            total_calls=total_calls,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )

@router.post("/listener/withdraw", response_model=WithdrawalResponse)
async def request_withdrawal(
    data: WithdrawalRequest,
    user=Depends(get_current_user_async)
):
    """Request withdrawal from wallet (Listener only)"""
    user_id = user["user_id"]
    amount = data.amount
    
    # Check listener role
    await check_listener_role(user_id)
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get wallet information
        wallet = await conn.fetchrow(
            "SELECT wallet_id, withdrawable_money FROM user_wallets WHERE user_id = $1",
            user_id
        )
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Check if user has sufficient balance
        if amount > wallet['withdrawable_money']:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient balance. Available: ₹{wallet['withdrawable_money']:.2f}, Requested: ₹{amount:.2f}"
            )
        
        # Check if user has bank details
        bank_details = await conn.fetchrow(
            "SELECT payout_account FROM listener_payout WHERE user_id = $1",
            user_id
        )
        
        if not bank_details or not bank_details['payout_account']:
            raise HTTPException(
                status_code=400,
                detail="Bank details not found. Please add your bank details before requesting withdrawal."
            )
        
        # Create withdrawal transaction
        transaction = await conn.fetchrow(
            """
            INSERT INTO user_transactions (wallet_id, tx_type, money_change, created_at)
            VALUES ($1, 'withdraw', -$2, now())
            RETURNING transaction_id, created_at
            """,
            wallet['wallet_id'], amount
        )
        
        return WithdrawalResponse(
            transaction_id=transaction['transaction_id'],
            amount=amount,
            message=f"Withdrawal request of ₹{amount:.2f} submitted successfully",
            created_at=transaction['created_at']
        )

@router.get("/listener/withdrawals", response_model=WithdrawalHistoryResponse)
async def get_withdrawal_history(
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """Get withdrawal history (Listener only)"""
    user_id = user["user_id"]
    
    # Check listener role
    await check_listener_role(user_id)
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get withdrawal transactions
        withdrawals_query = """
            SELECT 
                ut.transaction_id,
                ABS(ut.money_change) as amount,
                ut.created_at
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'withdraw'
            ORDER BY ut.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        withdrawals = await conn.fetch(withdrawals_query, user_id, per_page, offset)
        
        # Get total count
        total_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'withdraw'
            """,
            user_id
        )
        
        # Get total withdrawn and pending amounts
        stats = await conn.fetchrow(
            """
            SELECT 
                COALESCE(SUM(ABS(ut.money_change)), 0) as total_withdrawn,
                COALESCE(SUM(ABS(ut.money_change)), 0) as pending_amount
            FROM user_transactions ut
            JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
            WHERE uw.user_id = $1 AND ut.tx_type = 'withdraw'
            """,
            user_id
        )
        
        # Format withdrawals
        withdrawal_list = []
        for withdrawal in withdrawals:
            withdrawal_list.append(WithdrawalHistoryItem(
                transaction_id=withdrawal['transaction_id'],
                amount=float(withdrawal['amount']),
                created_at=withdrawal['created_at'],
                status="pending"  # All withdrawal transactions are pending until processed by admin
            ))
        
        has_next = offset + per_page < total_count
        has_previous = page > 1
        
        return WithdrawalHistoryResponse(
            withdrawals=withdrawal_list,
            total_withdrawn=float(stats['total_withdrawn'] or 0),
            pending_amount=float(stats['pending_amount'] or 0),
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )

@router.put("/listener/bank-details", response_model=BankDetailsResponse)
async def update_bank_details(
    data: BankDetailsUpdate,
    user=Depends(get_current_user_async)
):
    """Update listener's bank details for withdrawals (Listener only)"""
    user_id = user["user_id"]
    
    # Check listener role
    await check_listener_role(user_id)
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if listener payout record exists
        existing = await conn.fetchrow(
            "SELECT user_id FROM listener_payout WHERE user_id = $1",
            user_id
        )
        
        if existing:
            # Update existing record
            await conn.execute(
                "UPDATE listener_payout SET payout_account = $1, updated_at = now() WHERE user_id = $2",
                data.payout_account, user_id
            )
        else:
            # Create new record
            await conn.execute(
                "INSERT INTO listener_payout (user_id, payout_account, created_at, updated_at) VALUES ($1, $2, now(), now())",
                user_id, data.payout_account
            )
        
        return BankDetailsResponse(
            has_bank_details=True,
            message="Bank details updated successfully"
        )

@router.get("/listener/bank-details", response_model=BankDetailsResponse)
async def get_bank_details_status(user=Depends(get_current_user_async)):
    """Check if listener has bank details configured (Listener only)"""
    user_id = user["user_id"]
    
    # Check listener role
    await check_listener_role(user_id)
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        bank_details = await conn.fetchrow(
            "SELECT payout_account FROM listener_payout WHERE user_id = $1",
            user_id
        )
        
        has_details = bank_details is not None and bank_details['payout_account'] is not None
        
        return BankDetailsResponse(
            has_bank_details=has_details,
            message="Bank details configured" if has_details else "Bank details not configured"
        )