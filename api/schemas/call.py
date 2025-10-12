from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class CallType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"

class CallStatus(str, Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    DROPPED = "dropped"

class StartCallRequest(BaseModel):
    listener_id: int = Field(..., description="ID of the listener to call")
    call_type: CallType = Field(..., description="Type of call (audio or video)")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated call duration in minutes")

class StartCallResponse(BaseModel):
    call_id: int
    message: str
    estimated_cost: int = Field(..., description="Estimated cost in coins")
    remaining_coins: int = Field(..., description="Remaining coins after call starts")
    call_type: CallType
    listener_id: int
    status: CallStatus

class EndCallRequest(BaseModel):
    call_id: int
    reason: Optional[str] = Field(None, description="Reason for ending call (e.g., 'completed', 'dropped', 'coin_empty')")

class EndCallResponse(BaseModel):
    call_id: int
    message: str
    duration_seconds: int
    duration_minutes: int
    coins_spent: int
    user_money_spend: int
    listener_money_earned: int
    status: CallStatus

class CallInfo(BaseModel):
    call_id: int
    user_id: int
    listener_id: int
    call_type: CallType
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    duration_minutes: Optional[int]
    user_money_spend: int
    coins_spent: int
    listener_money_earned: int
    status: CallStatus
    updated_at: datetime
    created_at: datetime

class CallHistoryResponse(BaseModel):
    calls: list[CallInfo]
    total_calls: int
    total_coins_spent: int
    total_money_spent: int
    total_earnings: int = Field(..., description="Total earnings as listener")
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class CoinBalanceResponse(BaseModel):
    user_id: int
    current_balance: int
    total_earned: int
    total_spent: int

class CallRateConfig(BaseModel):
    call_type: CallType
    rate_per_minute: int = Field(..., description="Rate in coins per minute")
    minimum_charge: int = Field(..., description="Minimum charge in coins")

# Default call rates (can be configured)
DEFAULT_CALL_RATES = {
    CallType.AUDIO: CallRateConfig(
        call_type=CallType.AUDIO,
        rate_per_minute=10,
        minimum_charge=10  # 1 minute minimum
    ),
    CallType.VIDEO: CallRateConfig(
        call_type=CallType.VIDEO,
        rate_per_minute=60,
        minimum_charge=60  # 1 minute minimum
    )
}

# Listener earnings in rupees per minute
LISTENER_EARNINGS = {
    CallType.AUDIO: 1,  # 1 rupee per minute
    CallType.VIDEO: 6   # 6 rupees per minute
}

# Recharge rates (rupees to coins conversion)
RECHARGE_RATES = {
    "150": 300,  # 150 rupees = 300 coins
    "300": 600,  # 300 rupees = 600 coins
    "500": 1000, # 500 rupees = 1000 coins
    "1000": 2000 # 1000 rupees = 2000 coins
}

class RechargeRequest(BaseModel):
    amount_rupees: int = Field(..., description="Amount in rupees to recharge")
    payment_method: str = Field(..., description="Payment method (upi, card, wallet)")

class RechargeResponse(BaseModel):
    transaction_id: str
    amount_rupees: int
    coins_added: int
    new_balance: int
    message: str

class RechargeHistoryResponse(BaseModel):
    transactions: list[dict]
    total_recharged: int
    total_coins_added: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class TransactionType(str, Enum):
    PURCHASE = "purchase"
    SPEND = "spend"
    EARN = "earn"
    WITHDRAW = "withdraw"
    BONUS = "bonus"
    REFERRAL_BONUS = "referral_bonus"

class TransactionInfo(BaseModel):
    transaction_id: int
    tx_type: TransactionType
    coins_change: int
    money_change: float
    description: str
    call_id: Optional[int] = None
    created_at: datetime

class UserTransactionHistoryResponse(BaseModel):
    transactions: list[TransactionInfo]
    total_coins_spent: int
    total_money_spent: float
    total_coins_earned: int
    total_money_earned: float
    current_balance: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class ListenerTransactionHistoryResponse(BaseModel):
    transactions: list[TransactionInfo]
    total_coins_earned: int
    total_money_earned: float
    total_calls_completed: int
    current_withdrawable_balance: float
    page: int
    per_page: int
    has_next: bool
    has_previous: bool
