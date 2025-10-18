from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BlockUserRequest(BaseModel):
    blocked_id: int = Field(..., description="ID of the user to block")
    reason: Optional[str] = Field(None, description="Optional reason for blocking")


class UnblockUserRequest(BaseModel):
    blocked_id: int = Field(..., description="ID of the user to unblock")


class BlockActionResponse(BaseModel):
    success: bool
    message: str
    blocked_id: int
    is_blocked: bool


class BlockedUser(BaseModel):
    user_id: int
    username: Optional[str] = None
    sex: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    reason: Optional[str] = None
    blocked_at: datetime


class BlockedUsersResponse(BaseModel):
    blocked_users: List[BlockedUser]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool


