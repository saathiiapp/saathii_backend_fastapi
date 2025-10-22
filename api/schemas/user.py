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
    is_active: Optional[bool] = None


class EditUserRequest(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    rating: Optional[int] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None


class DeleteUserRequest(BaseModel):
    reason: Optional[str] = None


class DeleteUserResponse(BaseModel):
    message: str
    request_id: Optional[int] = None


class DeleteRequestRecord(BaseModel):
    request_id: int
    user_id: int
    username: Optional[str] = None
    phone: Optional[str] = None
    reason: Optional[str] = None
    user_role: str
    deleted_at: datetime
    created_at: datetime


# Admin User Management Schemas (Customers & Listeners)
class AdminUserResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    phone: str
    sex: Optional[SexEnum] = None
    dob: Optional[date] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
    rating: Optional[int] = None
    country: Optional[str] = None
    roles: List[str]  # List of user roles (customer, listener, or both)
    is_active: bool
    is_online: Optional[bool] = None
    last_seen: Optional[datetime] = None
    is_verified: Optional[bool] = None  # For listeners
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool


class AdminUserStatusUpdateRequest(BaseModel):
    user_id: int
    is_active: bool


class AdminUserStatusUpdateResponse(BaseModel):
    success: bool
    message: str
    user_id: int
    is_active: bool
    user_type: str  # "customer", "listener", or "both"