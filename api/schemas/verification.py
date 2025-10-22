from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class VerificationStatusResponse(BaseModel):
    verification_status: bool  # true = verified, false = not verified
    verification_message: Optional[str] = None
    verified_on: Optional[datetime] = None


class UnverifiedListenerResponse(BaseModel):
    user_id: int
    username: str
    sex: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
    country: Optional[str] = None
    verification_status: bool
    verification_message: Optional[str] = None
    audio_file_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminVerificationListResponse(BaseModel):
    unverified_listeners: List[UnverifiedListenerResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool
