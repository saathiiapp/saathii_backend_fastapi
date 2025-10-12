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

class StartCallResponse(BaseModel):
    call_id: int
    message: str
    call_duration: int = Field(..., description="Maximum call duration in minutes based on available coins")
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
    coins_spent: int
    listener_money_earned: int
    status: CallStatus
    updated_at: datetime
    created_at: datetime

class CallHistoryResponse(BaseModel):
    calls: list[CallInfo]
    total_calls: int
    total_coins_spent: int
    total_earnings: int = Field(..., description="Total earnings as listener")
    page: int
    per_page: int
    has_next: bool
    has_previous: bool

# Default call rates (can be configured)
DEFAULT_CALL_RATES = {
    CallType.AUDIO: {
        "rate_per_minute": 10,
        "minimum_charge": 10  # 1 minute minimum
    },
    CallType.VIDEO: {
        "rate_per_minute": 60,
        "minimum_charge": 60  # 1 minute minimum
    }
}
