from pydantic import BaseModel
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
    busy_until: Optional[datetime] = None


class UpdateStatusRequest(BaseModel):
    is_online: Optional[bool] = None
    is_busy: Optional[bool] = None
    busy_until: Optional[datetime] = None


class HeartbeatRequest(BaseModel):
    # Empty body - just a ping to update last_seen
    pass


class UserPresenceResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    is_online: bool
    last_seen: datetime
    is_busy: bool
    busy_until: Optional[datetime] = None
