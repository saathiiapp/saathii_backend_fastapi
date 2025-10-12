from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum


class SexEnum(str, Enum):
    male = "male"
    female = "female"


class UserResponse(BaseModel):
    user_id: int
    phone: str
    username: Optional[str] = None
    sex: Optional[SexEnum] = None
    dob: Optional[date] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
    rating: Optional[int] = None
    country: Optional[str] = None
    roles: Optional[List[str]] = None


class EditUserRequest(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    rating: Optional[int] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None


# Status-related schemas
class UserStatusResponse(BaseModel):
    user_id: int
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None


class UpdateStatusRequest(BaseModel):
    is_online: Optional[bool] = None
    is_busy: Optional[bool] = None
    wait_time: Optional[int] = None


class HeartbeatRequest(BaseModel):
    # Empty body - just a ping to update last_seen
    pass


class UserPresenceResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None


# Feed-related schemas
class ListenerFeedItem(BaseModel):
    user_id: int
    username: Optional[str] = None
    sex: Optional[SexEnum] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
    rating: Optional[int] = None
    country: Optional[str] = None
    roles: Optional[List[str]] = None
    # Status information
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None
    # Additional feed-specific fields
    is_available: bool  # True if online and not busy


class FeedResponse(BaseModel):
    listeners: List[ListenerFeedItem]
    total_count: int
    online_count: int
    available_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool


class FeedFilters(BaseModel):
    online_only: Optional[bool] = False
    available_only: Optional[bool] = False  # Online and not busy
    language: Optional[str] = None
    interests: Optional[List[str]] = None
    min_rating: Optional[int] = None
    page: Optional[int] = 1
    per_page: Optional[int] = 20

# Favorite-related schemas
class AddFavoriteRequest(BaseModel):
    listener_id: int = Field(..., description="ID of the listener to add to favorites")

class RemoveFavoriteRequest(BaseModel):
    listener_id: int = Field(..., description="ID of the listener to remove from favorites")

class FavoriteUser(BaseModel):
    user_id: int
    username: Optional[str] = None
    sex: Optional[SexEnum] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
    rating: Optional[int] = None
    country: Optional[str] = None
    # Status information
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None
    # Favorite-specific fields
    is_available: bool  # True if online and not busy
    favorited_at: datetime

class FavoritesResponse(BaseModel):
    favorites: List[FavoriteUser]
    total_count: int
    online_count: int
    available_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class FavoriteActionResponse(BaseModel):
    success: bool
    message: str
    listener_id: int
    is_favorited: bool

# Simplified Wallet schemas
class UserBalanceResponse(BaseModel):
    user_id: int
    balance_coins: int

class AddCoinRequest(BaseModel):
    coins: int = Field(..., gt=0, description="Number of coins to add")
    tx_type: str = Field(default="purchase", description="Transaction type")
    money_amount: float = Field(default=0.0, description="Money amount associated")

class AddCoinResponse(BaseModel):
    transaction_id: int
    coins_added: int
    new_balance: int
    message: str
    created_at: datetime

class RechargeTransaction(BaseModel):
    transaction_id: int
    coins_added: int
    money_amount: float
    tx_type: str
    created_at: datetime

class RechargeHistoryResponse(BaseModel):
    transactions: List[RechargeTransaction]
    total_coins_added: int
    total_money_spent: float
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class ListenerBalanceResponse(BaseModel):
    user_id: int
    withdrawable_money: float
    total_earned: float

class ListenerEarning(BaseModel):
    call_id: int
    user_id: int
    listener_id: int
    call_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    money_earned: float
    created_at: datetime

class ListenerEarningsResponse(BaseModel):
    earnings: List[ListenerEarning]
    total_earned: float
    total_calls: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

# Legacy wallet schemas (to be removed)
class WalletBalanceResponse(BaseModel):
    user_id: int
    balance_coins: int
    withdrawable_money: float
    total_earned: float
    total_withdrawn: float
    pending_withdrawals: float

class CallEarning(BaseModel):
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

class CallEarningsResponse(BaseModel):
    earnings: List[CallEarning]
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
    message: str
    created_at: datetime

class WithdrawalHistoryItem(BaseModel):
    transaction_id: int
    amount: float
    created_at: datetime
    status: str = "pending"  # withdraw transactions are always pending until processed

class WithdrawalHistoryResponse(BaseModel):
    withdrawals: List[WithdrawalHistoryItem]
    total_withdrawn: float
    pending_amount: float
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

class BankDetailsUpdate(BaseModel):
    payout_account: dict = Field(..., description="Bank account details for withdrawal (JSON)")

class BankDetailsResponse(BaseModel):
    has_bank_details: bool
    message: str

# Blocking related schemas
class BlockUserRequest(BaseModel):
    blocked_id: int = Field(..., description="ID of the user to block")
    action_type: str = Field("block", description="Type of action (block or report)")
    reason: Optional[str] = Field(None, description="Optional reason for blocking")

class UnblockUserRequest(BaseModel):
    blocked_id: int = Field(..., description="ID of the user to unblock")

class BlockActionResponse(BaseModel):
    success: bool
    message: str
    blocked_id: int
    action_type: str
    is_blocked: bool

class BlockedUser(BaseModel):
    user_id: int
    username: Optional[str] = None
    sex: Optional[SexEnum] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    action_type: str
    reason: Optional[str] = None
    blocked_at: datetime

class BlockedUsersResponse(BaseModel):
    blocked_users: List[BlockedUser]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

# Listener Verification related schemas
class ListenerVerificationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class UploadAudioRequest(BaseModel):
    audio_file_url: str = Field(..., description="S3 URL for the audio file")

class UploadAudioFileRequest(BaseModel):
    # This will be used for direct file upload
    pass

class ListenerVerificationResponse(BaseModel):
    sample_id: int
    listener_id: int
    audio_file_url: str
    status: ListenerVerificationStatus
    remarks: Optional[str] = None
    uploaded_at: datetime
    reviewed_at: Optional[datetime] = None

class VerificationStatusResponse(BaseModel):
    is_verified: bool
    verification_status: Optional[ListenerVerificationStatus] = None
    last_verification: Optional[ListenerVerificationResponse] = None
    message: str

class AdminReviewRequest(BaseModel):
    sample_id: int
    status: ListenerVerificationStatus
    remarks: Optional[str] = None

class AdminReviewResponse(BaseModel):
    success: bool
    message: str
    verification: ListenerVerificationResponse

# Add coins to wallet schemas
class AddCoinsRequest(BaseModel):
    coins: int = Field(..., gt=0, description="Number of coins to add (must be positive)")
    tx_type: str = Field(default="purchase", description="Transaction type (purchase, bonus, referral_bonus)")
    money_amount: Optional[float] = Field(default=0.0, ge=0, description="Optional money amount associated with the transaction")

class AddCoinsResponse(BaseModel):
    transaction_id: int
    coins_added: int
    money_amount: float
    new_balance: int
    message: str
    created_at: datetime
