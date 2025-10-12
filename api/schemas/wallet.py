from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserBalanceResponse(BaseModel):
    user_id: int
    balance_coins: int
    total_earned: int
    total_spent: int

class AddCoinRequest(BaseModel):
    coins: int = Field(..., gt=0, description="Number of coins to add (must be positive)")
    tx_type: str = Field(default="purchase", description="Transaction type (purchase, bonus, referral_bonus)")
    money_amount: Optional[float] = Field(default=0.0, ge=0, description="Optional money amount associated with the transaction")

class AddCoinResponse(BaseModel):
    transaction_id: int
    coins_added: int
    money_amount: float
    new_balance: int
    message: str
    created_at: datetime

class RechargeTransaction(BaseModel):
    transaction_id: int
    amount_rupees: int
    coins_added: int
    created_at: datetime

class RechargeHistoryResponse(BaseModel):
    transactions: List[RechargeTransaction]
    total_recharged: int
    total_coins_added: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class ListenerBalanceResponse(BaseModel):
    listener_id: int
    balance_coins: int
    withdrawable_money: float
    total_earned: float
    total_withdrawn: float
    pending_withdrawals: float

class ListenerEarning(BaseModel):
    call_id: int
    user_id: int
    listener_id: int
    call_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    money_earned: float
    coins_earned: int
    status: str

class ListenerEarningsResponse(BaseModel):
    earnings: List[ListenerEarning]
    total_earnings: float
    total_calls: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to withdraw (must be positive)")

class WithdrawalResponse(BaseModel):
    transaction_id: int
    amount: float
    new_balance: float
    message: str
    created_at: datetime

class WithdrawalHistoryItem(BaseModel):
    transaction_id: int
    amount: float
    status: str
    created_at: datetime

class WithdrawalHistoryResponse(BaseModel):
    withdrawals: List[WithdrawalHistoryItem]
    total_withdrawn: float
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class BankDetailsUpdate(BaseModel):
    account_holder_name: str = Field(..., min_length=1, max_length=100)
    account_number: str = Field(..., min_length=8, max_length=20)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    bank_name: str = Field(..., min_length=1, max_length=100)

class BankDetailsResponse(BaseModel):
    account_holder_name: str
    account_number: str
    ifsc_code: str
    bank_name: str
    updated_at: datetime
