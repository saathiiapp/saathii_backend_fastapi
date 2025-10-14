from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from api.schemas.user import SexEnum


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
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None
    is_available: bool
    # Listener call preferences
    listener_allowed_call_type: Optional[List[str]] = None
    listener_audio_call_enable: Optional[bool] = None
    listener_video_call_enable: Optional[bool] = None


class ListenerFeedResponse(BaseModel):
    items: List[ListenerFeedItem]
    total_count: int
    online_count: int
    available_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool


class FeedFilters(BaseModel):
    online_only: Optional[bool] = False
    available_only: Optional[bool] = False
    language: Optional[str] = None
    interests: Optional[List[str]] = None
    min_rating: Optional[int] = None
    page: Optional[int] = 1
    per_page: Optional[int] = 20
