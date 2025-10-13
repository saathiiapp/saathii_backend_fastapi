from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Reuse SexEnum from user schemas to avoid duplication
from api.schemas.user import SexEnum


class AddFavoriteRequest(BaseModel):
    listener_id: int = Field(..., description="ID of the listener to add to favorites")


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


